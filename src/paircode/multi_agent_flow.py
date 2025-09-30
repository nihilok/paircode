from typing import Annotated, Sequence
from typing_extensions import TypedDict
import operator
import functools
import uuid

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel
from typing import Literal

from paircode.tools import FileSystemTools


# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str


# --- Members ---
members = ["Researcher", "Coder"]
options_for_next = ["FINISH"] + members


# --- Route Response Model ---
class RouteResponse(BaseModel):
    next: Literal[tuple(options_for_next)]


# --- Supervisor Prompt ---
system_prompt = (
    "You are a supervisor tasked with managing a conversation between the "
    "following workers:  {members}. Given the following user request, "
    "respond with the worker to act next. Each worker will perform a "
    "task and respond with their results and status. When finished, "
    "respond with FINISH.\n"
    "Given the conversation above, who should act next? Or should we FINISH? "
    "Select one of: {options}"
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
prompt = prompt.partial(options=str(options_for_next), members=", ".join(members))

llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)


def supervisor_agent(state):
    supervisor_chain = prompt | llm.with_structured_output(RouteResponse)
    return supervisor_chain.invoke(state)


# --- Tools ---
from langchain_experimental.tools import PythonREPLTool

python_repl_tool = PythonREPLTool()


# --- Agent Node Utility ---
def agent_node(state, agent, name, context=None):
    agent_response = agent.invoke(state, context=context)
    return {
        "messages": [
            HumanMessage(content=agent_response["messages"][-1].content, name=name)
        ]
    }


# --- Researcher Node ---
research_agent = create_react_agent(
    llm, tools=[FileSystemTools.read_file, FileSystemTools.list_files]
)  # No tools
research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

# --- Coder Node ---
coder_agent = create_react_agent(llm, tools=[python_repl_tool])
coder_node = functools.partial(agent_node, agent=coder_agent, name="Coder")

# --- Graph Construction ---
workflow = StateGraph(AgentState)
workflow.add_node("Researcher", research_node)
workflow.add_node("Coder", coder_node)
workflow.add_node("Supervisor", supervisor_agent)
for member in members:
    workflow.add_edge(member, "Supervisor")
conditional_map = {k: k for k in members}
conditional_map["FINISH"] = END


def get_next(state):
    return state["next"]


workflow.add_conditional_edges("Supervisor", get_next, conditional_map)
workflow.add_edge(START, "Supervisor")
graph = workflow.compile(checkpointer=MemorySaver())


# --- Entry Point for CLI ---
def run_multi_agent_flow(user_message: str):
    config = RunnableConfig(
        recursion_limit=10, configurable={"thread_id": str(uuid.uuid4())}
    )
    inputs = {
        "messages": [HumanMessage(content=user_message)],
    }
    # Stream the graph output
    for event in graph.stream(inputs, config):
        # Print all messages in the state
        state = event.get("messages")
        if state:
            for msg in state:
                name = getattr(msg, "name", None)
                content = getattr(msg, "content", None)
                # Detect tool call in content and explain result
                if content and "Tool call:" in content:
                    # Extract tool name and result if possible
                    lines = content.splitlines()
                    tool_line = next((l for l in lines if "Tool call:" in l), None)
                    result_line = next((l for l in lines if "Result:" in l), None)
                    if tool_line:
                        print(f"[{name}] {tool_line}")
                    if result_line:
                        print(f"[Tool Result] {result_line}")
                        # Plain-language explanation for common tools
                        if "read_file" in tool_line:
                            print(
                                "The file was read successfully. Here’s a summary of its contents above."
                            )
                        elif "list_files" in tool_line:
                            print(
                                "The files in the directory were listed. See the results above."
                            )
                        elif "write_to_file" in tool_line:
                            print("The file was written successfully.")
                        elif "execute_in_shell" in tool_line:
                            print(
                                "The shell command was executed. See the output above."
                            )
                        elif "python_repl" in tool_line:
                            print(
                                "The code was executed in a Python REPL. See the output above."
                            )
                        else:
                            print("A tool was called and its result is shown above.")
                elif name and content:
                    print(f"[{name}] {content}")
                elif content:
                    print(content)
        # Print next agent decision
        next_agent = event.get("next")
        if next_agent:
            print(f"Next: {next_agent}")
