from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm
from langgraph.checkpoint.memory import InMemorySaver
from .file_service import FileService


def run_tests(test_file: str) -> str:
    """Run tests on the code."""
    return "I don't have the ability to execute code. Please run the tests in your local environment."


EXPLAIN_TOOL_RESULTS = (
    "Whenever you reference the result of a tool call, always explain it to the user in plain language, "
    "since the user cannot see the raw tool output. Always continue from where you left off in the workflow. Do not repeat previous steps or explanations."
)


# Factory for swarm-based agents and workflow

def create_paircode_swarm(coder_name: str, tester_name: str, supervisor_name: str = "Supervisor", base_directory: str = "."):
    model = ChatOpenAI(model="gpt-4o")
    file_service = FileService(base_directory)
    # File tools
    def read_file(path: str) -> str:
        """Read and return the content of a file at the specified path."""
        return file_service.read_file(path)
    def write_to_file(path: str, content: str) -> str:
        """Write content to a file at the specified path."""
        return file_service.write_to_file(path, content)
    def list_files(directory: str) -> str:
        """List files in the specified directory."""
        return file_service.list_files(directory)
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
            write_to_file,
            read_file,
            list_files,
            create_handoff_tool(agent_name=supervisor_name, description="Transfer to the supervisor for coordination."),
            create_handoff_tool(agent_name=tester_name, description="Transfer to the tester to write or run tests."),
        ],
        prompt=(
            f"You are {coder_name}, a helpful coder. Use your tools to write code, read/write files, and hand off as needed. "
            "You have access to file tools: read_file, write_to_file, list_files. "
            "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
            f"{EXPLAIN_TOOL_RESULTS}"
        ),
        name=coder_name,
    )
    # Tester agent
    tester = create_react_agent(
        model,
        [
            run_tests,
            write_to_file,
            read_file,
            list_files,
            create_handoff_tool(agent_name=supervisor_name, description="Transfer to the supervisor for coordination."),
            create_handoff_tool(agent_name=coder_name, description="Transfer to the coder to implement code."),
        ],
        prompt=(
            f"You are {tester_name}, a helpful tester. Use your tools to write and run tests, read/write files, and hand off as needed. "
            "You have access to file tools: read_file, write_to_file, list_files. "
            "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
            f"{EXPLAIN_TOOL_RESULTS}"
        ),
        name=tester_name,
    )
    checkpointer = InMemorySaver()
    swarm = create_swarm([supervisor, coder, tester], default_active_agent=supervisor_name)
    app = swarm.compile(checkpointer=checkpointer)

    # Adding a logger to stream outputs
    import logging
    logging.basicConfig(level=logging.INFO)

    app.logging_function = lambda message: logging.info(message)

    return app
