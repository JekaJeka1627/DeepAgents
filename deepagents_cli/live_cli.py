"""
DeepAgents Live CLI with Claude Code-style UI

Features:
- Persistent status bar at bottom (like Claude Code)
- Scrolling conversation area
- Enhanced input handling
- Real-time status updates
"""
import sys
import argparse
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, List
from datetime import datetime

# Import DeepAgents components
from deepagents_cli.agent.factory import create_agent
from deepagents_cli.agent.tools import get_default_tools
from deepagents_cli.agent.logging import set_verbose, is_verbose
from deepagents_cli.agent.state import save_vfs, load_vfs
from deepagents_cli.agent.factory import get_last_selection
from deepagents_cli.agent import config as cfg
from deepagents_cli.agent.status_line import get_status_line

# Rich components for enhanced UI
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.markup import escape

# Load environment variables
try:
    from dotenv import load_dotenv
    env_paths = [
        Path.cwd() / '.env',
        Path(__file__).parent.parent / '.env',
        Path.home() / '.env',
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
    else:
        load_dotenv()
except Exception:
    pass


class ClaudeCodeStyleUI:
    """Claude Code-style UI with persistent status bar."""
    
    def __init__(self):
        self.console = Console()
        self.conversation_lines: List[str] = []
        self.running = False
        self.live: Live = None
        self.layout: Layout = None
        
    def create_layout(self) -> Layout:
        """Create the main layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="conversation", ratio=1), 
            Layout(name="status", size=1)
        )
        return layout
    
    def update_header(self) -> None:
        """Update header area."""
        header_text = (
            "🧠 [bold]DeepAgents CLI[/bold] — type [cyan]:help[/cyan] for commands.\n"
            "[dim]([yellow]Your text[/yellow] is yellow, [white]DeepAgents responses[/white] are white)[/dim]\n"
            f"[dim][sandbox][/dim] root: [bold]{cfg.FS_ROOT}[/bold] | "
            f"write-enabled: [bold]{cfg.ALLOW_FS_WRITE}[/bold] | "
            f"auto-apply: [bold]{cfg.ALLOW_AUTO_APPLY}[/bold]"
        )
        self.layout["header"].update(Panel(
            header_text,
            border_style="cyan"
        ))
    
    def update_conversation(self) -> None:
        """Update conversation area."""
        if self.conversation_lines:
            # Show recent conversation
            display_lines = self.conversation_lines[-40:] if len(self.conversation_lines) > 40 else self.conversation_lines
            conversation_text = "\n".join(display_lines)
        else:
            conversation_text = "[dim]Ready for your input...[/dim]"
        
        self.layout["conversation"].update(Panel(
            conversation_text,
            title="Conversation",
            border_style="blue"
        ))
    
    def update_status(self) -> None:
        """Update status bar."""
        status_text = get_status_line()
        self.layout["status"].update(Panel(
            f"[cyan]{status_text}[/cyan]",
            border_style="cyan"
        ))
    
    def add_message(self, message: str, sender: str = "system") -> None:
        """Add a message to conversation."""
        if sender == "user":
            formatted = f"[yellow]You:[/yellow] {escape(message)}"
        elif sender == "assistant":
            formatted = f"[white]DeepAgents:[/white] {escape(message)}"  
        else:
            formatted = escape(message)
        
        self.conversation_lines.append(formatted)
        
        # Keep conversation manageable
        if len(self.conversation_lines) > 100:
            self.conversation_lines = self.conversation_lines[-80:]
    
    def update_display(self) -> None:
        """Update all display areas."""
        self.update_header()
        self.update_conversation() 
        self.update_status()
    
    def start_live_display(self) -> None:
        """Start the live display in a separate thread."""
        self.layout = self.create_layout()
        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=2,
            screen=False  # Don't take over entire screen
        )
        
        def display_loop():
            with self.live:
                while self.running:
                    self.update_display()
                    time.sleep(0.5)
        
        display_thread = threading.Thread(target=display_loop, daemon=True)
        display_thread.start()
    
    def stop(self) -> None:
        """Stop the live display."""
        self.running = False
        if self.live:
            self.live.stop()


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


def main(argv: List[str]) -> int:
    """Main CLI function with Claude Code-style UI."""
    parser = argparse.ArgumentParser(prog="deepagents-live", add_help=True)
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

    # Create UI
    ui = ClaudeCodeStyleUI()
    ui.running = True
    ui.start_live_display()
    
    # Create agent
    try:
        agent = create_agent()
    except Exception as e:
        ui.add_message(f"Failed to create agent: {e}", "system")
        return 1

    ui.add_message("DeepAgents ready! Type your message or use commands.", "system")
    
    try:
        while True:
            try:
                # Get user input
                ui.console.print("\n[yellow]You:[/yellow] ", end="")
                user = input().strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user:
                continue
            
            # Add user message to conversation
            ui.add_message(user, "user")
            
            # Handle special commands
            if user in (":quit", ":exit"):
                break
            elif user == ":help":
                help_text = """
Commands:
  :help           Show this help
  :quit/:exit     Quit
  /status         Show status line
  /[command]      Use any DeepAgents command
  
Just type to chat with the agent.
                """
                ui.add_message(help_text, "system")
                continue
            elif user.startswith('/status'):
                status = get_status_line()
                ui.add_message(f"Status: {status}", "system")
                continue
            
            # Handle slash commands and regular chat
            try:
                # Simple agent invocation
                result = agent.invoke({"messages": [{"role": "user", "content": user}]})
                text = _safe_str(result)
                
                if text.strip():
                    ui.add_message(text, "assistant")
                else:
                    ui.add_message("(no text output)", "system")
                    
            except Exception as e:
                ui.add_message(f"Error: {str(e)}", "system")

    finally:
        ui.stop()
        ui.console.print("Goodbye.")
    
    return 0


def console_main() -> None:
    """Entry point for live CLI."""
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    console_main()