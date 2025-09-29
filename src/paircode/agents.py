from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm
from langgraph.checkpoint.memory import InMemorySaver

def write_to_file(path: str, content: str) -> str:
    """Write content to a file at the specified path."""
    import os
    from pathlib import Path
    import time

    path = os.path.expanduser(path)
    p = Path(path)
    if p.exists():
        backup_path = path + f".paircode.{time.time()}.bak"
        os.rename(path, backup_path)
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote to {path}"

def read_file(path: str) -> str:
    """Read and return the content of a file at the specified path."""
    import os
    path = os.path.expanduser(path)
    with open(path, "r") as f:
        return f.read()


def list_files(directory: str) -> str:
    """List files in the specified directory."""
    import os
    path = os.path.expanduser(directory)
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files in {path}: {e}"


EXPLAIN_TOOL_RESULTS = (
    "Whenever you reference the result of a tool call, always explain it to the user in plain language, "
    "since the user cannot see the raw tool output."
)

# Factory for swarm-based agents and workflow
def create_paircode_swarm(coder_name: str, tester_name: str, supervisor_name: str = "Supervisor"):
    model = ChatOpenAI(model="gpt-4o")
    # Supervisor agent
    supervisor = create_react_agent(
        model,
        [
            create_handoff_tool(agent_name=coder_name, description="Transfer to the coder to implement code."),
            create_handoff_tool(agent_name=tester_name, description="Transfer to the tester to write or run tests."),
        ],
        prompt=(
            f"You are {supervisor_name}, the supervisor. "
            f"You manage a coder ({coder_name}) and a tester ({tester_name}). "
            "Assign work by handing off to the appropriate agent. "
            "Coordinate the workflow: agree on a test plan, have the coder write code, the tester write and run tests, and agree on a definition of done. "
            "Always use handoff tools to transfer control. "
            "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
            f"{EXPLAIN_TOOL_RESULTS}"
        ),
        name=supervisor_name,
    )
    # Coder agent
    coder = create_react_agent(
        model,
        [
            write_to_file, read_file, list_files,
            create_handoff_tool(agent_name=supervisor_name, description="Transfer to the supervisor for coordination."),
            create_handoff_tool(agent_name=tester_name, description="Transfer to the tester to write or run tests."),
        ],
        prompt=(
            f"You are {coder_name}, a helpful coder. Use your tools to write code and hand off as needed. "
            "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
            f"{EXPLAIN_TOOL_RESULTS}"
        ),
        name=coder_name,
    )
    # Tester agent
    tester = create_react_agent(
        model,
        [
            write_to_file, read_file, list_files,
            create_handoff_tool(agent_name=supervisor_name, description="Transfer to the supervisor for coordination."),
            create_handoff_tool(agent_name=coder_name, description="Transfer to the coder to implement code."),
        ],
        prompt=(
            f"You are {tester_name}, a helpful tester. Use your tools to write and run tests and hand off as needed. "
            "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
            f"{EXPLAIN_TOOL_RESULTS}"
        ),
        name=tester_name,
    )
    checkpointer = InMemorySaver()
    swarm = create_swarm([supervisor, coder, tester], default_active_agent=supervisor_name)
    app = swarm.compile(checkpointer=checkpointer)
    return app
