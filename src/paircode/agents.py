from langchain_anthropic import ChatAnthropic
from langchain_core.stores import InMemoryStore
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm
from langgraph.checkpoint.memory import InMemorySaver
from .file_service import FileService
from .shell_service import ShellService
from .tools import HandoffTools, FileSystemTools


def run_tests(test_file: str) -> str:
    """Run tests on the code."""
    return "I don't have the ability to execute code. Please run the tests in your local environment."


EXPLAIN_TOOL_RESULTS = (
    "Whenever you reference the result of a tool call, always explain it to the user in plain language, "
    "since the user cannot see the raw tool output. Always continue from where you left off in the workflow. Do not repeat previous steps or explanations."
)


def end_session() -> str:
    """End the swarm session when the definition of done is met."""
    return "Session ended. The definition of done has been met."


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
        # Agents
        self.supervisor = create_react_agent(
            self.model,
            [
                HandoffTools.hand_off_to_coder(coder_name),
                HandoffTools.hand_off_to_supervisor(supervisor_name),
                HandoffTools.end_session,
                FileSystemTools.read_file,
            ],
            prompt=(
                f"You are {supervisor_name}, the supervisor. "
                f"You manage a coder ({coder_name}) and a tester ({tester_name}). "
                "Assign work by handing off to the appropriate agent. "
                "Coordinate the workflow: agree on a test plan, have the coder write code, the tester write and run tests, and agree on a definition of done. "
                "Always use handoff tools to transfer control. "
                "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
                "When the definition of done is met, call the end_session tool to finish the workflow."
            ),
            name=supervisor_name,
        )
        self.coder = create_react_agent(
            self.model,
            [
                FileSystemTools.write_to_file,
                FileSystemTools.read_file,
                FileSystemTools.list_files,
                HandoffTools.hand_off_to_tester(tester_name),
                HandoffTools.hand_off_to_supervisor(supervisor_name),
            ],
            prompt=(
                f"You are {coder_name}, a helpful coder. Use your tools to write code, read/write files, and hand off as needed. "
                "You have access to file tools: read_file, write_to_file, list_files. "
                f"You are not able to run tests or execute shell commands, so hand off to {tester_name} the tester when "
                "tests need to be run. You must check in with the supervisor for coordination. "
                "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
            ),
            name=coder_name,
        )
        self.tester = create_react_agent(
            self.model,
            [
                FileSystemTools.execute_in_shell,
                FileSystemTools.write_to_file,
                FileSystemTools.read_file,
                FileSystemTools.list_files,
                HandoffTools.hand_off_to_supervisor(supervisor_name),
                HandoffTools.hand_off_to_coder(coder_name),
            ],
            prompt=(
                f"You are {tester_name}, a helpful tester and mentor to {coder_name} (the coder). Use your tools to write "
                "and run tests, read/write files, and hand off as needed. "
                "You have access to file tools: read_file, write_to_file, list_files. You can also execute shell commands "
                "using execute_in_shell. The coder does not have this ability, so you can help by running tests and reporting results. "
                "You oversee the quality of the code and ensure it meets the definition of done. Check in with the supervisor for coordination. "
                "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
            ),
            name=tester_name,
        )
        self.checkpointer = InMemorySaver()
        self.swarm = create_swarm(
            [self.supervisor, self.coder, self.tester],
            default_active_agent=supervisor_name,
        )
        self.app = self.swarm.compile(
            checkpointer=self.checkpointer, store=InMemoryStore()
        )

        # Logging
        import logging

        logging.basicConfig(level=logging.INFO)

        def user_update(message: str):
            logging.debug(f"[DEBUG]: {message}")

        self.app.logging_function = user_update

    def stream(self, input, config=None):
        """
        Stream agent steps for a single input.
        Yields each event (agent action, state update, message) in the workflow.
        """
        yield from self.app.stream(input=input, config=config)
