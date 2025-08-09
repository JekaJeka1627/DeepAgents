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
from datetime import datetime

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
from deepagents_cli.agent.claude_formatter import ClaudeFormatter
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
    # Try multiple locations for .env file
    env_paths = [
        Path.cwd() / '.env',  # Current working directory
        Path(__file__).parent.parent / '.env',  # Project root
        Path.home() / '.env',  # Home directory fallback
    ]
    loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            loaded = True
            # Debug: print which .env file was loaded (uncomment for debugging)
            # print(f"DEBUG: Loaded .env from {env_path}")
            break
    if not loaded:
        load_dotenv()  # Fallback to default search
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
  :safety         Show safety settings and conversation stats
  :log on|off     Toggle trace logging for tool calls
  :debug on|off   Toggle raw result debug printing
  :stream on|off  Toggle streaming output (if supported)
  :cd PATH        Change sandbox root to PATH

Claude Code-Style Commands:
  /status                   Show comprehensive status line with time, model, git info
  /read FILE [start:end]     Read file with syntax highlighting
  /write FILE               Write content to file with backup
  /edit FILE old new        Search and replace in file
  /ls [PATH] [pattern]      List files with rich formatting
  /grep PATTERN [PATH]      Search files with context
  /bash COMMAND             Execute shell command safely
  /task add DESCRIPTION     Add task to current list
  /task done ID             Mark task as completed  
  /task list                Show all tasks
  /task clear               Clear completed tasks
  /search QUERY             Web search (like Claude Code)
  /fetch URL                Fetch web content

Memory Commands:
  /memory history [N]       Show recent conversation history
  /memory projects          List remembered projects
  /memory note TEXT         Add note about current project
  /memory forget PROJECT    Clear memory for project

Specialized Agent Commands:
  /agent list               Show all available specialized agents
  /agent help               Detailed help for agent commands
  /agent stats              Show agent usage statistics
  /agent auto QUESTION      Auto-route question to best agent
  /agent AGENT_ID QUESTION  Consult specific agent directly

Smart Workflow Commands:
  /workflow list            Show all available smart workflows
  /workflow help            Detailed help for workflow commands
  /workflow history         Show workflow execution history
  /workflow suggest TEXT    Get workflow recommendations
  /workflow ID [params]     Execute workflow with parameters

Model Management Commands:
  /model list               Show GPT-5 variants and pricing
  /model set MODEL          Switch to specific model (gpt-5, gpt-5-mini, etc)
  /model benchmark          Show performance comparisons
  /model costs              Show cost analysis
  /model features           Show feature comparisons
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
formatter = ClaudeFormatter()
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

    console.print("🧠 [bold]DeepAgents CLI[/bold] — type [cyan]:help[/cyan] for commands.")
    console.print("[dim]([yellow]Your text[/yellow] is yellow, [white]DeepAgents responses[/white] are white)[/dim]\n")
    console.print(f"[dim][sandbox][/dim] root: [bold]{cfg.FS_ROOT}[/bold]")
    console.print(f"[dim][sandbox][/dim] write-enabled: [bold]{cfg.ALLOW_FS_WRITE}[/bold]")
    console.print(f"[dim][sandbox][/dim] auto-apply: [bold]{cfg.ALLOW_AUTO_APPLY}[/bold]")
    
    # Show initial status line
    try:
        from deepagents_cli.agent.status_line import get_status_line
        status = get_status_line()
        console.print(f"\n[dim][status][/dim] {status}")
    except Exception:
        pass  # Status line is optional
    
    try:
        agent = create_agent()
    except Exception as e:
        console.print(Panel.fit(str(e), title="Failed to create agent", border_style="red"))
        return 1

    while True:
        try:
            # Display user prompt in yellow and get input
            console.print("[yellow]You: [/yellow]", end="")
            user = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user:
            continue
        
        # Add some spacing for better visual separation
        console.print()
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
        if user == ":safety":
            from deepagents_cli.agent.safety import safety
            turns = len(safety.turn_history)
            console.print(Panel.fit(
                f"Safety Status:\n"
                f"• Turns in last minute: {turns}/{safety.max_turns_per_minute}\n"
                f"• Max tool calls per turn: {safety.max_tool_calls_per_turn}\n"
                f"• Response length limit: {safety.max_response_length} chars\n"
                f"• Timeout protection: 30 seconds\n\n"
                f"💡 These limits prevent runaway conversations and ensure stability.",
                title="Safety Controls", border_style="green"
            ))
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

        # ===============================
        # CLAUDE CODE-STYLE COMMANDS
        # ===============================
        
        if user.startswith('/'):
            from deepagents_cli.agent.claude_commands import claude_commands
            parts = user[1:].split(maxsplit=2)  # Remove leading /
            
            # Handle autocomplete for partial commands
            if len(parts) == 1 and not user.endswith(' '):
                command_part = parts[0] if parts else ""
                from deepagents_cli.agent.autocomplete import get_matching_commands
                
                # Show autocomplete if it's a partial command
                matches = get_matching_commands(command_part)
                if len(matches) > 1 or (len(matches) == 1 and matches[0][0] != command_part):
                    console.print()
                    console.print("╭─ Available Commands ─────────────────────────────────────╮")
                    for cmd, desc in matches[:8]:  # Show max 8 options
                        cmd_display = f"/{cmd}"
                        console.print(f"│ [green]{cmd_display:<20}[/green] {desc:<35} │")
                    console.print("╰──────────────────────────────────────────────────────────╯")
                    continue
            
            if not parts:
                console.print("❌ Empty command. Type :help for available commands.")
                continue
                
            cmd = parts[0].lower()
            
            # Status line command
            if cmd == 'status':
                from deepagents_cli.agent.status_line import get_status_line
                status = get_status_line()
                console.print(Panel.fit(
                    status,
                    title="🚀 DeepAgents Status", 
                    border_style="cyan"
                ))
                continue
            
            # File operations
            elif cmd == 'read' and len(parts) >= 2:
                file_path = parts[1]
                line_range = parts[2] if len(parts) > 2 else None
                
                if line_range and ':' in line_range:
                    try:
                        start, end = map(int, line_range.split(':'))
                        result = claude_commands.read_file(file_path, start, end)
                    except ValueError:
                        result = claude_commands.read_file(file_path)
                else:
                    result = claude_commands.read_file(file_path)
                    
                if not result.startswith('✅'):
                    console.print(result)
                continue
                
            elif cmd == 'write' and len(parts) >= 2:
                file_path = parts[1]
                console.print(f"📝 Enter content for {file_path} (end with Ctrl+D on Unix or Ctrl+Z on Windows):")
                try:
                    import sys
                    content_lines = []
                    while True:
                        try:
                            line = input()
                            content_lines.append(line)
                        except EOFError:
                            break
                    content = '\n'.join(content_lines)
                    result = claude_commands.write_file(file_path, content)
                    console.print(result)
                except KeyboardInterrupt:
                    console.print("\n❌ Write operation cancelled")
                continue
                
            elif cmd == 'edit' and len(parts) >= 4:
                file_path, old_text, new_text = parts[1], parts[2], parts[3]
                result = claude_commands.edit_file(file_path, old_text, new_text)
                console.print(result)
                continue
                
            elif cmd == 'ls':
                directory = parts[1] if len(parts) > 1 else "."
                pattern = parts[2] if len(parts) > 2 else "*"
                result = claude_commands.list_files(directory, pattern)
                if not result.startswith('✅'):
                    console.print(result)
                continue
                
            elif cmd == 'grep' and len(parts) >= 2:
                pattern = parts[1]
                directory = parts[2] if len(parts) > 2 else "."
                result = claude_commands.grep_search(pattern, directory)
                if not result.startswith('✅'):
                    console.print(result)
                continue
                
            elif cmd == 'bash' and len(parts) >= 2:
                command = ' '.join(parts[1:])
                result = claude_commands.run_bash(command)
                if not result.startswith('✅'):
                    console.print(result)
                continue
                
            # Task management
            elif cmd == 'task' and len(parts) >= 2:
                subcmd = parts[1].lower()
                
                if subcmd == 'add' and len(parts) >= 3:
                    description = ' '.join(parts[2:])
                    result = claude_commands.add_task(description)
                    console.print(result)
                    
                elif subcmd == 'done' and len(parts) >= 3:
                    try:
                        task_id = int(parts[2])
                        result = claude_commands.complete_task(task_id)
                        console.print(result)
                    except ValueError:
                        console.print("❌ Invalid task ID. Use /task list to see task numbers.")
                        
                elif subcmd == 'list':
                    claude_commands.list_tasks()
                    
                elif subcmd == 'clear':
                    result = claude_commands.clear_completed_tasks()
                    console.print(result)
                    
                else:
                    console.print("❌ Usage: /task [add|done|list|clear] [args...]")
                continue
                
            # Web operations
            elif cmd == 'search' and len(parts) >= 2:
                query = ' '.join(parts[1:])
                result = claude_commands.web_search(query)
                if not result.startswith('✅'):
                    console.print(result)
                continue
                
            elif cmd == 'fetch' and len(parts) >= 2:
                url = parts[1]
                result = claude_commands.web_fetch(url)
                if not result.startswith('✅'):
                    console.print(result)
                continue
            
            # Memory operations
            elif cmd == 'memory' and len(parts) >= 2:
                subcmd = parts[1].lower()
                
                if subcmd == 'history':
                    limit = int(parts[2]) if len(parts) > 2 else 10
                    conversations = memory_system.get_conversation_history(limit=limit)
                    
                    if conversations:
                        console.print(Panel.fit(
                            f"📚 Recent Conversation History (Last {len(conversations)} turns)",
                            title="Memory", border_style="blue"
                        ))
                        
                        for i, conv in enumerate(reversed(conversations), 1):
                            time_str = conv.timestamp.strftime("%m/%d %H:%M")
                            console.print(f"\n**{i}. [{time_str}] User:** {conv.user_input[:100]}...")
                            console.print(f"**AI:** {conv.ai_response[:150]}...")
                    else:
                        console.print("📝 No conversation history found")
                        
                elif subcmd == 'projects':
                    projects = list(memory_system.project_contexts.values())
                    if projects:
                        console.print(Panel.fit(
                            f"📁 Remembered Projects ({len(projects)})",
                            title="Project Memory", border_style="green"
                        ))
                        
                        for project in sorted(projects, key=lambda p: p.last_accessed, reverse=True):
                            time_str = project.last_accessed.strftime("%m/%d %H:%M")
                            console.print(f"\n🔹 **{project.project_name}**")
                            console.print(f"   Path: {project.project_path}")
                            console.print(f"   Last accessed: {time_str}")
                            console.print(f"   Type: {project.project_type}")
                            if project.notes:
                                console.print(f"   Notes: {len(project.notes)} saved")
                    else:
                        console.print("📁 No projects in memory yet")
                        
                elif subcmd == 'note' and len(parts) >= 3:
                    note_text = ' '.join(parts[2:])
                    # Try to determine current project
                    current_project = None
                    cwd = Path.cwd()
                    
                    # Look for project in current working directory
                    for path, context in memory_system.project_contexts.items():
                        if str(cwd).startswith(path) or path.startswith(str(cwd)):
                            current_project = path
                            break
                    
                    if current_project:
                        memory_system.add_project_note(current_project, note_text)
                        project_name = memory_system.project_contexts[current_project].project_name
                        console.print(f"📝 Added note to {project_name}: {note_text}")
                    else:
                        console.print("❌ No current project detected. Navigate to a project folder first.")
                        
                elif subcmd == 'forget' and len(parts) >= 3:
                    project_identifier = ' '.join(parts[2:])
                    # Find matching project
                    matching_projects = []
                    for path, context in memory_system.project_contexts.items():
                        if (project_identifier.lower() in context.project_name.lower() or 
                            project_identifier in path):
                            matching_projects.append((path, context))
                    
                    if len(matching_projects) == 1:
                        path, context = matching_projects[0]
                        del memory_system.project_contexts[path]
                        memory_system._save_project_contexts()
                        console.print(f"🗑️ Forgot project: {context.project_name}")
                    elif len(matching_projects) > 1:
                        console.print("❌ Multiple projects match. Be more specific:")
                        for path, context in matching_projects:
                            console.print(f"  • {context.project_name} ({path})")
                    else:
                        console.print(f"❌ No project found matching: {project_identifier}")
                        
                else:
                    console.print("❌ Usage: /memory [history|projects|note|forget] [args...]")
                continue
            
            # Specialized agent operations
            elif cmd == 'agent' and len(parts) >= 2:
                from deepagents_cli.agent.agent_commands import (
                    list_specialized_agents, consult_specialized_agent, 
                    auto_route_question, show_routing_stats, get_agent_help
                )
                
                subcmd = parts[1].lower()
                
                if subcmd == 'list':
                    list_specialized_agents()
                    
                elif subcmd == 'help':
                    get_agent_help()
                    
                elif subcmd == 'stats':
                    show_routing_stats()
                    
                elif subcmd == 'auto' and len(parts) >= 3:
                    question = ' '.join(parts[2:])
                    context = {
                        "working_directory": os.getcwd(),
                        "project_path": project_path if 'project_path' in locals() else None
                    }
                    auto_route_question(question, context)
                    
                elif len(parts) >= 3:
                    # Direct agent consultation: /agent <agent_id> <question>
                    agent_id = subcmd
                    question = ' '.join(parts[2:])
                    context = {
                        "working_directory": os.getcwd(),
                        "project_path": project_path if 'project_path' in locals() else None
                    }
                    consult_specialized_agent(agent_id, question, context)
                    
                else:
                    console.print("❌ Usage: /agent [list|help|stats|auto <question>|<agent_id> <question>]")
                    console.print("💡 Try /agent help for detailed information")
                continue
            
            # Smart workflow operations
            elif cmd == 'workflow' and len(parts) >= 2:
                from deepagents_cli.agent.workflow_commands import (
                    list_workflows, execute_workflow, suggest_workflow, 
                    show_workflow_history, get_workflow_help
                )
                
                subcmd = parts[1].lower()
                
                if subcmd == 'list':
                    list_workflows()
                    
                elif subcmd == 'help':
                    get_workflow_help()
                    
                elif subcmd == 'history':
                    show_workflow_history()
                    
                elif subcmd == 'suggest' and len(parts) >= 3:
                    description = ' '.join(parts[2:])
                    suggest_workflow(description)
                    
                elif len(parts) >= 2:
                    # Execute workflow: /workflow <workflow_id> [params]
                    workflow_id = subcmd
                    params_str = ' '.join(parts[2:]) if len(parts) > 2 else ""
                    execute_workflow(workflow_id, params_str)
                    
                else:
                    console.print("❌ Usage: /workflow [list|help|history|suggest <description>|<workflow_id> [params]]")
                    console.print("💡 Try /workflow help for detailed information")
                continue
            
            # Model management operations
            elif cmd == 'model' and len(parts) >= 2:
                from deepagents_cli.agent.model_commands import (
                    show_gpt5_models, set_model, benchmark_models,
                    show_model_costs, show_model_features, get_model_help
                )
                
                subcmd = parts[1].lower()
                
                if subcmd == 'list':
                    show_gpt5_models()
                    
                elif subcmd == 'help':
                    get_model_help()
                    
                elif subcmd == 'benchmark':
                    benchmark_models()
                    
                elif subcmd == 'costs':
                    show_model_costs()
                    
                elif subcmd == 'features':
                    show_model_features()
                    
                elif subcmd == 'set' and len(parts) >= 3:
                    model_name = parts[2]
                    set_model(model_name)
                    
                else:
                    console.print("❌ Usage: /model [list|help|benchmark|costs|features|set <model>]")
                    console.print("💡 Try /model help for detailed information")
                continue
                
            else:
                console.print(f"❌ Unknown command: /{cmd}")
                console.print("💡 Type :help to see available commands")
                continue

        try:
            # Safety wrapper for conversations
            from deepagents_cli.agent.safety import safety, ContextLoader
            from deepagents_cli.agent.persistent_memory import memory_system
            
            # Reset safety counters for new turn
            safety.reset_turn()
            
            # Check rate limiting
            if not safety.check_rate_limit():
                console.print(Panel.fit(
                    "⚠️ Rate limit reached. Please wait a moment before continuing.",
                    title="Safety Control", border_style="yellow"
                ))
                continue
                
            # Smart folder analysis - if user provides a path, analyze it
            user_processed = user
            project_path = None
            
            if user.strip() and (user.strip().startswith('C:') or user.strip().startswith('/') or user.strip().startswith('./')):
                project_path = user.strip()
                folder_analysis = ContextLoader.analyze_folder(project_path)
                user_processed = f"Please analyze this folder: {project_path}\n\n{folder_analysis}\n\nWhat would you like to know about this project?"
                
                # Update project context in memory
                memory_system.update_project_context(
                    project_path, 
                    last_accessed=datetime.now(),
                    project_type="detected_from_analysis"
                )
            
            # Get memory context for this conversation
            memory_context = memory_system.get_contextual_memory_prompt(user_processed, project_path)
            
            # Add memory context to the user message if available
            if memory_context:
                user_processed = f"{memory_context}\n\n---\n\n**Current Request**: {user_processed}"
            
            # Invoke agent with cross-platform timeout protection
            import threading
            
            result = None
            exception = None
            
            def agent_call():
                nonlocal result, exception
                try:
                    result = agent.invoke({"messages": [{"role": "user", "content": user_processed}]})
                except Exception as e:
                    exception = e
            
            # Start agent call in thread with timeout
            thread = threading.Thread(target=agent_call)
            thread.daemon = True
            thread.start()
            thread.join(timeout=30)  # 30-second timeout
            
            if thread.is_alive():
                console.print(Panel.fit(
                    "⏰ Response timed out. The AI took too long to respond. Please try a simpler request.",
                    title="Timeout Error", border_style="red"
                ))
                continue
            
            if exception:
                raise exception
                
            # Record successful turn
            safety.record_turn()
            
            text = _safe_str(result)
            if text.strip():
                # Learn from user input (name, preferences, etc.)
                memory_system.extract_and_learn_user_info(user)
                
                # Store conversation in persistent memory
                memory_system.store_conversation_turn(
                    user_input=user,
                    ai_response=text,
                    context={
                        "working_directory": os.getcwd(),
                        "project_path": project_path,
                        "session_id": memory_system.current_session_id
                    }
                )
                
                # Add DeepAgents label and use enhanced formatter for better output
                console.print("\n[white]DeepAgents:[/white]")
                formatter.format_response(text, context={"user_input": user})
            else:
                console.print("[dim](no text output)[/dim]")
            if _DEBUG:
                console.print(Panel.fit(Pretty(result), title="raw result", border_style="magenta"))
            
        except KeyboardInterrupt:
            console.print("\n⚠️ Interrupted by user (Ctrl+C)")
            continue
        except Exception as e:
            console.print(Panel.fit(
                f"🚨 Error: {str(e)}\n\n💡 Try:\n• Asking a simpler question\n• Using :help for available commands\n• Restarting if problems persist",
                title="Error invoking agent", border_style="red"
            ))

    console.print("Goodbye.")
    return 0


def console_main() -> None:
    """Entry point for console_scripts."""
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    console_main()
