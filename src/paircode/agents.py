from langchain_anthropic import ChatAnthropic
from langchain_core.stores import InMemoryStore
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm
from langgraph.checkpoint.memory import InMemorySaver
from .file_service import FileService
from .shell_service import ShellService
from .tools import HandoffTools, FileSystemTools
from langchain_core.runnables import RunnableConfig
from typing import Generator, Dict, Any, Optional, List, Tuple


def run_tests(test_file: str) -> str:
    """Run tests on the code."""
    return "I don't have the ability to execute code. Please run the tests in your local environment."


EXPLAIN_TOOL_RESULTS = (
    "Try not to use more than 3 nodes in a row without checking in with another agent. "
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
        # Agents
        self.supervisor = create_react_agent(
            self.model,
            [
                HandoffTools.hand_off_to_coder(coder_name),
                HandoffTools.hand_off_to_tester(tester_name),
                HandoffTools.end_session,
                FileSystemTools.read_file,
            ],
            prompt=(
                f"You are {supervisor_name}, the supervisor. "
                f"You manage a coder ({coder_name}) and a tester ({tester_name}). "
                "Assign work by handing off to the appropriate agent. "
                "Coordinate the workflow: agree on a test plan, have the coder write code, the tester write and run tests, and agree on a definition of done. "
                "Always use handoff tools to transfer control. Try not to use more than 3 nodes in a row without checking in with another agent. "
                "Only call one handoff tool per turn. Never call multiple handoff tools in a single turn. "
                f"{EXPLAIN_TOOL_RESULTS}"
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
                f"{EXPLAIN_TOOL_RESULTS}"
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
                f"{EXPLAIN_TOOL_RESULTS}"
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


class PaircodeSession:
    """Unified session and swarm service for PairCode."""

    def __init__(
        self,
        coder_name: str,
        tester_name: str,
        supervisor_name: str = "Supervisor",
        base_directory: str = ".",
    ):
        self.coder_name = coder_name
        self.tester_name = tester_name
        self.supervisor_name = supervisor_name
        self.swarm_service = PaircodeSwarmService(
            coder_name, tester_name, supervisor_name, base_directory
        )
        self.config = RunnableConfig(
            recursion_limit=10,
            configurable={"thread_id": "1"},
            tags=["my-tag"],
        )

    def send_message(self, message: str) -> Generator[Dict[str, Any], None, None]:
        """Send a message to the swarm and stream responses."""
        message_payload = {"messages": [{"role": "user", "content": message}]}
        yield from self.swarm_service.stream(message_payload, self.config)

    @staticmethod
    def extract_event_info(
        event: Dict[str, Any],
    ) -> List[Tuple[Optional[str], Optional[str], Optional[str]]]:
        """Extract all agent messages, tool explanations, and handoff/status updates from a swarm event.
        Returns a list of (agent_name, message_content, tool_explanation) tuples for every message in the event.
        Always returns at least one tuple per event.
        """
        results = []
        if not isinstance(event, dict):
            return [(None, str(event), None)]

        agent = event.get("active_agent") or event.get("agent") or event.get("name")
        messages = event.get("messages")
        # Handle agent handoff (ToolMessage with transfer)
        if event.get("name", "").startswith("transfer_to_"):
            target = event.get("name", "").replace("transfer_to_", "")
            results.append(
                (
                    agent or target,
                    None,
                    f"[yellow]Control transferred to {target}[/yellow]",
                )
            )

        # Extract all messages
        if messages:
            for msg in messages:
                message_content = None
                tool_explanation = None
                if isinstance(msg, dict):
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        text_chunks = []
                        for chunk in content:
                            if isinstance(chunk, dict):
                                if "text" in chunk:
                                    text_chunks.append(chunk["text"])
                                elif "content" in chunk:
                                    text_chunks.append(chunk["content"])
                        message_content = (
                            "\n".join(text_chunks) if text_chunks else str(content)
                        )
                    elif isinstance(content, str):
                        message_content = content
                    else:
                        message_content = str(content)
                elif hasattr(msg, "content"):
                    message_content = str(msg.content)
                else:
                    message_content = str(msg)
                # If agent exists but no message, print '(no message)'
                if agent and not message_content:
                    message_content = "(no message)"
                results.append((agent, message_content, tool_explanation))

        # Extract tool result and explain it
        if "ToolMessage" in str(type(event)) or event.get("status") == "error":
            tool_name = event.get("name")
            tool_content = event.get("content", "")
            tool_explanation = None
            if event.get("status") == "error":
                tool_explanation = (
                    f"[red]Tool '{tool_name}' error:[/red] {tool_content}"
                )
            elif tool_name and tool_content:
                if "write_to_file" in tool_name:
                    tool_explanation = f"[green]File written:[/green] {tool_content}"
                elif "read_file" in tool_name:
                    tool_explanation = (
                        f"[cyan]File read:[/cyan] {tool_content[:200]}..."
                    )
                elif "execute_in_shell" in tool_name:
                    tool_explanation = f"[magenta]Shell command output:[/magenta] {tool_content[:200]}..."
                else:
                    tool_explanation = (
                        f"[blue]Tool '{tool_name}' result:[/blue] {tool_content}"
                    )
            elif tool_name:
                tool_explanation = f"[blue]Tool '{tool_name}' called.[/blue]"
            results.append((agent, None, tool_explanation))

        # Fallback: if nothing is printed, show raw event for debugging
        if not results:
            results.append((None, str(event), None))

        return results
