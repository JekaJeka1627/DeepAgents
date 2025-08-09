"""
DeepAgents Claude Code UI using Rich

Provides Claude Code-style interface with:
- Persistent status bar at bottom
- Autocomplete menu above status bar  
- Proper text input handling
- Clean conversation display
"""
import sys
import argparse
import threading
import time
from typing import Any, List, Optional

from deepagents_cli.agent.factory import create_agent
from deepagents_cli.agent import config as cfg
from deepagents_cli.agent.status_line import get_status_line
from deepagents_cli.agent.autocomplete import get_matching_commands, COMMANDS

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markup import escape

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


class RichClaudeUI:
    """Rich-based Claude Code UI."""
    
    def __init__(self):
        self.console = Console()
        self.conversation_lines: List[str] = []
        self.current_input = ""
        self.autocomplete_visible = False
        self.autocomplete_matches = []
        self.running = False
        self.live: Optional[Live] = None
        
    def create_layout(self) -> Layout:
        """Create the main layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="conversation", ratio=1),
            Layout(name="autocomplete", size=0),  # Hidden by default
            Layout(name="input", size=3),
            Layout(name="status", size=1)
        )
        
        return layout
        
    def update_conversation(self, layout: Layout):
        """Update conversation area."""
        if self.conversation_lines:
            # Show recent messages (last 30 lines)
            display_lines = self.conversation_lines[-30:] if len(self.conversation_lines) > 30 else self.conversation_lines
            conversation_text = "\n".join(display_lines)
        else:
            conversation_text = "Ready for your input..."
            
        layout["conversation"].update(Panel(
            conversation_text,
            title="DeepAgents Conversation",
            border_style="blue",
            padding=(1, 2)
        ))
        
    def update_autocomplete(self, layout: Layout):
        """Update autocomplete area."""
        if self.autocomplete_visible and self.autocomplete_matches:
            # Create table for autocomplete options
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Command", style="green", no_wrap=True)
            table.add_column("Description", style="white")
            
            for cmd, desc in self.autocomplete_matches[:8]:  # Show max 8 options
                table.add_row(f"/{cmd}", desc)
                
            layout["autocomplete"].update(Panel(
                table,
                title="Commands",
                border_style="yellow",
                height=min(len(self.autocomplete_matches) + 2, 10)
            ))
            layout["autocomplete"].size = min(len(self.autocomplete_matches) + 2, 10)
        else:
            layout["autocomplete"].update("")
            layout["autocomplete"].size = 0
            
    def update_input(self, layout: Layout):
        """Update input area."""
        input_display = f"[yellow]You:[/yellow] {self.current_input}[dim]█[/dim]"  # Show cursor
        
        layout["input"].update(Panel(
            input_display,
            border_style="green",
            padding=(0, 1)
        ))
        
    def update_status(self, layout: Layout):
        """Update status bar."""
        status_text = get_status_line()
        
        layout["status"].update(Panel(
            f"[cyan]{status_text}[/cyan]",
            border_style="cyan",
            padding=(0, 1)
        ))
        
    def add_message(self, text: str, sender: str = "system"):
        """Add message to conversation."""
        if sender == "user":
            formatted = f"[yellow]You:[/yellow] {escape(text)}"
        elif sender == "assistant":
            formatted = f"[white]DeepAgents:[/white] {escape(text)}"
        else:
            formatted = escape(text)
            
        self.conversation_lines.append(formatted)
        
        # Keep manageable size
        if len(self.conversation_lines) > 100:
            self.conversation_lines = self.conversation_lines[-80:]
            
    def check_autocomplete(self):
        """Check if autocomplete should be shown."""
        if self.current_input.startswith('/'):
            command_part = self.current_input[1:]
            
            matches = []
            for cmd, desc in COMMANDS.items():
                if cmd.startswith(command_part.lower()):
                    matches.append((cmd, desc))
                    
            # Show autocomplete if there are matches and it's not an exact command
            if matches and (not command_part or len(matches) > 1 or command_part not in COMMANDS):
                self.autocomplete_visible = True
                self.autocomplete_matches = matches
            else:
                self.autocomplete_visible = False
                self.autocomplete_matches = []
        else:
            self.autocomplete_visible = False
            self.autocomplete_matches = []
            
    def update_display(self, layout: Layout):
        """Update all display components."""
        self.update_conversation(layout)
        self.update_autocomplete(layout)
        self.update_input(layout)
        self.update_status(layout)
        
    def start_live_display(self, layout: Layout):
        """Start the live display."""
        self.live = Live(
            layout,
            console=self.console,
            refresh_per_second=10,
            screen=True
        )
        
        # Background status updater
        def status_updater():
            while self.running:
                if self.live:
                    self.update_status(layout)
                time.sleep(1)
                
        threading.Thread(target=status_updater, daemon=True).start()
        
        return self.live
        
    def get_input(self) -> str:
        """Get input from user with autocomplete."""
        self.current_input = ""
        
        # Input loop
        while True:
            try:
                # Simple input for now - we'll enhance this
                self.console.print("\n[yellow]You:[/yellow] ", end="")
                user_input = input().strip()
                
                if user_input:
                    return user_input
                    
            except (EOFError, KeyboardInterrupt):
                raise


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
        return str(obj)
    except Exception:
        return "[No printable response]"


def main(argv: List[str]) -> int:
    """Main function."""
    parser = argparse.ArgumentParser(prog="deepagents-rich-ui")
    parser.add_argument("--cwd", type=str, default=None, help="Set working directory")
    parser.add_argument("--allow-write", action="store_true", help="Allow writes")
    parser.add_argument("--auto-apply", action="store_true", help="Auto-apply")
    args = parser.parse_args(argv)
    
    # Configure
    if args.cwd:
        try:
            cfg.set_fs_root(args.cwd)
        except Exception as e:
            print(f"Config error: {e}")
            return 1
    cfg.set_allow_fs_write(bool(args.allow_write))
    cfg.set_allow_auto_apply(bool(args.auto_apply))
    
    # Create components
    try:
        agent = create_agent()
    except Exception as e:
        print(f"Failed to create agent: {e}")
        return 1
        
    ui = RichClaudeUI()
    ui.running = True
    
    # Add initial messages
    ui.add_message("🧠 DeepAgents CLI — type :help for commands.", "system")
    ui.add_message("(Your text is yellow, DeepAgents responses are white)", "system")
    ui.add_message(f"Sandbox: {cfg.FS_ROOT} | Write: {cfg.ALLOW_FS_WRITE}", "system")
    ui.add_message("", "system")  # Empty line
    
    layout = ui.create_layout()
    
    try:
        with ui.start_live_display(layout):
            while ui.running:
                ui.update_display(layout)
                
                # Get user input
                try:
                    user_input = ui.get_input()
                except (EOFError, KeyboardInterrupt):
                    break
                    
                if not user_input:
                    continue
                    
                # Add to conversation
                ui.add_message(user_input, "user")
                ui.update_display(layout)
                
                # Handle commands
                if user_input in (":quit", ":exit"):
                    break
                elif user_input == ":help":
                    help_text = """Commands:
:help - Show help
:quit - Exit
/status - Show status
/[cmd] - Slash commands
Type normally to chat!"""
                    ui.add_message(help_text, "system")
                elif user_input.startswith('/status'):
                    status = get_status_line() 
                    ui.add_message(f"Status: {status}", "system")
                elif user_input.startswith('/'):
                    # Show that we detected a slash command
                    from deepagents_cli.agent.autocomplete import show_command_menu
                    ui.add_message(f"Detected command: {user_input}", "system")
                    ui.add_message("Autocomplete will work in next version...", "system")
                else:
                    # Regular chat
                    try:
                        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
                        response = _safe_str(result)
                        ui.add_message(response, "assistant")
                    except Exception as e:
                        ui.add_message(f"Error: {e}", "system")
                        
                ui.update_display(layout)
                
    except KeyboardInterrupt:
        pass
    finally:
        ui.running = False
        ui.console.print("\nGoodbye!")
        
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))