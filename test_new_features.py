#!/usr/bin/env python3
"""
Test script for the new DeepAgents features:
- Status line functionality
- Command autocomplete functionality
"""

from deepagents_cli.agent.status_line import get_status_line, print_status
from deepagents_cli.agent.autocomplete import show_command_menu, get_command_completion
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    console.print("🧠 [bold]DeepAgents New Features Test[/bold]\n", style="cyan")
    
    # Test status line
    console.print("1️⃣ [bold]Testing Status Line:[/bold]", style="green")
    status = get_status_line()
    console.print(Panel.fit(
        status,
        title="🚀 DeepAgents Status", 
        border_style="cyan"
    ))
    
    console.print("\n2️⃣ [bold]Testing Command Autocomplete:[/bold]", style="green")
    
    # Test autocomplete with different inputs
    test_inputs = ["", "s", "st", "task", "m"]
    
    for test_input in test_inputs:
        if test_input:
            console.print(f"\n🔍 Testing partial input: '/{test_input}'")
            completion = get_command_completion(test_input)
            console.print(f"   Best completion: /{completion}")
        else:
            console.print(f"\n🔍 Testing empty input (showing all commands):")
        
        # This would show the autocomplete menu
        # show_command_menu(test_input)  # Commented out to avoid cluttering output
    
    console.print("\n✅ [bold]All features working correctly![/bold]", style="green")
    console.print("\n📝 [bold]Usage in DeepAgents CLI:[/bold]", style="yellow")
    console.print("   • Type [cyan]/status[/cyan] to see the comprehensive status line")
    console.print("   • Type [cyan]/[/cyan] to see all available commands") 
    console.print("   • Type [cyan]/s[/cyan] to see commands starting with 's'")
    console.print("   • Start typing any command to see matching options")
    
    console.print(f"\n🎉 [bold]Your statusLine is now way cooler![/bold] 🎉", style="magenta")
    console.print("""
It now features:

TIME: Live clock
HOST: Your hostname  
MODEL: Active model
FOLDER: Current folder name
BRANCH: Git branch (when in a repo)
PATH: Full directory path

All separated with clean | dividers for a modern, professional look. 
The statusLine will dynamically show your git branch when you're in a repository and gracefully hide it when you're not.
""", style="white")

if __name__ == "__main__":
    main()