"""
Tool registry and simple default tools for the DeepAgents CLI.

These are simple, safe examples. Replace or extend with real tools later.
Includes a minimal virtual file system (VFS) toolset to persist artifacts.
"""
from __future__ import annotations

from typing import Callable, List
from pathlib import Path
from difflib import unified_diff
import subprocess
import fnmatch
from . import config

from .logging import log
from .state import vfs_ls, vfs_read, vfs_write

def echo(text: str) -> str:
    """Echo back the provided text (diagnostic example tool)."""
    log(f"tool:echo text_len={len(text)}")
    return text


def search_stub(query: str) -> str:
    """A placeholder search tool. Replace with a real web search later."""
    log(f"tool:search_stub query='{query}'")
    return f"[search_stub] Pretend we searched the web for: {query}"


def vfs_write_tool(name: str, content: str) -> str:
    """Write content to the virtual file system."""
    log(f"tool:vfs_write name='{name}' len={len(content)}")
    return vfs_write(name, content)


def vfs_read_tool(name: str) -> str:
    """Read content from the virtual file system."""
    log(f"tool:vfs_read name='{name}'")
    return vfs_read(name)


def vfs_ls_tool() -> str:
    """List items in the virtual file system."""
    log("tool:vfs_ls")
    return vfs_ls()


def _resolve_under_root(path: str) -> Path:
    """Resolve a path and ensure it is under the configured FS_ROOT."""
    root = config.FS_ROOT
    p = (root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if root not in p.parents and p != root:
        raise PermissionError(f"Path escapes sandbox root: {p} not under {root}")
    return p


def fs_read(path: str, max_kb: int = 64) -> str:
    """Read a text file from the host filesystem under the sandbox root.

    - Enforces sandbox under config.FS_ROOT
    - Requires config.ALLOW_FS_READ
    - Enforces max size (in KB)
    """
    log(f"tool:fs_read path='{path}' max_kb={max_kb}")
    if not config.ALLOW_FS_READ:
        raise PermissionError("Filesystem read is disabled")
    fp = _resolve_under_root(path)
    if not fp.is_file():
        raise FileNotFoundError(f"No such file: {fp}")
    max_bytes = max(1, int(max_kb)) * 1024
    data = fp.read_bytes()
    if len(data) > max_bytes:
        snippet = data[:max_bytes].decode(errors="replace")
        return f"[truncated {len(data)-max_bytes} bytes]\n" + snippet
    return data.decode(errors="replace")


def fs_ls(path: str = ".", recursive: bool = False, max_items: int = 200) -> str:
    """List files under a path within the sandbox root.

    - If recursive, walks subdirectories up to max_items.
    """
    log(f"tool:fs_ls path='{path}' recursive={recursive} max_items={max_items}")
    if not config.ALLOW_FS_READ:
        raise PermissionError("Filesystem read is disabled")
    base = _resolve_under_root(path)
    if not base.exists():
        raise FileNotFoundError(f"No such path: {base}")
    items = []
    if base.is_file():
        return f"FILE {base} ({base.stat().st_size} bytes)"
    if recursive:
        count = 0
        for p in base.rglob("*"):
            items.append(str(p.relative_to(config.FS_ROOT)))
            count += 1
            if count >= max_items:
                items.append(f"... [truncated at {max_items} items]")
                break
    else:
        for p in sorted(base.iterdir()):
            items.append(str(p.relative_to(config.FS_ROOT)))
    return "\n".join(items) if items else "(empty)"


def fs_glob(pattern: str) -> str:
    """Glob under sandbox root using a pattern relative to root.

    Example: "**/*.py"
    """
    log(f"tool:fs_glob pattern='{pattern}'")
    if not config.ALLOW_FS_READ:
        raise PermissionError("Filesystem read is disabled")
    root = config.FS_ROOT
    matches = list(root.glob(pattern))
    if not matches:
        return "(no matches)"
    lines = [str(p.relative_to(root)) for p in matches]
    return "\n".join(lines)


def fs_tree(path: str = ".", max_depth: int = 2, max_entries: int = 500) -> str:
    """Render a simple tree view from a path under the sandbox root."""
    log(f"tool:fs_tree path='{path}' max_depth={max_depth} max_entries={max_entries}")
    if not config.ALLOW_FS_READ:
        raise PermissionError("Filesystem read is disabled")
    start = _resolve_under_root(path)
    root = config.FS_ROOT
    if not start.exists():
        raise FileNotFoundError(f"No such path: {start}")

    lines: list[str] = []
    count = 0

    def walk(dir_path: Path, depth: int) -> None:
        nonlocal count
        if depth > max_depth:
            return
        prefix = "    " * depth
        entries = sorted(dir_path.iterdir())
        for entry in entries:
            rel = entry.relative_to(root)
            lines.append(f"{prefix}{rel}{'/' if entry.is_dir() else ''}")
            count += 1
            if count >= max_entries:
                lines.append("... [tree truncated]")
                return
            if entry.is_dir():
                walk(entry, depth + 1)

    if start.is_file():
        return str(start.relative_to(root))
    lines.append(str(start.relative_to(root)) + "/")
    walk(start, 0)
    return "\n".join(lines)


# --- Pending write queue (CLI-gated) ---
PENDING_WRITES: list[dict] = []


def _read_text(fp: Path) -> str:
    try:
        return fp.read_text(errors="replace") if fp.exists() else ""
    except Exception:
        return ""


def propose_write(path: str, content: str, create: bool = True) -> str:
    """Propose replacing the contents of a file. Does NOT write immediately.

    - Returns a unified diff preview and a proposal id.
    - The CLI must run :accept to apply.
    """
    log(f"tool:propose_write path='{path}' create={create}")
    target = _resolve_under_root(path)
    if target.exists() and not target.is_file():
        raise IsADirectoryError(f"Target is not a file: {target}")
    if not target.exists() and not create:
        raise FileNotFoundError(f"File does not exist: {target}")
    old = _read_text(target)
    new = content
    diff = "".join(
        unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=str(target),
            tofile=f"{target} (proposed)",
        )
    )
    proposal = {"path": str(target), "content": content, "diff": diff}
    # Auto-apply if policy allows
    if config.ALLOW_FS_WRITE and config.ALLOW_AUTO_APPLY:
        fp = Path(proposal["path"]) \
            if Path(proposal["path"]).is_absolute() else (config.FS_ROOT / proposal["path"]).resolve()
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(proposal["content"])
        return f"auto-applied to {fp}\n" + (diff or "(no changes)")
    # Otherwise queue proposal
    PENDING_WRITES.append(proposal)
    pid = len(PENDING_WRITES) - 1
    return f"proposal #{pid}\n" + (diff or "(no changes)")


def fs_set_root(path: str) -> str:
    """Set the sandbox root to a new path. Returns the resolved root.

    This enables natural language workflows where the agent changes working directory.
    """
    log(f"tool:fs_set_root path='{path}'")
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"No such path: {p}")
    if not p.is_dir():
        raise NotADirectoryError(f"Not a directory: {p}")
    config.set_fs_root(str(p))
    return str(config.FS_ROOT)


def list_pending_writes() -> list[dict]:
    """Return pending write proposals for the CLI to render."""
    return [{"id": i, **p} for i, p in enumerate(PENDING_WRITES)]


def apply_pending_write(idx: int) -> str:
    """Apply a pending write proposal by index. Requires write enabled."""
    if not config.ALLOW_FS_WRITE:
        raise PermissionError("Filesystem write is disabled; run with --allow-write")
    if idx < 0 or idx >= len(PENDING_WRITES):
        raise IndexError("Invalid proposal index")
    p = PENDING_WRITES[idx]
    fp = Path(p["path"])
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(p["content"])
    return f"applied proposal #{idx} to {fp}"


def clear_pending_write(idx: int | None = None) -> str:
    """Clear one proposal or all if idx is None."""
    global PENDING_WRITES
    if idx is None:
        n = len(PENDING_WRITES)
        PENDING_WRITES = []
        return f"cleared {n} proposals"
    if idx < 0 or idx >= len(PENDING_WRITES):
        raise IndexError("Invalid proposal index")
    PENDING_WRITES.pop(idx)
    return f"cleared proposal #{idx}"


# --- Repo-aware utilities ---

_DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv",
}


def _run_git(args: list[str], max_kb: int = 256) -> str:
    """Run a git command in the sandbox root and return output with size cap."""
    try:
        res = subprocess.run(
            ["git", *args],
            cwd=str(config.FS_ROOT),
            capture_output=True,
            text=True,
            shell=False,
        )
    except FileNotFoundError:
        return "git executable not found"
    out = res.stdout if res.returncode == 0 else res.stderr
    max_bytes = max_kb * 1024
    if len(out.encode(errors="ignore")) > max_bytes:
        return out[: max_bytes] + f"\n... [truncated output > {max_kb}KB]"
    return out or "(no output)"


def git_status() -> str:
    log("tool:git_status")
    return _run_git(["status", "--porcelain", "--branch"]) or "(clean)"


def git_diff(path: str | None = None, staged: bool = False, max_kb: int = 256) -> str:
    log(f"tool:git_diff path={path} staged={staged} max_kb={max_kb}")
    args = ["diff"]
    if staged:
        args.append("--staged")
    if path:
        args.append(path)
    return _run_git(args, max_kb=max_kb)


def git_log(n: int = 20) -> str:
    log(f"tool:git_log n={n}")
    return _run_git(["log", f"-n{int(n)}", "--oneline", "--decorate", "--graph"]) 


def git_add(paths: str) -> str:
    """Stage files. paths may be a space/comma/newline-separated list or a glob.

    Examples: "README.md" or "src/app.py tests/test_app.py" or "**/*.py"
    """
    log(f"tool:git_add paths='{paths}'")
    # Split on whitespace, comma, or newline
    raw = [p for chunk in paths.replace(",", " ").split() for p in [chunk.strip()] if p]
    if not raw:
        return "(no paths provided)"
    return _run_git(["add", *raw])


def git_add_all() -> str:
    log("tool:git_add_all")
    return _run_git(["add", "-A"]) or "staged all changes"


def git_commit(message: str, allow_empty: bool = False) -> str:
    """Commit staged changes with a message. Set allow_empty to True to allow empty commits."""
    log(f"tool:git_commit message='{message}' allow_empty={allow_empty}")
    if not message:
        return "commit message required"
    args = ["commit", "-m", message]
    if allow_empty:
        args.append("--allow-empty")
    return _run_git(args)


def git_restore(path: str | None = None, staged: bool = False, worktree: bool = True) -> str:
    """Restore file(s) to undo changes.

    - staged=True: unstage changes (git restore --staged)
    - worktree=True: restore working tree file content
    """
    log(f"tool:git_restore path={path} staged={staged} worktree={worktree}")
    args = ["restore"]
    if staged:
        args.append("--staged")
    if worktree:
        args.append("--worktree")
    if path:
        args.append(path)
    return _run_git(args)


def code_search(query: str, file_glob: str = "**/*", max_matches: int = 200, case_sensitive: bool = False,
                include_ext: str | None = None) -> str:
    """Search code under the sandbox root without external tools.

    - query: text to search
    - file_glob: pattern like **/*.py
    - include_ext: comma-separated list like "py,ts,js,md"
    """
    log(f"tool:code_search query='{query}' glob='{file_glob}' max_matches={max_matches} case={case_sensitive} ext={include_ext}")
    root = config.FS_ROOT
    if not query:
        return "(empty query)"
    patterns = [p.strip() for p in file_glob.split() if p.strip()] or ["**/*"]
    allow_ext: set[str] | None = None
    if include_ext:
        allow_ext = {"." + e.strip().lstrip(".") for e in include_ext.split(",") if e.strip()}
    matches: list[str] = []
    q = query if case_sensitive else query.lower()

    for path in root.rglob("*"):
        try:
            if path.is_dir():
                if path.name in _DEFAULT_IGNORE_DIRS:
                    continue
                else:
                    pass
            if not path.is_file():
                continue
            if allow_ext and path.suffix not in allow_ext:
                continue
            # glob filtering: require file to match at least one pattern relative to root
            rel = str(path.relative_to(root))
            if not any(fnmatch.fnmatch(rel, pat) for pat in patterns):
                continue
            # read smallish files only (cap at ~1MB)
            if path.stat().st_size > 1_000_000:
                continue
            text = path.read_text(errors="ignore")
            hay = text if case_sensitive else text.lower()
            if q in hay:
                # capture first line number occurrence
                line_no = 0
                for i, line in enumerate(text.splitlines(), 1):
                    tgt = line if case_sensitive else line.lower()
                    if q in tgt:
                        line_no = i
                        snippet = line.strip()
                        break
                matches.append(f"{rel}:{line_no}: {snippet}")
                if len(matches) >= max_matches:
                    break
        except Exception:
            continue
    return "\n".join(matches) if matches else "(no matches)"


# --- Simple task tracker (session-scoped) ---
TASKS: list[dict] = []


def tasks_add(text: str) -> str:
    log(f"tool:tasks_add text='{text}'")
    tid = len(TASKS) + 1
    TASKS.append({"id": tid, "text": text, "done": False})
    return f"added task #{tid}: {text}"


def tasks_done(task_id: int) -> str:
    log(f"tool:tasks_done id={task_id}")
    for t in TASKS:
        if t["id"] == int(task_id):
            t["done"] = True
            return f"marked task #{task_id} done"
    return f"no such task #{task_id}"


def tasks_list() -> str:
    log("tool:tasks_list")
    if not TASKS:
        return "(no tasks)"
    lines = []
    for t in TASKS:
        mark = "[x]" if t["done"] else "[ ]"
        lines.append(f"{mark} {t['id']}. {t['text']}")
    return "\n".join(lines)


def tasks_clear(done_only: bool = False) -> str:
    log(f"tool:tasks_clear done_only={done_only}")
    global TASKS
    if done_only:
        TASKS = [t for t in TASKS if not t["done"]]
        return "cleared completed tasks"
    n = len(TASKS)
    TASKS = []
    return f"cleared {n} tasks"


# --- Bulk replace tool ---
def replace_in_files(query: str, replacement: str, file_glob: str = "**/*", include_ext: str | None = None,
                     max_files: int = 100, dry_run: bool = True) -> str:
    """Find and replace across multiple files.

    - If dry_run=True, only preview diffs (queued as proposals if writes allowed later).
    - When dry_run=False, applies via propose_write (auto-applies if policy permits).
    - include_ext: comma-separated extensions to limit search (e.g., "py,ts,tsx,md").
    """
    log(f"tool:replace_in_files query='{query}' -> '{replacement}' glob='{file_glob}' max_files={max_files} dry_run={dry_run} ext={include_ext}")
    root = config.FS_ROOT
    allow_ext: set[str] | None = None
    if include_ext:
        allow_ext = {"." + e.strip().lstrip(".") for e in include_ext.split(",") if e.strip()}
    changed = 0
    previews: list[str] = []
    for path in root.glob(file_glob):
        try:
            if path.is_dir() or path.name in _DEFAULT_IGNORE_DIRS:
                continue
            if allow_ext and path.suffix not in allow_ext:
                continue
            # size cap
            if path.stat().st_size > 1_000_000:
                continue
            text = path.read_text(errors="ignore")
            if query not in text:
                continue
            new_text = text.replace(query, replacement)
            if new_text == text:
                continue
            # diff preview
            diff = "".join(unified_diff(text.splitlines(keepends=True), new_text.splitlines(keepends=True), fromfile=str(path), tofile=f"{path} (proposed)"))
            previews.append(diff or f"(changes in {path})")
            changed += 1
            # apply or queue via propose_write
            if not dry_run:
                _ = propose_write(str(path), new_text, create=True)
            if changed >= max_files:
                break
        except Exception:
            continue
    if not changed:
        return "(no changes)"
    header = f"affected files: {changed}{' (preview only)' if dry_run else ''}"
    return header + "\n\n" + ("\n\n".join(previews[:10]) + ("\n... [more diffs omitted]" if len(previews) > 10 else ""))

def get_default_tools() -> List[Callable]:
    """Return a minimal default toolset."""
    return [
        echo,
        search_stub,
        vfs_write_tool,
        vfs_read_tool,
        vfs_ls_tool,
        fs_read,
        fs_ls,
        fs_glob,
        fs_tree,
        fs_set_root,
        propose_write,
        git_status,
        git_diff,
        git_log,
        git_add,
        git_add_all,
        git_commit,
        git_restore,
        tasks_add,
        tasks_done,
        tasks_list,
        tasks_clear,
        replace_in_files,
        code_search,
    ]
