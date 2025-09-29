from typer import Typer, Option
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import json
from pathlib import Path
from paircode.agents import create_paircode_swarm

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
def config(agent_coder: str = Option(None, help="Name for the coder agent"),
           agent_tester: str = Option(None, help="Name for the tester agent")):
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
    # coder_name = config.get("agent_coder") or Prompt.ask("Name for the coder agent", default="Coder")
    # tester_name = config.get("agent_tester") or Prompt.ask("Name for the tester agent", default="Tester")
    coder_name = "Jane"
    tester_name = "John"
    supervisor_name = "Supervisor"
    console.print(f"Agents: [cyan]{coder_name}[/cyan] (coder), [magenta]{tester_name}[/magenta] (tester), [yellow]{supervisor_name}[/yellow] (supervisor)")
    swarm = create_paircode_swarm(coder_name, tester_name, supervisor_name)
    user_task = Prompt.ask("What code-related problem should the agents solve?")
    console.print("[bold blue]Swarm session starting...[/bold blue]")
    config_obj = {"configurable": {"thread_id": "1"}}
    def print_tool_results(result):
        # Look for tool call results in the output and print them nicely
        explanations = []
        def _extract(result):
            if isinstance(result, dict):
                for k, v in result.items():
                    _extract(v)
            elif isinstance(result, list):
                for item in result:
                    _extract(item)
            elif hasattr(result, 'name') and hasattr(result, 'content'):
                # Likely a ToolMessage or similar
                explanation = f"[bold]{result.name}[/bold]: {result.content}\n[dim]Above is the result of calling one or more tools. The user cannot see the results, so you should explain them to the user if referencing them in your answer.[/dim]"
                explanations.append(explanation)
        _extract(result)
        if explanations:
            console.print(Panel("\n\n".join(explanations), title="Tool Results Explained", style="green"))
    # First turn
    result = swarm.invoke({"messages": [{"role": "user", "content": user_task}]}, config_obj)
    console.print("[bold]Swarm output:[/bold]")
    console.print(result)
    print_tool_results(result)
    # Optionally, allow multi-turn interaction
    while True:
        next_input = Prompt.ask("Enter next message (or 'exit' to quit)")
        if next_input.strip().lower() == "exit":
            break
        result = swarm.invoke({"messages": [{"role": "user", "content": next_input}]}, config_obj)
        console.print("[bold]Swarm output:[/bold]")
        console.print(result)
        print_tool_results(result)

# More CLI commands and agent logic will be added here.
