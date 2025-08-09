#!/usr/bin/env python3
"""
DeepAgents with Claude Code-style UI

Usage:
  python3 deepagents_claude_ui.py
  python3 deepagents_claude_ui.py --allow-write
  python3 deepagents_claude_ui.py --cwd /path/to/project
"""
import sys
import os
from pathlib import Path

# Add the project root and venv to Python path
project_root = Path(__file__).parent
venv_site_packages = project_root / "venv" / "lib" / "python3.12" / "site-packages"

# Add both project root and venv site-packages to path
sys.path.insert(0, str(project_root))
if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))

def main():
    """Run DeepAgents with Claude Code UI."""
    print("🚀 Starting DeepAgents with Claude Code-style UI...")
    
    try:
        # Check if we're in the right directory
        deepagents_cli_path = project_root / "deepagents_cli"
        if not deepagents_cli_path.exists():
            print(f"❌ DeepAgents CLI directory not found at: {deepagents_cli_path}")
            print("Make sure you're in the DeepAgents project directory.")
            return 1
            
        from deepagents_cli.claude_style_cli import main as cli_main
        return cli_main(sys.argv[1:])
    except ImportError as e:
        print(f"❌ Failed to import DeepAgents CLI: {e}")
        print(f"Current directory: {Path.cwd()}")
        print(f"Project root: {project_root}")
        print("Try running from the DeepAgents project directory.")
        return 1
    except Exception as e:
        print(f"❌ Error starting DeepAgents: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())