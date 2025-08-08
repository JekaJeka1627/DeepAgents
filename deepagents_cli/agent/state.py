"""
Simple in-memory virtual file system (VFS) with JSON persistence.
This is independent from deepagents' internal state, but provides a
useful shared store for tools to read/write artifacts and notes.
"""
from __future__ import annotations

import json
from typing import Dict, Any

# Module-level VFS store
_VFS: Dict[str, str] = {}


def vfs_write(name: str, content: str) -> str:
    """Write content to a named item in the VFS."""
    _VFS[name] = content
    return f"[vfs_write] Wrote {len(content)} chars to '{name}'"


def vfs_read(name: str) -> str:
    """Read content from a named item in the VFS."""
    if name not in _VFS:
        return f"[vfs_read] '{name}' not found"
    return _VFS[name]


def vfs_ls() -> str:
    """List items in the VFS."""
    if not _VFS:
        return "[vfs_ls] (empty)"
    keys = sorted(_VFS.keys())
    return "\n".join(keys)


def save_vfs(path: str) -> str:
    """Persist the VFS to a JSON file."""
    data: Dict[str, Any] = {"vfs": _VFS}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return f"[vfs] saved to {path}"


def load_vfs(path: str) -> str:
    """Load the VFS from a JSON file. Replaces current store."""
    global _VFS
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _VFS = {**(data.get("vfs") or {})}
    return f"[vfs] loaded from {path}"
