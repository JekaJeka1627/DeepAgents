#!/usr/bin/env python3
"""
Simple launcher that uses the virtual environment Python directly
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run DeepAgents using the venv Python."""
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "bin" / "python3"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        print(f"Expected: {venv_python}")
        print("Please ensure the venv is set up correctly.")
        return 1
    
    # Run the CLI using venv Python
    cmd = [str(venv_python), "-m", "deepagents_cli.claude_main"] + sys.argv[1:]
    
    try:
        print("🚀 Starting DeepAgents with Claude Code-style UI...")
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())