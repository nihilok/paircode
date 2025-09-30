"""Command-line interface for PairCode."""

from typer import Typer, Option
from rich.console import Console
from rich.prompt import Prompt

from paircode.config_service import ConfigService
from paircode.session_service import SessionService


app = Typer()
console = Console()


@app.command()
def config(
    agent_coder: str = Option(None, help="Name for the coder agent"),
    agent_tester: str = Option(None, help="Name for the tester agent"),
):
    """Configure agent names and settings."""
    config_service = ConfigService()
    config_service.update(agent_coder=agent_coder, agent_tester=agent_tester)
    console.print("[green]Configuration saved![/green]")


@app.command()
def start():
    """Start a paircode agent session."""
    # Load configuration
    config_service = ConfigService()
    coder_name, tester_name, supervisor_name = config_service.get_agent_names()

    # Display welcome message
    console.print("[bold green]Welcome to PairCode![/bold green]")
    console.print(
        f"Agents: [cyan]{coder_name}[/cyan] (coder), "
        f"[magenta]{tester_name}[/magenta] (tester), "
        f"[yellow]{supervisor_name}[/yellow] (supervisor)"
    )

    # Initialize session
    session = SessionService(coder_name, tester_name, supervisor_name)

    # Get initial task
    user_task = Prompt.ask("What code-related problem should the agents solve?")
    console.print("[bold blue]Swarm session starting...[/bold blue]")

    # Process initial task
    for event in session.send_message(user_task):
        for agent, content, tool_explanation in session.extract_event_info(event):
            if agent:
                console.print(f"[bold][{agent}][/bold]", style="yellow")
            if content:
                console.print(content, style="white")
            if tool_explanation:
                console.print(tool_explanation)
            if not agent and not content and not tool_explanation:
                console.print(f"[dim]Raw event:[/dim] {event}")

    # Multi-turn interaction loop
    while True:
        next_input = Prompt.ask("Enter next message (or 'exit' to quit)")
        if next_input.strip().lower() == "exit":
            console.print("[bold yellow]Session ended. Goodbye![/bold yellow]")
            break

        for event in session.send_message(next_input):
            for agent, content, tool_explanation in session.extract_event_info(event):
                if agent:
                    console.print(f"[bold][{agent}][/bold]", style="yellow")
                if content:
                    console.print(content, style="white")
                if tool_explanation:
                    console.print(tool_explanation)
                if not agent and not content and not tool_explanation:
                    console.print(f"[dim]Raw event:[/dim] {event}")


if __name__ == "__main__":
    app()
