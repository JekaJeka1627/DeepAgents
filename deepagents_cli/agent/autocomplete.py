"""
DeepAgents Command Autocomplete Module

Provides autocomplete functionality similar to Claude Code when typing '/' commands.
Shows a menu of available commands with descriptions.
"""
from typing import List, Dict, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Define all available commands with their descriptions
COMMANDS: Dict[str, str] = {
    # Core status and info
    "status": "Show comprehensive status line with time, model, git info",
    
    # File operations
    "read": "Read file with syntax highlighting",
    "write": "Write content to file with backup",
    "edit": "Search and replace in file",
    "ls": "List files with rich formatting",
    "grep": "Search files with context",
    "bash": "Execute shell command safely",
    
    # Task management
    "task": "Task management (add/done/list/clear)",
    
    # Web operations
    "search": "Web search (like Claude Code)",
    "fetch": "Fetch web content",
    
    # Memory operations
    "memory": "Memory management (history/projects/note/forget)",
    
    # Specialized agents
    "agent": "Specialized agent operations (list/help/stats/auto/direct)",
    
    # Smart workflows
    "workflow": "Smart workflow management (list/help/history/suggest/execute)",
    
    # Model management
    "model": "Model management (list/set/benchmark/costs/features)",
}

# Subcommands for complex commands
SUBCOMMANDS: Dict[str, Dict[str, str]] = {
    "task": {
        "add": "Add task to current list",
        "done": "Mark task as completed",
        "list": "Show all tasks",
        "clear": "Clear completed tasks"
    },
    "memory": {
        "history": "Show recent conversation history",
        "projects": "List remembered projects",
        "note": "Add note about current project",
        "forget": "Clear memory for project"
    },
    "agent": {
        "list": "Show all available specialized agents",
        "help": "Detailed help for agent commands",
        "stats": "Show agent usage statistics",
        "auto": "Auto-route question to best agent"
    },
    "workflow": {
        "list": "Show all available smart workflows",
        "help": "Detailed help for workflow commands", 
        "history": "Show workflow execution history",
        "suggest": "Get workflow recommendations"
    },
    "model": {
        "list": "Show GPT-5 variants and pricing",
        "set": "Switch to specific model",
        "benchmark": "Show performance comparisons",
        "costs": "Show cost analysis",
        "features": "Show feature comparisons"
    }
}


class CommandAutocomplete:
    """Handles command autocomplete functionality."""
    
    def __init__(self):
        self.console = Console()
    
    def get_matching_commands(self, partial: str) -> List[Tuple[str, str]]:
        """Get commands that match the partial input."""
        if not partial:
            # Return all commands if no partial input
            return [(cmd, desc) for cmd, desc in COMMANDS.items()]
        
        partial_lower = partial.lower()
        matches = []
        
        # Match main commands
        for cmd, desc in COMMANDS.items():
            if cmd.startswith(partial_lower):
                matches.append((cmd, desc))
        
        # If partial contains a space, check for subcommands
        if ' ' in partial:
            parts = partial.split()
            if len(parts) >= 2:
                main_cmd = parts[0].lower()
                sub_partial = parts[1].lower()
                
                if main_cmd in SUBCOMMANDS:
                    for subcmd, desc in SUBCOMMANDS[main_cmd].items():
                        if subcmd.startswith(sub_partial):
                            full_cmd = f"{main_cmd} {subcmd}"
                            matches.append((full_cmd, desc))
        
        # Sort matches by relevance (exact matches first, then alphabetical)
        matches.sort(key=lambda x: (not x[0].startswith(partial_lower), x[0]))
        
        return matches
    
    def show_autocomplete_menu(self, partial: str = "") -> None:
        """Display the autocomplete menu for the given partial input."""
        matches = self.get_matching_commands(partial)
        
        if not matches:
            self.console.print("No matching commands found.")
            return
        
        # Create table for commands
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Command", style="green", no_wrap=True)
        table.add_column("Description", style="white")
        
        # Add matching commands to table
        for cmd, desc in matches[:15]:  # Limit to 15 results
            table.add_row(f"/{cmd}", desc)
        
        # Show more indicator if there are more matches
        if len(matches) > 15:
            table.add_row("...", f"({len(matches) - 15} more matches)")
        
        # Create panel with title
        title = "Available Commands"
        if partial:
            title = f"Commands matching '/{partial}'"
        
        panel = Panel(
            table,
            title=title,
            border_style="cyan",
            padding=(0, 1)
        )
        
        self.console.print(panel)
    
    def get_command_suggestion(self, partial: str) -> str:
        """Get the best command suggestion for partial input."""
        matches = self.get_matching_commands(partial)
        
        if matches:
            # Return the first (best) match
            return matches[0][0]
        
        return partial


# Global autocomplete instance
autocomplete = CommandAutocomplete()


def show_command_menu(partial: str = "") -> None:
    """Show the command autocomplete menu."""
    autocomplete.show_autocomplete_menu(partial)


def get_command_completion(partial: str) -> str:
    """Get command completion suggestion."""
    return autocomplete.get_command_suggestion(partial)


def get_matching_commands(partial: str) -> List[Tuple[str, str]]:
    """Get matching commands for partial input."""
    return autocomplete.get_matching_commands(partial)


def handle_slash_input(user_input: str) -> bool:
    """
    Handle when user types something starting with '/'.
    Returns True if autocomplete was shown, False if command should be executed.
    """
    if not user_input.startswith('/'):
        return False
    
    # Remove the leading '/'
    command_part = user_input[1:]
    
    # If just '/' or incomplete command, show autocomplete
    if not command_part or (command_part and not any(command_part.startswith(cmd) for cmd in COMMANDS.keys())):
        show_command_menu(command_part)
        return True
    
    # Check if it's a partial match that could benefit from autocomplete
    matches = autocomplete.get_matching_commands(command_part)
    
    # If there are multiple matches and the input doesn't exactly match any command
    if len(matches) > 1 and command_part not in COMMANDS:
        show_command_menu(command_part)
        return True
    
    # Otherwise, let the command execute normally
    return False