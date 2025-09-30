from typer import Typer, Option
from rich.console import Console
from rich.prompt import Prompt
import json
from pathlib import Path
from paircode.agents import PaircodeSwarmService

app = Typer()
console = Console()

CONFIG_PATH = Path.home() / ".paircode_config.json"


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


@app.command()
def config(
    agent_coder: str = Option(None, help="Name for the coder agent"),
    agent_tester: str = Option(None, help="Name for the tester agent"),
):
    """Configure agent names and settings."""
    config = load_config()
    if agent_coder:
        config["agent_coder"] = agent_coder
    if agent_tester:
        config["agent_tester"] = agent_tester
    save_config(config)
    console.print("[green]Configuration saved![/green]")


@app.command()
def start():
    """Start a paircode agent session."""
    config = load_config()
    console.print("[bold green]Welcome to PairCode![/bold green]")
    coder_name = config.get("coder_name", "Alice")
    tester_name = config.get("tester_name", "Bob")
    supervisor_name = config.get("supervisor_name", "Chief")
    console.print(
        f"Agents: [cyan]{coder_name}[/cyan] (coder), [magenta]{tester_name}[/magenta] (tester), [yellow]{supervisor_name}[/yellow] (supervisor)"
    )
    swarm = PaircodeSwarmService(coder_name, tester_name, supervisor_name)
    user_task = Prompt.ask("What code-related problem should the agents solve?")
    console.print("[bold blue]Swarm session starting...[/bold blue]")
    config_obj = {"configurable": {"thread_id": "1"}}

    def print_streamed_event(event):
        # Print agent name and latest message if available
        if isinstance(event, dict):
            agent = event.get("active_agent") or event.get("agent")
            messages = event.get("messages")
            if agent:
                console.print(f"[bold][{agent}][/bold]")
            if messages:
                last_msg = (
                    messages[-1] if isinstance(messages, list) and messages else None
                )
                if last_msg:
                    if isinstance(last_msg, dict):
                        role = last_msg.get("role", "")
                        content = last_msg.get("content", "")
                        console.print(f"[{role}] {content}")
                    else:
                        console.print(str(last_msg))
        else:
            console.print(str(event))

    # First turn (streamed)
    console.print("[bold]Swarm output (streamed):[/bold]")
    for event in swarm.stream(
        {"messages": [{"role": "user", "content": user_task}]}, config_obj
    ):
        print_streamed_event(event)
    # Optionally, allow multi-turn interaction
    while True:
        next_input = Prompt.ask("Enter next message (or 'exit' to quit)")
        if next_input.strip().lower() == "exit":
            break
        console.print("[bold]Swarm output (streamed):[/bold]")
        for event in swarm.stream(
            {"messages": [{"role": "user", "content": next_input}]}, config_obj
        ):
            print_streamed_event(event)
