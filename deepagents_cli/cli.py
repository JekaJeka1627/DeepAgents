"""
DeepAgents CLI entrypoint.

Starts a conversational loop using deepagents with preferred model selection
(OpenAI > Claude > Gemini > OpenRouter). Type :help for commands.
"""
from __future__ import annotations

import sys
import argparse
import os
import re
from pathlib import Path
from typing import Any, List

from deepagents_cli.agent.factory import create_agent
from deepagents_cli.agent.tools import get_default_tools
from deepagents_cli.agent.logging import set_verbose, is_verbose
from deepagents_cli.agent.state import save_vfs, load_vfs
from deepagents_cli.agent.factory import get_last_selection
from deepagents_cli.agent import config as cfg
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from deepagents_cli.agent.tools import (
    fs_ls as _tool_fs_ls,
    fs_tree as _tool_fs_tree,
    fs_glob as _tool_fs_glob,
    list_pending_writes as _list_pending_writes,
    apply_pending_write as _apply_pending_write,
    clear_pending_write as _clear_pending_write,
)
try:
    # Optional: load environment variables from .env in project root
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


def _safe_str(obj: Any) -> str:
    """Best-effort extraction of assistant text from varied result shapes."""
    try:
        if obj is None:
            return ""
        if isinstance(obj, str):
            return obj
        # LangChain message-like object
        if hasattr(obj, "content"):
            try:
                return str(getattr(obj, "content"))
            except Exception:
                pass
        # Mapping outputs
        if isinstance(obj, dict):
            # Common keys
            for k in ("output_text", "text", "output"):
                if k in obj and isinstance(obj[k], str):
                    return obj[k]
            # DeepAgents often returns {"messages": [BaseMessage,...]}
            msgs = obj.get("messages")
            if isinstance(msgs, list) and msgs:
                for m in reversed(msgs):
                    if hasattr(m, "content"):
                        try:
                            return str(getattr(m, "content"))
                        except Exception:
                            pass
                    if isinstance(m, dict) and "content" in m:
                        return str(m["content"])  # type: ignore
            # Fallback to stringifying
            return str(obj)
        # Iterables (take last item if message-like)
        if isinstance(obj, list) and obj:
            for m in reversed(obj):
                if hasattr(m, "content"):
                    return str(getattr(m, "content"))
        return str(obj)
    except Exception:
        return "[No printable response]"


def print_help() -> None:
    console.print(Panel.fit(
        """
Commands:
  :help           Show this help (note the leading colon)
  :tools          List available tools
  :model          Show provider/model selection and env-based priority
  :model!         Force model initialization, then show selection
  :log on|off     Toggle trace logging for tool calls
  :debug on|off   Toggle raw result debug printing
  :stream on|off  Toggle streaming output (if supported)
  :cd PATH        Change sandbox root to PATH
  :ls [PATH]      List files (relative to root). Use PATH or '.'
  :tree [PATH]    Show directory tree (default '.')
  :glob PATTERN   Glob under root, e.g. **/*.py
  :proposals      Show proposed edits awaiting acceptance
  :accept ID|all  Apply a proposal (requires --allow-write)
  :clear  ID|all  Clear one proposal or all
  (Tip) Paste an absolute path like C:\\Users\\jesse\\MyProj to switch root
  :save PATH      Save virtual FS to JSON file at PATH
  :load PATH      Load virtual FS JSON file from PATH
  :quit / :exit   Quit the CLI

Just type to chat with the agent.
        """.strip(), title="Help", border_style="cyan"))


def show_tools() -> None:
    tools = get_default_tools()
    names = [getattr(t, "__name__", str(t)) for t in tools]
    print("Tools:")
    for n in names:
        print(f"  - {n}")


def show_model_hint() -> None:
    actual = get_last_selection()
    console.print(Panel.fit(
        (
            "Model selection is priority-based: OpenAI > Claude > Gemini > OpenRouter.\n"
            f"Current selection: {actual}\n"
            "Set keys OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY / OPENROUTER_API_KEY.\n"
            "Override with OPENAI_MODEL / ANTHROPIC_MODEL / GEMINI_MODEL / OPENROUTER_MODEL."
        ),
        title="Model",
        border_style="green",
    ))


console = Console()
_DEBUG = False
_STREAM = False


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="deepagents", add_help=True)
    parser.add_argument("--cwd", type=str, default=None, help="Set working directory/sandbox root")
    parser.add_argument("--allow-write", action="store_true", help="Allow host filesystem writes (default off)")
    parser.add_argument("--auto-apply", action="store_true", help="Auto-apply write proposals (requires --allow-write)")
    args = parser.parse_args(argv)

    # Configure sandbox root and write policy
    if args.cwd:
        try:
            cfg.set_fs_root(args.cwd)
        except Exception as e:
            print(f"[config] failed to set --cwd: {e}")
            return 1
    else:
        # default root is current working directory
        pass
    cfg.set_allow_fs_write(bool(args.allow_write))
    cfg.set_allow_auto_apply(bool(args.auto_apply))

    console.print("🧠 [bold]DeepAgents CLI[/bold] — type [cyan]:help[/cyan] for commands.\n")
    console.print(f"[dim][sandbox][/dim] root: [bold]{cfg.FS_ROOT}[/bold]")
    console.print(f"[dim][sandbox][/dim] write-enabled: [bold]{cfg.ALLOW_FS_WRITE}[/bold]")
    console.print(f"[dim][sandbox][/dim] auto-apply: [bold]{cfg.ALLOW_AUTO_APPLY}[/bold]")
    
    try:
        agent = create_agent()
    except Exception as e:
        console.print(Panel.fit(str(e), title="Failed to create agent", border_style="red"))
        return 1

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user:
            continue
        # Quick UX: if the user enters a bare absolute path, treat it as :cd
        # Support Windows paths like C:\foo\bar and quoted variants
        bare_path = user.strip().strip('"')
        if re.match(r"^[A-Za-z]:\\\\", bare_path):
            try:
                cfg.set_fs_root(bare_path)
                console.print(f"[sandbox] root: [bold]{cfg.FS_ROOT}[/bold]")
                continue
            except Exception as e:
                console.print(Panel.fit(str(e), title=":cd error", border_style="red"))

        if user.startswith(":debug"):
            parts = user.split()
            if len(parts) == 2 and parts[1].lower() in ("on", "off"):
                globals()["_DEBUG"] = parts[1].lower() == "on"
                console.print(f"[debug] {'on' if _DEBUG else 'off'}")
            else:
                console.print("Usage: :debug on|off")
            continue
        if user.startswith(":stream"):
            parts = user.split()
            if len(parts) == 2 and parts[1].lower() in ("on", "off"):
                globals()["_STREAM"] = parts[1].lower() == "on"
                console.print(f"[stream] {'on' if _STREAM else 'off'} (note: provider support may vary)")
            else:
                console.print("Usage: :stream on|off")
            continue
        if user.startswith(":cd ") or user == ":cd":
            parts = user.split(maxsplit=1)
            if len(parts) == 2 and parts[1].strip():
                try:
                    cfg.set_fs_root(parts[1].strip())
                    console.print(f"[sandbox] root: [bold]{cfg.FS_ROOT}[/bold]")
                except Exception as e:
                    console.print(Panel.fit(str(e), title=":cd error", border_style="red"))
            else:
                console.print("Usage: :cd PATH")
            continue
        if user.startswith(":ls"):
            parts = user.split(maxsplit=1)
            path = parts[1] if len(parts) == 2 else "."
            try:
                listing = _tool_fs_ls(path)
                console.print(Panel.fit(listing if listing else "(empty)", title=f"ls {path}", border_style="blue"))
            except Exception as e:
                console.print(Panel.fit(str(e), title=":ls error", border_style="red"))
            continue
        if user.startswith(":tree"):
            parts = user.split(maxsplit=1)
            path = parts[1] if len(parts) == 2 else "."
            try:
                tree = _tool_fs_tree(path)
                console.print(Panel.fit(tree, title=f"tree {path}", border_style="blue"))
            except Exception as e:
                console.print(Panel.fit(str(e), title=":tree error", border_style="red"))
            continue
        if user.startswith(":glob"):
            parts = user.split(maxsplit=1)
            if len(parts) != 2:
                console.print("Usage: :glob PATTERN")
            else:
                try:
                    matches = _tool_fs_glob(parts[1])
                    console.print(Panel.fit(matches, title=f"glob {parts[1]}", border_style="blue"))
                except Exception as e:
                    console.print(Panel.fit(str(e), title=":glob error", border_style="red"))
            continue
        if user == ":proposals":
            proposals = _list_pending_writes()
            if not proposals:
                console.print("(no pending proposals)")
            else:
                for p in proposals:
                    title = f"proposal #{p['id']} — {p['path']}"
                    diff = p.get('diff') or '(no changes)'
                    console.print(Panel(diff, title=title, border_style="yellow"))
            continue
        if user.startswith(":accept"):
            parts = user.split(maxsplit=1)
            if len(parts) != 2:
                console.print("Usage: :accept ID|all")
            else:
                target = parts[1].strip().lower()
                try:
                    if target == "all":
                        applied = 0
                        while True:
                            proposals = _list_pending_writes()
                            if not proposals:
                                break
                            _apply_pending_write(0)
                            _clear_pending_write(0)
                            applied += 1
                        console.print(f"applied {applied} proposals")
                    else:
                        idx = int(target)
                        msg = _apply_pending_write(idx)
                        console.print(msg)
                        _clear_pending_write(idx)
                except Exception as e:
                    console.print(Panel.fit(str(e), title=":accept error", border_style="red"))
            continue
        if user.startswith(":clear"):
            parts = user.split(maxsplit=1)
            if len(parts) != 2:
                console.print("Usage: :clear ID|all")
            else:
                target = parts[1].strip().lower()
                try:
                    if target == "all":
                        console.print(_clear_pending_write(None))
                    else:
                        idx = int(target)
                        console.print(_clear_pending_write(idx))
                except Exception as e:
                    console.print(Panel.fit(str(e), title=":clear error", border_style="red"))
            continue

        if user in (":quit", ":exit"):
            break
        if user == ":help":
            print_help()
            continue
        if user == ":tools":
            show_tools()
            continue
        if user == ":model":
            show_model_hint()
            continue
        if user == ":model!":
            # Force a lightweight initialization by invoking a no-op
            try:
                _ = agent.invoke({"messages": [{"role": "user", "content": "ping"}]})
            except Exception:
                pass
            show_model_hint()
            continue
        if user.startswith(":log"):
            parts = user.split()
            if len(parts) == 2 and parts[1].lower() in ("on", "off"):
                set_verbose(parts[1].lower() == "on")
                state = "on" if is_verbose() else "off"
                print(f"[log] verbosity {state}")
            else:
                print("Usage: :log on|off")
            continue
        if user.startswith(":save"):
            parts = user.split(maxsplit=1)
            if len(parts) == 2 and parts[1]:
                path = parts[1]
                try:
                    msg = save_vfs(path)
                    print(msg)
                except Exception as e:
                    print(f"[vfs save error] {e}")
            else:
                print("Usage: :save PATH")
            continue
        if user.startswith(":load"):
            parts = user.split(maxsplit=1)
            if len(parts) == 2 and parts[1]:
                path = parts[1]
                try:
                    msg = load_vfs(path)
                    print(msg)
                except Exception as e:
                    print(f"[vfs load error] {e}")
            else:
                print("Usage: :load PATH")
            continue

        try:
            result = agent.invoke({"messages": [{"role": "user", "content": user}]})
            text = _safe_str(result)
            if text.strip():
                console.print(Markdown(text))
            else:
                console.print("[dim](no text output)[/dim]")
            if _DEBUG:
                console.print(Panel.fit(Pretty(result), title="raw result", border_style="magenta"))
        except Exception as e:
            console.print(Panel.fit(str(e), title="Error invoking agent", border_style="red"))

    console.print("Goodbye.")
    return 0


def console_main() -> None:
    """Entry point for console_scripts."""
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    console_main()
