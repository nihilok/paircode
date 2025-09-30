from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm
from langgraph.checkpoint.memory import InMemorySaver
from .file_service import FileService
from .shell_service import ShellService


def run_tests(test_file: str) -> str:
    """Run tests on the code."""
    return "I don't have the ability to execute code. Please run the tests in your local environment."


EXPLAIN_TOOL_RESULTS = (
    "Whenever you reference the result of a tool call, always explain it to the user in plain language, "
    "since the user cannot see the raw tool output. Always continue from where you left off in the workflow. Do not repeat previous steps or explanations."
)


# Factory for swarm-based agents and workflow
class PaircodeSwarmService:
    def __init__(
        self,
        coder_name: str,
        tester_name: str,
        supervisor_name: str = "Supervisor",
        base_directory: str = ".",
    ):
        self.model = ChatAnthropic(model="claude-sonnet-4-5")
        self.file_service = FileService(base_directory)
        self.shell_service = ShellService()

        # File tools
        def read_file(path: str) -> str:
            """Read text content from a file."""
            return self.file_service.read_file(path)

        def write_to_file(path: str, content: str) -> str:
            """Write text content to a file."""
            return self.file_service.write_to_file(path, content)

        def list_files(directory: str) -> str:
            """List files in a directory."""
            return self.file_service.list_files(directory)

        def execute_in_shell(command: str) -> str:
            """Execute a shell command and return the output."""
            return self.shell_service.execute_in_shell(command)

        # Agents
        self.supervisor = create_react_agent(
            self.model,
            [
                create_handoff_tool(
                    agent_name=coder_name,
                    description="Transfer to the coder to implement code.",
                ),
                create_handoff_tool(
                    agent_name=tester_name,
                    description="Transfer to the tester to write or run tests.",
                ),
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
        self.coder = create_react_agent(
            self.model,
            [
                write_to_file,
                read_file,
                list_files,
                create_handoff_tool(
                    agent_name=supervisor_name,
                    description="Transfer to the supervisor for coordination.",
                ),
                create_handoff_tool(
                    agent_name=tester_name,
                    description="Transfer to the tester to write or run tests.",
                ),
            ],
            prompt=(
                f"You are {coder_name}, a helpful coder. Use your tools to write code, read/write files, and hand off as needed. "
                "You have access to file tools: read_file, write_to_file, list_files. "
                "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
                f"{EXPLAIN_TOOL_RESULTS}"
            ),
            name=coder_name,
        )
        self.tester = create_react_agent(
            self.model,
            [
                execute_in_shell,
                write_to_file,
                read_file,
                list_files,
                create_handoff_tool(
                    agent_name=supervisor_name,
                    description="Transfer to the supervisor for coordination.",
                ),
                create_handoff_tool(
                    agent_name=coder_name,
                    description="Transfer to the coder to implement code.",
                ),
            ],
            prompt=(
                f"You are {tester_name}, a helpful tester. Use your tools to write and run tests, read/write files, and hand off as needed. "
                "You have access to file tools: read_file, write_to_file, list_files. "
                "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
                f"{EXPLAIN_TOOL_RESULTS}"
            ),
            name=tester_name,
        )
        self.checkpointer = InMemorySaver()
        self.swarm = create_swarm(
            [self.supervisor, self.coder, self.tester],
            default_active_agent=supervisor_name,
        )
        self.app = self.swarm.compile(checkpointer=self.checkpointer)
        # Logging
        import logging

        logging.basicConfig(level=logging.INFO)

        def user_update(message: str):
            logging.info(f"User Update: {message}")

        self.app.logging_function = user_update

    def stream(self, input, config=None):
        """
        Stream agent steps for a single input.
        Yields each event (agent action, state update, message) in the workflow.
        """
        if hasattr(self.app, "_swarm") and hasattr(self.app._swarm, "stream"):
            yield from self.app._swarm.stream(input=input, config=config)
        else:
            yield self.app.invoke(input=input, config=config)

    @classmethod
    def factory(
        cls,
        coder_name: str,
        tester_name: str,
        supervisor_name: str = "Supervisor",
        base_directory: str = ".",
        input=None,
        config=None,
    ):
        """
        Entrypoint for running the swarm service from CLI or script.
        """
        service = cls(coder_name, tester_name, supervisor_name, base_directory)
        for event in service.stream(input, config):
            print(event)
