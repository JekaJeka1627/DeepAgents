"""
DeepAgents CLI with exact Claude Code-style interface

Replicates Claude Code's UI:
- Main conversation area (scrollable)
- Status bar at bottom with live updates  
- Input prompt below status bar
- Same visual style as Claude Code
"""
import sys
import argparse
import os
import threading
import time
from pathlib import Path
from typing import Any, List
from datetime import datetime

from deepagents_cli.agent.factory import create_agent
from deepagents_cli.agent import config as cfg
from deepagents_cli.agent.status_line import get_status_line
from deepagents_cli.agent.autocomplete import handle_slash_input

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.markup import escape
from rich import print as rprint

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


class ClaudeCodeUI:
    """Exact replica of Claude Code's UI layout."""
    
    def __init__(self):
        self.console = Console()
        self.status_line = ""
        self.update_status()
        
    def update_status(self):
        """Update the status line."""
        self.status_line = get_status_line()
    
    def print_status_bar(self):
        """Print the status bar (like Claude Code)."""
        # Clear line and print status
        status_panel = Panel(
            f"[bright_cyan]{self.status_line}[/bright_cyan]",
            border_style="bright_blue",
            padding=(0, 1)
        )
        self.console.print(status_panel)
    
    def print_header(self):
        """Print the initial header."""
        self.console.print("🧠 [bold]DeepAgents CLI[/bold] — type [cyan]:help[/cyan] for commands.")
        self.console.print("[dim]([yellow]Your text[/yellow] is yellow, [white]DeepAgents responses[/white] are white)[/dim]\n")
        self.console.print(f"[dim][sandbox][/dim] root: [bold]{cfg.FS_ROOT}[/bold]")
        self.console.print(f"[dim][sandbox][/dim] write-enabled: [bold]{cfg.ALLOW_FS_WRITE}[/bold]") 
        self.console.print(f"[dim][sandbox][/dim] auto-apply: [bold]{cfg.ALLOW_AUTO_APPLY}[/bold]")
        self.console.print()


def _safe_str(obj: Any) -> str:
    """Extract text from agent response."""
    try:
        if obj is None:
            return ""
        if isinstance(obj, str):
            return obj
        if hasattr(obj, "content"):
            return str(getattr(obj, "content"))
        if isinstance(obj, dict):
            for k in ("output_text", "text", "output"):
                if k in obj and isinstance(obj[k], str):
                    return obj[k]
            msgs = obj.get("messages")
            if isinstance(msgs, list) and msgs:
                for m in reversed(msgs):
                    if hasattr(m, "content"):
                        return str(getattr(m, "content"))
                    if isinstance(m, dict) and "content" in m:
                        return str(m["content"])
            return str(obj)
        if isinstance(obj, list) and obj:
            for m in reversed(obj):
                if hasattr(m, "content"):
                    return str(getattr(m, "content"))
        return str(obj)
    except Exception:
        return "[No printable response]"


def print_help(console: Console) -> None:
    """Print help information."""
    console.print(Panel.fit(
        """
Commands:
  :help           Show this help (note the leading colon)
  :tools          List available tools
  :model          Show provider/model selection and env-based priority
  :safety         Show safety settings and conversation stats
  :log on|off     Toggle trace logging for tool calls
  :debug on|off   Toggle raw result debug printing
  :cd PATH        Change sandbox root to PATH
  :quit / :exit   Quit the CLI

Claude Code-Style Commands:
  /status         Show comprehensive status line with time, model, git info
  /read FILE      Read file with syntax highlighting
  /write FILE     Write content to file with backup  
  /edit FILE      Search and replace in file
  /ls [PATH]      List files with rich formatting
  /grep PATTERN   Search files with context
  /bash COMMAND   Execute shell command safely
  /task add DESC  Add task to current list
  /task done ID   Mark task as completed
  /task list      Show all tasks
  /task clear     Clear completed tasks
  /search QUERY   Web search (like Claude Code)
  /fetch URL      Fetch web content

Memory Commands:
  /memory history Show recent conversation history
  /memory projects List remembered projects
  /memory note    Add note about current project
  /memory forget  Clear memory for project

Just type to chat with the agent.
        """.strip(), title="Help", border_style="cyan"))


def main(argv: List[str]) -> int:
    """Main CLI with Claude Code UI."""
    parser = argparse.ArgumentParser(prog="deepagents-claude-ui", add_help=True)
    parser.add_argument("--cwd", type=str, default=None, help="Set working directory/sandbox root")
    parser.add_argument("--allow-write", action="store_true", help="Allow host filesystem writes")
    parser.add_argument("--auto-apply", action="store_true", help="Auto-apply write proposals")
    args = parser.parse_args(argv)

    # Configure sandbox
    if args.cwd:
        try:
            cfg.set_fs_root(args.cwd)
        except Exception as e:
            print(f"[config] failed to set --cwd: {e}")
            return 1
    cfg.set_allow_fs_write(bool(args.allow_write))
    cfg.set_allow_auto_apply(bool(args.auto_apply))

    # Initialize UI
    ui = ClaudeCodeUI()
    console = ui.console
    
    # Print header
    ui.print_header()
    
    # Create agent
    try:
        agent = create_agent()
    except Exception as e:
        console.print(Panel.fit(str(e), title="Failed to create agent", border_style="red"))
        return 1

    # Print initial status bar
    ui.print_status_bar()

    # Main conversation loop
    while True:
        try:
            # Display user prompt in yellow and get input (like Claude Code)
            console.print("[yellow]You: [/yellow]", end="")
            user = input().strip()
            
            # Check for autocomplete on slash commands
            if user.startswith('/') and len(user) > 1:
                command_part = user[1:]
                from deepagents_cli.agent.autocomplete import get_matching_commands
                matches = get_matching_commands(command_part)
                
                # Show autocomplete menu if there are matches and it's not an exact match
                if matches and (len(matches) > 1 or (len(matches) == 1 and matches[0][0] != command_part)):
                    console.print()  # New line
                    
                    # Show autocomplete options
                    console.print("╭─ Available Commands ─────────────────────────────────────╮")
                    for cmd, desc in matches[:10]:  # Show max 10 options
                        cmd_display = f"/{cmd}"
                        console.print(f"│ [green]{cmd_display:<20}[/green] {desc:<35} │")
                    console.print("╰──────────────────────────────────────────────────────────╯")
                    console.print()
                    
                    # Ask for input again
                    console.print("[yellow]You: [/yellow]", end="")
                    user = input().strip()
            
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user:
            continue
        
        # Add some spacing for better visual separation 
        console.print()

        # Handle commands
        if user in (":quit", ":exit"):
            break
        elif user == ":help":
            print_help(console)
            continue
        elif user.startswith('/status'):
            # Show status command
            status = get_status_line()
            console.print(Panel.fit(
                status,
                title="🚀 DeepAgents Status", 
                border_style="cyan"
            ))
            continue
        elif user.startswith('/'):
            # Handle autocomplete for slash commands
            if handle_slash_input(user):
                continue
                
            # Handle other slash commands here
            # For now, just show that we detected a slash command
            console.print(f"[dim]Command detected: {user}[/dim]")
            console.print("[dim]Full slash command implementation coming soon...[/dim]")
            continue

        # Regular chat with agent
        try:
            result = agent.invoke({"messages": [{"role": "user", "content": user}]})
            text = _safe_str(result)
            
            if text.strip():
                # Display DeepAgents response in white (like Claude Code)
                console.print("\n[white]DeepAgents:[/white]")
                console.print(text)
            else:
                console.print("[dim](no text output)[/dim]")
                
        except KeyboardInterrupt:
            console.print("\n⚠️ Interrupted by user (Ctrl+C)")
            continue
        except Exception as e:
            console.print(Panel.fit(
                f"🚨 Error: {str(e)}\n\n💡 Try:\n• Asking a simpler question\n• Using :help for available commands\n• Restarting if problems persist",
                title="Error invoking agent", border_style="red"
            ))

    console.print("Goodbye.")
    return 0


def console_main() -> None:
    """Entry point for console_scripts."""
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    console_main()