"""
Minimal logging/trace controls for the DeepAgents CLI.
"""
from __future__ import annotations

VERBOSE: bool = False


def set_verbose(value: bool) -> None:
    global VERBOSE
    VERBOSE = bool(value)


def is_verbose() -> bool:
    return VERBOSE


def log(msg: str) -> None:
    if VERBOSE:
        print(f"[trace] {msg}")
