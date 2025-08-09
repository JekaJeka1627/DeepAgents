#!/usr/bin/env python3
"""
Launcher for DeepAgents with Claude Code-style UI
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the live CLI
from deepagents_cli.live_cli import main

if __name__ == "__main__":
    print("🚀 Starting DeepAgents with Claude Code-style UI...")
    sys.exit(main(sys.argv[1:]))