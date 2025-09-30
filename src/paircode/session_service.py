"""Session service for managing PairCode swarm sessions."""

from typing import Generator, Dict, Any, Optional
from paircode.agents import PaircodeSwarmService


class SessionService:
    """Service for managing swarm coding sessions."""

    def __init__(self, coder_name: str, tester_name: str, supervisor_name: str):
        """Initialize a session service.

        Args:
            coder_name: Name of the coder agent
            tester_name: Name of the tester agent
            supervisor_name: Name of the supervisor agent
        """
        self.coder_name = coder_name
        self.tester_name = tester_name
        self.supervisor_name = supervisor_name
        self.swarm = PaircodeSwarmService(coder_name, tester_name, supervisor_name)
        self.config = {"configurable": {"thread_id": "1"}}

    def send_message(self, message: str) -> Generator[Dict[str, Any], None, None]:
        """Send a message to the swarm and stream responses.

        Args:
            message: User message to send to the swarm

        Yields:
            Event dictionaries from the swarm stream
        """
        message_payload = {"messages": [{"role": "user", "content": message}]}
        yield from self.swarm.stream(message_payload, self.config)

    @staticmethod
    def extract_event_info(
        event: Dict[str, Any],
    ) -> list[tuple[Optional[str], Optional[str], Optional[str]]]:
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
