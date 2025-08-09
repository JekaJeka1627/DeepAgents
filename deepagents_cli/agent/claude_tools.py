"""
Claude Code-inspired advanced tool implementations.
"""
from typing import List, Dict, Any, Optional
import subprocess
import json
import os
from pathlib import Path
from .tools import log
from . import config

def read_file_with_context(path: str, show_line_numbers: bool = True, context_lines: int = 0) -> str:
    """Read a file with optional line numbers and context - Claude Code style."""
    log(f"tool:read_file_with_context path='{path}' show_numbers={show_line_numbers}")
    
    try:
        full_path = config.FS_ROOT / path if not Path(path).is_absolute() else Path(path)
        
        if not full_path.exists():
            return f"❌ File not found: {path}"
        
        content = full_path.read_text(encoding='utf-8', errors='replace')
        lines = content.splitlines()
        
        if show_line_numbers:
            # Format like Claude Code with line numbers
            formatted_lines = []
            for i, line in enumerate(lines, 1):
                formatted_lines.append(f"{i:5}→{line}")
            return "\n".join(formatted_lines)
        else:
            return content
            
    except Exception as e:
        return f"❌ Error reading {path}: {str(e)}"

def write_file_with_backup(path: str, content: str, create_backup: bool = True) -> str:
    """Write file with automatic backup like Claude Code."""
    log(f"tool:write_file_with_backup path='{path}' backup={create_backup}")
    
    try:
        full_path = config.FS_ROOT / path if not Path(path).is_absolute() else Path(path)
        
        # Create backup if file exists
        if create_backup and full_path.exists():
            backup_path = full_path.with_suffix(full_path.suffix + '.backup')
            backup_path.write_bytes(full_path.read_bytes())
        
        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        full_path.write_text(content, encoding='utf-8')
        
        return f"✅ Successfully wrote {len(content)} characters to {path}"
        
    except Exception as e:
        return f"❌ Error writing {path}: {str(e)}"

def intelligent_search(query: str, file_patterns: str = "**/*", context: int = 2) -> str:
    """Advanced search with context lines like Claude Code."""
    log(f"tool:intelligent_search query='{query}' patterns='{file_patterns}'")
    
    try:
        root = config.FS_ROOT
        results = []
        
        # Search through files
        for file_path in root.glob(file_patterns):
            if file_path.is_file() and not any(exclude in str(file_path) for exclude in ['.git', 'node_modules', '__pycache__']):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.splitlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if query.lower() in line.lower():
                            # Get context lines
                            start = max(0, line_num - context - 1)
                            end = min(len(lines), line_num + context)
                            
                            context_lines = []
                            for i in range(start, end):
                                prefix = "→" if i == line_num - 1 else " "
                                context_lines.append(f"{i+1:5}{prefix}{lines[i]}")
                            
                            rel_path = file_path.relative_to(root)
                            results.append(f"📍 {rel_path}:{line_num}\n" + "\n".join(context_lines))
                            
                except Exception:
                    continue
        
        if results:
            return f"🔍 Found {len(results)} matches for '{query}':\n\n" + "\n\n".join(results[:10])
        else:
            return f"🔍 No matches found for '{query}'"
            
    except Exception as e:
        return f"❌ Search error: {str(e)}"

def project_structure(path: str = ".", max_depth: int = 3, show_hidden: bool = False) -> str:
    """Generate an intelligent project overview like Claude Code."""
    log(f"tool:project_structure path='{path}' depth={max_depth}")
    
    try:
        base_path = config.FS_ROOT / path if path != "." else config.FS_ROOT
        
        if not base_path.exists():
            return f"❌ Path not found: {path}"
        
        structure = []
        ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}
        
        def add_path(current_path: Path, depth: int, prefix: str = ""):
            if depth > max_depth:
                return
                
            items = sorted(current_path.iterdir())
            dirs = [p for p in items if p.is_dir() and (show_hidden or not p.name.startswith('.'))]
            files = [p for p in items if p.is_file() and (show_hidden or not p.name.startswith('.'))]
            
            # Add directories first
            for i, dir_path in enumerate(dirs):
                if dir_path.name in ignored_dirs:
                    continue
                    
                is_last_dir = i == len(dirs) - 1 and not files
                connector = "└── " if is_last_dir else "├── "
                structure.append(f"{prefix}{connector}{dir_path.name}/")
                
                next_prefix = prefix + ("    " if is_last_dir else "│   ")
                add_path(dir_path, depth + 1, next_prefix)
            
            # Add files
            for i, file_path in enumerate(files):
                is_last = i == len(files) - 1
                connector = "└── " if is_last else "├── "
                
                # Add file size and type info
                size = file_path.stat().st_size
                size_str = f" ({size} bytes)" if size < 1024 else f" ({size//1024}KB)"
                
                structure.append(f"{prefix}{connector}{file_path.name}{size_str}")
        
        structure.append(f"📁 {base_path.name}/")
        add_path(base_path, 0)
        
        return "\n".join(structure)
        
    except Exception as e:
        return f"❌ Error generating structure: {str(e)}"

def smart_git_status() -> str:
    """Enhanced git status with intelligent insights."""
    log("tool:smart_git_status")
    
    try:
        # Get basic git status
        result = subprocess.run(
            ["git", "status", "--porcelain", "-b"],
            cwd=config.FS_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return "❌ Not a git repository or git error"
        
        lines = result.stdout.strip().split('\n')
        if not lines or not lines[0]:
            return "✅ Working tree clean"
        
        branch_info = lines[0]
        changes = lines[1:] if len(lines) > 1 else []
        
        # Parse branch info
        branch_match = branch_info.replace('## ', '')
        
        # Categorize changes
        staged = []
        modified = []
        untracked = []
        
        for change in changes:
            if not change.strip():
                continue
            status = change[:2]
            filepath = change[3:]
            
            if status[0] in 'MADRC':
                staged.append(f"  ✓ {filepath}")
            elif status[1] in 'M':
                modified.append(f"  📝 {filepath}")
            elif status == '??':
                untracked.append(f"  ❓ {filepath}")
        
        # Build status report
        report = [f"🌿 Branch: {branch_match}"]
        
        if staged:
            report.append(f"\n📦 Staged changes ({len(staged)}):")
            report.extend(staged)
        
        if modified:
            report.append(f"\n📝 Modified files ({len(modified)}):")
            report.extend(modified)
        
        if untracked:
            report.append(f"\n❓ Untracked files ({len(untracked)}):")
            report.extend(untracked)
        
        return "\n".join(report)
        
    except Exception as e:
        return f"❌ Git status error: {str(e)}"

def multi_file_edit(edits: List[Dict[str, Any]]) -> str:
    """Perform multiple file edits atomically like Claude Code."""
    log(f"tool:multi_file_edit count={len(edits)}")
    
    try:
        results = []
        backups = []
        
        # Create backups first
        for edit in edits:
            file_path = Path(edit['file'])
            if file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.tmp_backup')
                backup_path.write_bytes(file_path.read_bytes())
                backups.append((file_path, backup_path))
        
        # Apply edits
        for edit in edits:
            file_path = config.FS_ROOT / edit['file']
            
            if 'content' in edit:
                # Full file replacement
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(edit['content'], encoding='utf-8')
                results.append(f"✅ Updated {edit['file']}")
                
            elif 'find' in edit and 'replace' in edit:
                # Find and replace
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    new_content = content.replace(edit['find'], edit['replace'])
                    file_path.write_text(new_content, encoding='utf-8')
                    results.append(f"✅ Replaced text in {edit['file']}")
                else:
                    results.append(f"❌ File not found: {edit['file']}")
        
        # Clean up backups on success
        for original, backup in backups:
            if backup.exists():
                backup.unlink()
        
        return "🔄 Multi-file edit completed:\n" + "\n".join(results)
        
    except Exception as e:
        # Restore backups on failure
        for original, backup in backups:
            if backup.exists():
                original.write_bytes(backup.read_bytes())
                backup.unlink()
        
        return f"❌ Multi-file edit failed: {str(e)}\n(Files restored from backup)"

def claude_code_tools() -> List:
    """Return the enhanced Claude Code-style tools."""
    return [
        read_file_with_context,
        write_file_with_backup,
        intelligent_search,
        project_structure,
        smart_git_status,
        multi_file_edit,
    ]