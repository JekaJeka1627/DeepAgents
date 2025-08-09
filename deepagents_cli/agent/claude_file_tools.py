"""
Claude Code-equivalent file system tools with full access.
These tools match Claude Code's file access capabilities.
"""
import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import fnmatch
import re
from .logging import log


def read_file_unrestricted(file_path: str, start_line: int = None, end_line: int = None) -> str:
    """
    Read file with full file system access - Claude Code equivalent.
    """
    log(f"tool:read_file_unrestricted path='{file_path}' start={start_line} end={end_line}")
    
    try:
        # Handle Windows and Unix paths
        path = Path(file_path).resolve()
        
        if not path.exists():
            return f"File not found: {file_path}"
        
        if path.is_dir():
            return f"Path is a directory, not a file: {file_path}"
        
        # Check if file is too large (>10MB)
        if path.stat().st_size > 10 * 1024 * 1024:
            return f"File too large to read: {file_path} ({path.stat().st_size} bytes)"
        
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except UnicodeDecodeError:
            # Try other encodings if UTF-8 fails
            for encoding in ['latin-1', 'cp1252', 'ascii']:
                try:
                    content = path.read_text(encoding=encoding, errors='replace')
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return f"Could not decode file: {file_path}"
        
        lines = content.splitlines()
        
        # Apply line range if specified
        if start_line is not None or end_line is not None:
            start = max(0, (start_line - 1)) if start_line else 0
            end = min(len(lines), end_line) if end_line else len(lines)
            lines = lines[start:end]
            line_offset = start_line or 1
        else:
            line_offset = 1
        
        # Format with line numbers like Claude Code
        if len(lines) > 0:
            formatted_lines = []
            for i, line in enumerate(lines):
                line_num = line_offset + i
                formatted_lines.append(f"{line_num:5d}→{line}")
            return "\n".join(formatted_lines)
        else:
            return f"File is empty: {file_path}"
            
    except PermissionError:
        return f"Permission denied: {file_path}"
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"


def write_file_unrestricted(file_path: str, content: str, create_backup: bool = True) -> str:
    """
    Write file with full file system access - Claude Code equivalent.
    """
    log(f"tool:write_file_unrestricted path='{file_path}' len={len(content)} backup={create_backup}")
    
    try:
        path = Path(file_path).resolve()
        
        # Create backup if file exists and requested
        if create_backup and path.exists():
            backup_path = path.with_suffix(path.suffix + '.backup')
            backup_path.write_bytes(path.read_bytes())
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        path.write_text(content, encoding='utf-8')
        
        lines_count = len(content.splitlines())
        return f"Successfully wrote {lines_count} lines to {file_path}"
        
    except PermissionError:
        return f"Permission denied writing to: {file_path}"
    except Exception as e:
        return f"Error writing {file_path}: {str(e)}"


def list_directory_unrestricted(directory: str = ".", pattern: str = "*", 
                               show_hidden: bool = False, max_items: int = 100) -> str:
    """
    List directory with full file system access - Claude Code equivalent.
    """
    log(f"tool:list_directory_unrestricted dir='{directory}' pattern='{pattern}' hidden={show_hidden}")
    
    try:
        path = Path(directory).resolve()
        
        if not path.exists():
            return f"Directory not found: {directory}"
        
        if not path.is_dir():
            return f"Not a directory: {directory}"
        
        # Get all items
        try:
            items = list(path.iterdir())
        except PermissionError:
            return f"Permission denied accessing: {directory}"
        
        # Filter by pattern
        if pattern != "*":
            items = [item for item in items if fnmatch.fnmatch(item.name, pattern)]
        
        # Filter hidden files
        if not show_hidden:
            items = [item for item in items if not item.name.startswith('.')]
        
        # Sort: directories first, then files alphabetically
        items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        
        # Limit results
        if len(items) > max_items:
            items = items[:max_items]
            truncated = True
        else:
            truncated = False
        
        # Format output like Claude Code
        result = []
        result.append(f"📁 {path}")
        result.append("")
        
        for item in items:
            try:
                if item.is_dir():
                    # Count items in subdirectory
                    try:
                        subitem_count = len([x for x in item.iterdir() if not x.name.startswith('.') or show_hidden])
                        result.append(f"📁 {item.name}/ ({subitem_count} items)")
                    except (PermissionError, OSError):
                        result.append(f"📁 {item.name}/ (access denied)")
                else:
                    # Show file size
                    try:
                        size = item.stat().st_size
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024**2:
                            size_str = f"{size/1024:.1f}KB"
                        elif size < 1024**3:
                            size_str = f"{size/(1024**2):.1f}MB"
                        else:
                            size_str = f"{size/(1024**3):.1f}GB"
                        result.append(f"📄 {item.name} ({size_str})")
                    except (PermissionError, OSError):
                        result.append(f"📄 {item.name} (access denied)")
            except Exception:
                result.append(f"❓ {item.name} (unknown)")
        
        if truncated:
            result.append(f"\n... and {len(list(path.iterdir())) - max_items} more items")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error listing {directory}: {str(e)}"


def search_files_unrestricted(pattern: str, directory: str = ".", file_pattern: str = "*",
                             context_lines: int = 2, case_sensitive: bool = False,
                             max_matches: int = 50) -> str:
    """
    Search files with full file system access - Claude Code equivalent.
    """
    log(f"tool:search_files_unrestricted pattern='{pattern}' dir='{directory}' file_pattern='{file_pattern}'")
    
    try:
        path = Path(directory).resolve()
        
        if not path.exists():
            return f"Directory not found: {directory}"
        
        if not path.is_dir():
            return f"Not a directory: {directory}"
        
        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return f"Invalid regex pattern: {e}"
        
        results = []
        files_searched = 0
        
        # Search recursively
        for file_path in path.rglob("*"):
            if len(results) >= max_matches:
                break
                
            try:
                if not file_path.is_file():
                    continue
                
                # Check file pattern
                if not fnmatch.fnmatch(file_path.name, file_pattern):
                    continue
                
                # Skip binary files and very large files
                if file_path.stat().st_size > 5 * 1024 * 1024:  # Skip files > 5MB
                    continue
                
                # Try to read as text
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                except (UnicodeDecodeError, PermissionError):
                    continue
                
                files_searched += 1
                lines = content.splitlines()
                
                # Search for pattern in each line
                for line_num, line in enumerate(lines):
                    if regex.search(line):
                        # Get context lines
                        start_line = max(0, line_num - context_lines)
                        end_line = min(len(lines), line_num + context_lines + 1)
                        
                        context = []
                        for i in range(start_line, end_line):
                            marker = "►" if i == line_num else " "
                            context.append(f"{i+1:4d}{marker} {lines[i]}")
                        
                        results.append({
                            'file': str(file_path.relative_to(path)),
                            'line': line_num + 1,
                            'match': line.strip(),
                            'context': "\n".join(context)
                        })
                        
                        if len(results) >= max_matches:
                            break
                            
            except Exception:
                continue  # Skip problematic files
        
        if not results:
            return f"No matches found for pattern '{pattern}' in {files_searched} files searched"
        
        # Format results like Claude Code
        output = []
        output.append(f"Found {len(results)} matches for '{pattern}' in {files_searched} files:")
        output.append("")
        
        for result in results:
            output.append(f"📄 {result['file']}:{result['line']}")
            output.append(result['context'])
            output.append("")
        
        if len(results) >= max_matches:
            output.append(f"(Showing first {max_matches} matches)")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error searching: {str(e)}"


def run_command_unrestricted(command: str, working_dir: str = None, timeout: int = 30) -> str:
    """
    Execute shell command with full system access - Claude Code equivalent.
    """
    log(f"tool:run_command_unrestricted cmd='{command}' cwd='{working_dir}' timeout={timeout}")
    
    # Basic safety checks
    dangerous_commands = [
        'rm -rf /', 'del /s /q c:\\', 'format c:', 'shutdown', 'reboot',
        'dd if=', ':(){ :|:& };:', 'chmod -R 777 /',
        'mv / /dev/null', 'cat /dev/zero >', 'mkfs'
    ]
    
    cmd_lower = command.lower()
    for dangerous in dangerous_commands:
        if dangerous in cmd_lower:
            return f"Dangerous command blocked: {command}"
    
    try:
        # Set working directory
        cwd = Path(working_dir).resolve() if working_dir else None
        if cwd and not cwd.exists():
            return f"Working directory not found: {working_dir}"
        
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        
        output_parts = []
        
        # Add stdout
        if result.stdout:
            output_parts.append("STDOUT:")
            output_parts.append(result.stdout.rstrip())
        
        # Add stderr
        if result.stderr:
            output_parts.append("STDERR:")
            output_parts.append(result.stderr.rstrip())
        
        # Add return code info
        if result.returncode == 0:
            status = "✅ Command completed successfully"
        else:
            status = f"❌ Command failed with exit code {result.returncode}"
        
        output_parts.append("")
        output_parts.append(status)
        
        return "\n".join(output_parts)
        
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds: {command}"
    except FileNotFoundError:
        return f"Command not found: {command.split()[0] if command.split() else command}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def glob_files_unrestricted(pattern: str, directory: str = ".") -> str:
    """
    Glob pattern matching with full file system access - Claude Code equivalent.
    """
    log(f"tool:glob_files_unrestricted pattern='{pattern}' dir='{directory}'")
    
    try:
        path = Path(directory).resolve()
        
        if not path.exists():
            return f"Directory not found: {directory}"
        
        if not path.is_dir():
            return f"Not a directory: {directory}"
        
        # Perform glob search
        matches = list(path.glob(pattern))
        
        if not matches:
            return f"No files match pattern '{pattern}' in {directory}"
        
        # Sort matches
        matches.sort()
        
        # Format output
        result = []
        result.append(f"Found {len(matches)} files matching '{pattern}':")
        result.append("")
        
        for match in matches:
            try:
                relative_path = match.relative_to(path)
                if match.is_dir():
                    result.append(f"📁 {relative_path}/")
                else:
                    size = match.stat().st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024**2:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024**2):.1f}MB"
                    result.append(f"📄 {relative_path} ({size_str})")
            except (ValueError, OSError):
                result.append(f"❓ {match}")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error globbing: {str(e)}"


def get_claude_file_tools() -> List:
    """Return all Claude Code-equivalent file tools."""
    return [
        read_file_unrestricted,
        write_file_unrestricted, 
        list_directory_unrestricted,
        search_files_unrestricted,
        run_command_unrestricted,
        glob_files_unrestricted
    ]