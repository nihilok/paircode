"""Command-line interface for PairCode."""

from typer import Typer, Option
from rich.console import Console
from rich.prompt import Prompt

from paircode.config_service import ConfigService
from paircode.multi_agent_flow import run_multi_agent_flow


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
    """Start a supervisor multi-agent session."""
    # Display welcome message
    console.print(
        "[bold green]Welcome to PairCode! Supervisor Multi-Agent Flow.[/bold green]"
    )
    user_task = Prompt.ask("What code-related problem should the agents solve?")
    console.print("[bold blue]Session starting...[/bold blue]")
    run_multi_agent_flow(user_task)


if __name__ == "__main__":
    app()
