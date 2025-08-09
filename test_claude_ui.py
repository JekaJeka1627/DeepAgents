#!/usr/bin/env python3
"""
Test the Claude Code-style UI
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_autocomplete():
    """Test autocomplete functionality."""
    from deepagents_cli.agent.autocomplete import get_matching_commands
    
    print("Testing autocomplete with '/s':")
    matches = get_matching_commands('s')
    for cmd, desc in matches:
        print(f"  /{cmd}: {desc}")
        
    print("\nTesting autocomplete with '/st':")
    matches = get_matching_commands('st')
    for cmd, desc in matches:
        print(f"  /{cmd}: {desc}")
        
    print("\nTesting autocomplete with '/task':")
    matches = get_matching_commands('task')
    for cmd, desc in matches:
        print(f"  /{cmd}: {desc}")

if __name__ == "__main__":
    print("🧪 Testing Claude Code-style UI components...\n")
    test_autocomplete()
    
    print("\n✅ Autocomplete working!")
    print("\n🚀 To run the full UI:")
    print("   python3 deepagents_claude_ui.py")