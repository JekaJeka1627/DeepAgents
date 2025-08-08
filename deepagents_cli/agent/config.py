"""
Shared runtime configuration for DeepAgents CLI tools.

- FS_ROOT: sandbox root for host filesystem operations (defaults to current working directory)
- ALLOW_FS_READ: allow reading files under FS_ROOT
- ALLOW_FS_WRITE: allow writing/modifying files under FS_ROOT (default False)

These can be adjusted by the CLI at startup based on flags/env.
"""
from __future__ import annotations

import os
from pathlib import Path

# Defaults
FS_ROOT: Path = Path(os.getcwd()).resolve()
ALLOW_FS_READ: bool = True
ALLOW_FS_WRITE: bool = False
ALLOW_AUTO_APPLY: bool = False


def set_fs_root(path: str | os.PathLike[str]) -> None:
    global FS_ROOT
    FS_ROOT = Path(path).resolve()


def set_allow_fs_read(value: bool) -> None:
    global ALLOW_FS_READ
    ALLOW_FS_READ = bool(value)


def set_allow_fs_write(value: bool) -> None:
    global ALLOW_FS_WRITE
    ALLOW_FS_WRITE = bool(value)


def set_allow_auto_apply(value: bool) -> None:
    """Allow the agent to apply write proposals without manual :accept.

    WARNING: This enables direct writes when ALLOW_FS_WRITE is also True.
    """
    global ALLOW_AUTO_APPLY
    ALLOW_AUTO_APPLY = bool(value)
