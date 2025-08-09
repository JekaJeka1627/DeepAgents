"""
DeepAgents Status Line Module

Provides a comprehensive status line similar to Claude Code with:
- TIME: Live clock
- HOST: Hostname 
- MODEL: Active model
- FOLDER: Current folder name
- BRANCH: Git branch (when in repo)
- PATH: Full directory path
"""
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class StatusLine:
    """Manages the DeepAgents status line display."""
    
    def __init__(self):
        self.last_git_check = 0
        self.cached_git_branch: Optional[str] = None
        self.cached_git_path: Optional[str] = None
        
    def get_current_time(self) -> str:
        """Get current time in 12-hour format."""
        return datetime.now().strftime("%I:%M:%S %p")
    
    def get_hostname(self) -> str:
        """Get the system hostname."""
        try:
            import socket
            return socket.gethostname()
        except Exception:
            return "unknown"
    
    def get_current_model(self) -> str:
        """Get the active Claude model."""
        # Try to get from environment or config
        from deepagents_cli.agent.factory import get_last_selection
        try:
            model_info = get_last_selection()
            if "claude" in model_info.lower():
                if "sonnet" in model_info.lower():
                    return "Sonnet 4"
                elif "haiku" in model_info.lower():
                    return "Haiku 3.5"
                else:
                    return "Claude"
            elif "gpt" in model_info.lower():
                if "gpt-5" in model_info.lower():
                    return "GPT-5"
                elif "gpt-4" in model_info.lower():
                    return "GPT-4"
                else:
                    return "GPT"
            elif "gemini" in model_info.lower():
                return "Gemini"
            else:
                return "AI Model"
        except Exception:
            return "Sonnet 4"  # Default fallback
    
    def get_current_folder(self) -> str:
        """Get the name of the current folder."""
        try:
            return Path.cwd().name
        except Exception:
            return "unknown"
    
    def get_git_branch(self, force_refresh: bool = False) -> Optional[str]:
        """Get current git branch if in a repository."""
        current_time = time.time()
        current_path = str(Path.cwd())
        
        # Cache git branch info for 5 seconds to avoid repeated subprocess calls
        if (not force_refresh and 
            current_time - self.last_git_check < 5 and 
            self.cached_git_path == current_path and 
            self.cached_git_branch is not None):
            return self.cached_git_branch
        
        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=current_path
            )
            
            if result.returncode == 0:
                # Get the current branch name
                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    cwd=current_path
                )
                
                if branch_result.returncode == 0:
                    branch = branch_result.stdout.strip()
                    if branch:
                        self.cached_git_branch = branch
                        self.cached_git_path = current_path
                        self.last_git_check = current_time
                        return branch
            
            # Not in a git repo or no branch
            self.cached_git_branch = None
            self.cached_git_path = current_path
            self.last_git_check = current_time
            return None
            
        except Exception:
            # Git not available or other error
            self.cached_git_branch = None
            self.cached_git_path = current_path
            self.last_git_check = current_time
            return None
    
    def get_full_path(self) -> str:
        """Get the full current directory path."""
        try:
            return str(Path.cwd())
        except Exception:
            return "unknown"
    
    def generate_status_line(self) -> str:
        """Generate the complete status line string."""
        components = []
        
        # Live clock
        components.append(f"TIME {self.get_current_time()}")
        
        # Hostname
        components.append(f"HOST {self.get_hostname()}")
        
        # Active model
        components.append(f"MODEL {self.get_current_model()}")
        
        # Current folder name
        components.append(f"FOLDER {self.get_current_folder()}")
        
        # Git branch (only if in repo)
        git_branch = self.get_git_branch()
        if git_branch:
            components.append(f"BRANCH {git_branch}")
        
        # Full directory path
        components.append(f"PATH {self.get_full_path()}")
        
        return " | ".join(components)
    
    def print_status_line(self) -> None:
        """Print the status line to console."""
        print(self.generate_status_line())


# Global status line instance
status_line = StatusLine()


def get_status_line() -> str:
    """Get the current status line string."""
    return status_line.generate_status_line()


def print_status() -> None:
    """Print the current status line."""
    status_line.print_status_line()


def refresh_git_cache() -> None:
    """Force refresh of git branch cache."""
    status_line.get_git_branch(force_refresh=True)