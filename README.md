# DeepAgents CLI

A simple, extensible conversational CLI built on top of `deepagents`, with priority model selection:

1) OpenAI  2) Claude (Anthropic)  3) Gemini  4) OpenRouter (fallback)

## Features (MVP)
- Model-agnostic via env-based selection
- Minimal tool registry with examples
- Claude Code–style chat loop (`python -m deepagents_cli.cli`)
- Easy to extend with real tools, sub-agents, and state persistence

## Install
```bash
# (Recommended) create a virtualenv first
pip install -r requirements.txt
```

## Configure Models
Set one or more provider API keys. The CLI will pick the first available in priority order.

- OpenAI: `OPENAI_API_KEY` (optional `OPENAI_MODEL`, default `gpt-4o-mini`)
- Claude: `ANTHROPIC_API_KEY` (optional `ANTHROPIC_MODEL`, default `claude-3-5-sonnet-20240620`)
- Gemini: `GOOGLE_API_KEY` (optional `GEMINI_MODEL`, default `gemini-1.5-pro-latest`)
- OpenRouter: `OPENROUTER_API_KEY` (optional `OPENROUTER_MODEL`, default `openrouter/auto`; optional `OPENROUTER_BASE_URL`)

You can put these in a `.env` file and use `python-dotenv` in your shell or IDE if desired.

## Run
```bash
python -m deepagents_cli.cli
```

Commands inside the CLI:
- `:help` — show help
- `:tools` — list available tools
- `:model` — show model selection hints
- `:exit` or `:quit` — leave the CLI

## Project Layout
```
DeepAgents/
  deepagents_cli/
    __init__.py
    cli.py
    agent/
      __init__.py
      factory.py
      prompts.py
      tools.py
  requirements.txt
  README.md
```

## Next Steps
- Add real tools (web search, GitHub, filesystem persistence)
- Add sub-agents with dedicated prompts and toolsets
- Add logging verbosity and planning/tool traces
- Optional: Streamed token output for long generations

## Notes
This project scaffolds a Claude Code–like UX while remaining provider-agnostic and easily extensible.
