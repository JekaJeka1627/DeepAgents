# 🚀 DeepAgents Claude Code UI

## Quick Start

### Windows PowerShell:
```powershell
venv\bin\python3 -m deepagents_cli.claude_main
```

### Linux/Mac:
```bash
venv/bin/python3 -m deepagents_cli.claude_main
```

## Features
- ✅ Status line with TIME, HOST, MODEL, FOLDER, BRANCH, PATH
- ✅ Autocomplete menu when typing `/` commands
- ✅ Claude Code-style interface
- ✅ No emojis (clean text only)

## Test Autocomplete
1. Start DeepAgents
2. Type `/s` and press Enter
3. Should show menu with `/status` and `/search` commands

## Options
```bash
# Allow file writes
venv/bin/python3 -m deepagents_cli.claude_main --allow-write

# Set working directory
venv/bin/python3 -m deepagents_cli.claude_main --cwd /your/project
```

## API Keys
Copy `.env.example` to `.env` and add your API keys:
- ANTHROPIC_API_KEY (for Claude)
- OPENAI_API_KEY (for GPT models)

## Next: Enhancement Implementation
Once autocomplete is confirmed working, we'll implement:
- Tab completion & command history
- Enhanced file operations with syntax highlighting
- Smart context awareness
- Workflow automation
- And much more!