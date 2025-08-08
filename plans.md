# DeepAgents CLI — Plan

## Vision
Build a Claude Code–class conversational CLI on top of deepagents that is model-agnostic, extensible (tools, sub-agents), and supports long-horizon workflows using planning and a virtual file system.

## Scope (MVP)
- Priority model selection: OpenAI > Claude > Gemini > OpenRouter (env-based)
- CLI chat loop with simple commands (:help, :tools, :model, :exit)
- Tool registry with safe example tools
- Ready to extend with sub-agents, persistence, and logging

## Milestones
1) Scaffold package + CLI entrypoint (DONE)
2) Agent factory with model selection (DONE)
3) Requirements + README (DONE)
4) Add optional persistence (virtual FS save/load)
5) Add logging/trace verbosity for planning + tools
6) Add real tools (web search, GitHub, filesystem)
7) Add sub-agents with dedicated prompts
8) Optional: streaming output, TUI/web UI

## Risks & Notes
- Provider SDK version drift: pinned via requirements; may revisit exact pins.
- Deepagents API evolution: keep factory decoupled to adapt quickly.
- Streaming support varies across providers; design an abstraction.
