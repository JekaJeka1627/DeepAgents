"""
DeepAgents Live UI Module

Provides a Claude Code-style interface with:
- Persistent status bar at the bottom
- Scrolling conversation area above
- Clean input handling
- Real-time status updates
"""
import threading
import time
from typing import List, Optional
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.markup import escape
from deepagents_cli.agent.status_line import get_status_line


class LiveUI:
    """Manages the live UI with persistent status bar."""
    
    def __init__(self):
        self.console = Console()
        self.conversation_lines: List[str] = []
        self.current_input = ""
        self.status_text = get_status_line()
        self.live: Optional[Live] = None
        self._running = False
        self._status_update_thread: Optional[threading.Thread] = None
        
    def create_layout(self) -> Layout:
        """Create the main layout with conversation and status bar."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="conversation", ratio=1),
            Layout(name="input_area", size=3),
            Layout(name="status", size=1)
        )
        
        return layout
    
    def update_conversation_area(self, layout: Layout) -> None:
        """Update the conversation area with recent messages."""
        # Show last 50 lines to prevent memory issues
        display_lines = self.conversation_lines[-50:] if len(self.conversation_lines) > 50 else self.conversation_lines
        
        if display_lines:
            conversation_text = "\n".join(display_lines)
        else:
            conversation_text = "🧠 [bold]DeepAgents CLI[/bold] — type [cyan]:help[/cyan] for commands.\n[dim]([yellow]Your text[/yellow] is yellow, [white]DeepAgents responses[/white] are white)[/dim]"
        
        layout["conversation"].update(Panel(
            conversation_text,
            title="DeepAgents Conversation",
            border_style="blue",
            height=None
        ))
    
    def update_input_area(self, layout: Layout) -> None:
        """Update the input area."""
        input_text = f"[yellow]You:[/yellow] {self.current_input}█"  # Adding cursor
        layout["input_area"].update(Panel(
            input_text,
            title="Input",
            border_style="green",
            height=3
        ))
    
    def update_status_bar(self, layout: Layout) -> None:
        """Update the status bar with current information."""
        layout["status"].update(Panel(
            f"[cyan]{self.status_text}[/cyan]",
            border_style="cyan",
            height=1
        ))
    
    def update_display(self, layout: Layout) -> None:
        """Update all areas of the display."""
        self.update_conversation_area(layout)
        self.update_input_area(layout)
        self.update_status_bar(layout)
    
    def add_message(self, message: str, sender: str = "system") -> None:
        """Add a message to the conversation."""
        if sender == "user":
            formatted_msg = f"[yellow]You:[/yellow] {escape(message)}"
        elif sender == "assistant" or sender == "deepagents":
            formatted_msg = f"[white]DeepAgents:[/white] {escape(message)}"
        else:
            formatted_msg = escape(message)
        
        self.conversation_lines.append(formatted_msg)
        
        # Keep conversation manageable
        if len(self.conversation_lines) > 100:
            self.conversation_lines = self.conversation_lines[-80:]  # Keep last 80 lines
    
    def set_input(self, text: str) -> None:
        """Set the current input text."""
        self.current_input = text
    
    def clear_input(self) -> None:
        """Clear the input area."""
        self.current_input = ""
    
    def start_status_updates(self) -> None:
        """Start background thread to update status every second."""
        def update_status():
            while self._running:
                self.status_text = get_status_line()
                time.sleep(1)  # Update every second
        
        self._status_update_thread = threading.Thread(target=update_status, daemon=True)
        self._status_update_thread.start()
    
    def start(self) -> None:
        """Start the live UI."""
        self._running = True
        layout = self.create_layout()
        
        # Add initial message
        self.add_message("🧠 DeepAgents CLI — type :help for commands.", "system")
        self.add_message("(Your text is yellow, DeepAgents responses are white)", "system")
        
        # Start status updates
        self.start_status_updates()
        
        self.live = Live(
            layout,
            console=self.console,
            refresh_per_second=10,
            screen=True
        )
        
        with self.live:
            while self._running:
                self.update_display(layout)
                self.live.update(layout)
                time.sleep(0.1)  # Small delay to prevent excessive updates
    
    def stop(self) -> None:
        """Stop the live UI."""
        self._running = False
        if self.live:
            self.live.stop()
    
    def get_input(self) -> str:
        """Get input from user (to be called from main thread)."""
        # This will be handled by the main CLI loop
        # The live UI will show the input as it's being typed
        pass


# Global UI instance
live_ui = LiveUI()