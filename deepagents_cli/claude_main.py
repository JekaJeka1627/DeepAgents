"""
Direct entry point for Claude Code-style DeepAgents CLI
Can be run with: python -m deepagents_cli.claude_main
"""
import sys
from .claude_style_cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))