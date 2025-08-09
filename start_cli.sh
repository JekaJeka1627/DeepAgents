#!/bin/bash
# DeepAgents CLI Startup Script

echo "🧠 Starting DeepAgents CLI..."
echo "💡 Tip: Type :help for available commands"
echo "🔧 Current directory: $(pwd)"
echo ""

# Set PATH to include pip packages
export PATH="$HOME/.local/bin:$PATH"

# Start the CLI
python3 -m deepagents_cli.cli "$@"