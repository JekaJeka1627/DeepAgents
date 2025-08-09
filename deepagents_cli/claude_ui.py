"""
DeepAgents CLI with exact Claude Code UI

Uses proper terminal control for:
- Persistent status bar at bottom
- Text entry above status bar
- Autocomplete menu between them
- No reprinting of UI elements
"""
import sys
import argparse
import signal
from pathlib import Path
from typing import Any

from deepagents_cli.agent.factory import create_agent
from deepagents_cli.agent import config as cfg
from deepagents_cli.terminal_ui import TerminalUI
from deepagents_cli.agent.autocomplete import handle_slash_input

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


def _safe_str(obj: Any) -> str:
    """Extract text from agent response."""
    try:
        if obj is None:
            return ""
        if isinstance(obj, str):
            return obj
        if hasattr(obj, "content"):
            return str(getattr(obj, "content"))
        if isinstance(obj, dict):
            for k in ("output_text", "text", "output"):
                if k in obj and isinstance(obj[k], str):
                    return obj[k]
            msgs = obj.get("messages")
            if isinstance(msgs, list) and msgs:
                for m in reversed(msgs):
                    if hasattr(m, "content"):
                        return str(getattr(m, "content"))
                    if isinstance(m, dict) and "content" in m:
                        return str(m["content"])
            return str(obj)
        if isinstance(obj, list) and obj:
            for m in reversed(obj):
                if hasattr(m, "content"):
                    return str(getattr(m, "content"))
        return str(obj)
    except Exception:
        return "[No printable response]"


def main(argv: list[str]) -> int:
    """Main CLI with Claude Code UI."""
    parser = argparse.ArgumentParser(prog="deepagents-claude", add_help=True)
    parser.add_argument("--cwd", type=str, default=None, help="Set working directory/sandbox root")
    parser.add_argument("--allow-write", action="store_true", help="Allow host filesystem writes")
    parser.add_argument("--auto-apply", action="store_true", help="Auto-apply write proposals")
    args = parser.parse_args(argv)

    # Configure sandbox
    if args.cwd:
        try:
            cfg.set_fs_root(args.cwd)
        except Exception as e:
            print(f"[config] failed to set --cwd: {e}")
            return 1
    cfg.set_allow_fs_write(bool(args.allow_write))
    cfg.set_allow_auto_apply(bool(args.auto_apply))

    # Create agent
    try:
        agent = create_agent()
    except Exception as e:
        print(f"Failed to create agent: {e}")
        return 1

    # Create UI
    ui = TerminalUI()
    
    # Add initial info
    ui.add_conversation_line(f"Sandbox root: {cfg.FS_ROOT}", "system")
    ui.add_conversation_line(f"Write enabled: {cfg.ALLOW_FS_WRITE}", "system")
    ui.add_conversation_line(f"Auto-apply: {cfg.ALLOW_AUTO_APPLY}", "system")
    ui.add_conversation_line("", "system")  # Empty line
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        ui.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start UI and handle input
        for user_input in ui.start():
            if not user_input.strip():
                continue
                
            # Handle commands
            if user_input in (":quit", ":exit"):
                break
            elif user_input == ":help":
                help_text = """Commands:
:help - Show this help
:quit/:exit - Quit
/status - Show status line
/[command] - Use slash commands
Just type to chat!"""
                ui.add_response(help_text)
                continue
            elif user_input.startswith('/status'):
                from deepagents_cli.agent.status_line import get_status_line
                status = get_status_line()
                ui.add_response(f"Status: {status}")
                continue
            elif user_input.startswith('/'):
                # Handle other slash commands
                ui.add_response(f"Command detected: {user_input}")
                ui.add_response("Full slash command support coming soon...")
                continue
            
            # Regular chat
            try:
                result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
                text = _safe_str(result)
                
                if text.strip():
                    ui.add_response(text)
                else:
                    ui.add_response("(no response)")
                    
            except Exception as e:
                ui.add_response(f"Error: {str(e)}")
                
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        ui.stop()
        
    return 0


def console_main() -> None:
    """Entry point."""
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    console_main()