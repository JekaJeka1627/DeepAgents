"""
Agent factory: creates a Deep Agent with preferred model selection
(OpenAI > Claude > Gemini > OpenRouter), tools, and system prompt.
"""
from __future__ import annotations

import os
from typing import Callable, List, Optional

from deepagents import create_deep_agent  # type: ignore

from .prompts import DEFAULT_SYSTEM_PROMPT
from .tools import get_default_tools

# LangChain chat model imports are optional; we gate by env
try:
    from langchain_openai import ChatOpenAI  # type: ignore
except Exception:  # pragma: no cover
    ChatOpenAI = None  # type: ignore

try:
    from langchain_anthropic import ChatAnthropic  # type: ignore
except Exception:  # pragma: no cover
    ChatAnthropic = None  # type: ignore

try:
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
except Exception:  # pragma: no cover
    ChatGoogleGenerativeAI = None  # type: ignore

try:
    from langchain_community.chat_models import ChatOpenAI as ChatOpenRouter  # type: ignore
except Exception:  # pragma: no cover
    ChatOpenRouter = None  # type: ignore


# Track last selection for debugging
_LAST_SELECTION: str = ""

def get_last_selection() -> str:
    return _LAST_SELECTION or "(none)"

def _select_llm(model_override: Optional[str] = None, temperature: float = 0.1):
    """
    Select an LLM in priority order using available API keys.
    Priority: OpenAI > Claude (Anthropic) > Gemini > OpenRouter.
    Optionally allow a direct model name override for OpenAI/Anthropic/Gemini.
    """
    # Optional explicit provider override
    global _LAST_SELECTION
    provider = (os.getenv("DEEPAGENTS_PROVIDER") or "").strip().lower()

    # Helper closures to construct each provider
    def _mk_openai():
        if not (os.getenv("OPENAI_API_KEY") and ChatOpenAI):
            return None
        model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        _LAST_SELECTION = f"openai:{model}"
        return ChatOpenAI(model=model, temperature=temperature)

    def _mk_anthropic():
        if not (os.getenv("ANTHROPIC_API_KEY") and ChatAnthropic):
            return None
        model = model_override or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
        _LAST_SELECTION = f"anthropic:{model}"
        return ChatAnthropic(model=model, temperature=temperature)

    def _mk_gemini():
        if not (os.getenv("GOOGLE_API_KEY") and ChatGoogleGenerativeAI):
            return None
        model = model_override or os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
        _LAST_SELECTION = f"gemini:{model}"
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)

    def _mk_openrouter():
        if not (os.getenv("OPENROUTER_API_KEY") and ChatOpenRouter):
            return None
        model = model_override or os.getenv("OPENROUTER_MODEL", "openrouter/auto")
        _LAST_SELECTION = f"openrouter:{model}"
        return ChatOpenRouter(
            model=model,
            temperature=temperature,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        )

    # If provider forced, honor it
    if provider in {"openai", "anthropic", "gemini", "openrouter"}:
        fn_map = {
            "openai": _mk_openai,
            "anthropic": _mk_anthropic,
            "gemini": _mk_gemini,
            "openrouter": _mk_openrouter,
        }
        llm = fn_map[provider]()
        if llm is not None:
            return llm
        # fall through to priority if forced provider unavailable

    # OpenAI (priority 1)
    if os.getenv("OPENAI_API_KEY") and ChatOpenAI:
        llm = _mk_openai()
        if llm is not None:
            return llm

    # Anthropic (Claude) (priority 2)
    if os.getenv("ANTHROPIC_API_KEY") and ChatAnthropic:
        llm = _mk_anthropic()
        if llm is not None:
            return llm

    # Google Gemini (priority 3)
    if os.getenv("GOOGLE_API_KEY") and ChatGoogleGenerativeAI:
        llm = _mk_gemini()
        if llm is not None:
            return llm

    # OpenRouter fallback (priority 4)
    if os.getenv("OPENROUTER_API_KEY") and ChatOpenRouter:
        llm = _mk_openrouter()
        if llm is not None:
            return llm

    _LAST_SELECTION = "(no provider)"
    raise RuntimeError(
        "No supported LLM configured. Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, "
        "GOOGLE_API_KEY, or OPENROUTER_API_KEY."
    )


def create_agent(
    tools: Optional[List[Callable]] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.1,
    model_override: Optional[str] = None,
):
    """
    Create and return a deep agent with selected LLM and provided tools/prompt.
    """
    # Try to pick an LLM, but tolerate absence to match deepagents defaults
    llm = None
    try:
        llm = _select_llm(model_override=model_override, temperature=temperature)
    except Exception:
        llm = None
    toolset = tools if tools is not None else get_default_tools()
    prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    # Try multiple signatures for compatibility across deepagents versions
    # Detected signature: (tools, instructions, model=None, subagents=None, state_schema=None)
    if llm is not None:
        # 1) tools, prompt, model=... (kw)
        try:
            return create_deep_agent(toolset, prompt, model=llm)
        except TypeError:
            pass
        # 2) tools, prompt, model (positional)
        try:
            return create_deep_agent(toolset, prompt, llm)
        except TypeError:
            pass
    # 3) tools, prompt (let deepagents choose defaults)
    return create_deep_agent(toolset, prompt)
