"""
Claude Code-style system commands for DeepAgents CLI.
Implements the same command interface as Claude Code for consistent UX.
"""
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.tree import Tree

console = Console()

class ClaudeCommands:
    """Claude Code-style system commands."""
    
    def __init__(self):
        self.current_task_list = []
        
    # ===============================
    # FILE OPERATIONS (like Claude Code)
    # ===============================
    
    def read_file(self, file_path: str, start_line: int = None, end_line: int = None) -> str:
        """Read file with syntax highlighting - Claude Code style."""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"❌ File not found: {file_path}"
            
            content = path.read_text(encoding='utf-8', errors='replace')
            lines = content.splitlines()
            
            # Apply line range if specified
            if start_line is not None or end_line is not None:
                start = (start_line - 1) if start_line else 0
                end = end_line if end_line else len(lines)
                lines = lines[start:end]
                
            # Format with line numbers like Claude Code
            formatted_lines = []
            line_start = start_line or 1
            for i, line in enumerate(lines):
                line_num = line_start + i
                formatted_lines.append(f"{line_num:4d}│{line}")
            
            # Detect file type for syntax highlighting
            suffix = path.suffix.lower()
            language_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.jsx': 'jsx', '.tsx': 'tsx', '.html': 'html', '.css': 'css',
                '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown',
                '.sh': 'bash', '.sql': 'sql', '.rs': 'rust', '.go': 'go',
                '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp'
            }
            
            language = language_map.get(suffix, 'text')
            
            # Display with syntax highlighting
            syntax = Syntax('\n'.join(formatted_lines), language, line_numbers=False, theme="monokai")
            console.print(Panel(syntax, title=f"📄 {path.name}", border_style="blue"))
            
            return f"✅ Read {len(lines)} lines from {file_path}"
            
        except Exception as e:
            return f"❌ Error reading {file_path}: {str(e)}"
    
    def write_file(self, file_path: str, content: str, create_backup: bool = True) -> str:
        """Write file with backup - Claude Code style."""
        try:
            path = Path(file_path)
            
            # Create backup if file exists
            if create_backup and path.exists():
                backup_path = path.with_suffix(path.suffix + '.backup')
                backup_path.write_bytes(path.read_bytes())
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            path.write_text(content, encoding='utf-8')
            
            lines_written = len(content.splitlines())
            return f"✅ Wrote {lines_written} lines to {file_path}"
            
        except Exception as e:
            return f"❌ Error writing {file_path}: {str(e)}"
    
    def edit_file(self, file_path: str, old_text: str, new_text: str, line_number: int = None) -> str:
        """Edit file with search and replace - Claude Code style."""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"❌ File not found: {file_path}"
            
            content = path.read_text(encoding='utf-8')
            
            if old_text not in content:
                return f"❌ Text not found in {file_path}: '{old_text[:50]}...'"
            
            # Perform replacement
            new_content = content.replace(old_text, new_text)
            
            # Create backup
            backup_path = path.with_suffix(path.suffix + '.backup')
            backup_path.write_text(content, encoding='utf-8')
            
            # Write new content
            path.write_text(new_content, encoding='utf-8')
            
            return f"✅ Edited {file_path} - replaced text successfully"
            
        except Exception as e:
            return f"❌ Error editing {file_path}: {str(e)}"
    
    def list_files(self, directory: str = ".", pattern: str = "*", show_hidden: bool = False) -> str:
        """List files with rich formatting - Claude Code style."""
        try:
            path = Path(directory)
            if not path.exists():
                return f"❌ Directory not found: {directory}"
            
            if not path.is_dir():
                return f"❌ Not a directory: {directory}"
            
            tree = Tree(f"📁 {path.name}")
            
            # Get files matching pattern
            if pattern == "*":
                files = list(path.iterdir())
            else:
                files = list(path.glob(pattern))
            
            # Filter hidden files
            if not show_hidden:
                files = [f for f in files if not f.name.startswith('.')]
            
            # Sort: directories first, then files
            files.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for file_path in files:
                if file_path.is_dir():
                    tree.add(f"📁 {file_path.name}/")
                else:
                    # Get file size
                    size = file_path.stat().st_size
                    size_str = self._format_file_size(size)
                    tree.add(f"📄 {file_path.name} ({size_str})")
            
            console.print(tree)
            return f"✅ Listed {len(files)} items in {directory}"
            
        except Exception as e:
            return f"❌ Error listing {directory}: {str(e)}"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f}KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f}MB"
        else:
            return f"{size_bytes/(1024**3):.1f}GB"
    
    # ===============================
    # SEARCH OPERATIONS
    # ===============================
    
    def grep_search(self, pattern: str, directory: str = ".", file_pattern: str = "*", 
                   context_lines: int = 2, case_sensitive: bool = False) -> str:
        """Grep search with context - Claude Code style."""
        try:
            import re
            
            path = Path(directory)
            if not path.exists():
                return f"❌ Directory not found: {directory}"
            
            # Get files to search
            if file_pattern == "*":
                files = [f for f in path.rglob("*") if f.is_file()]
            else:
                files = list(path.rglob(file_pattern))
            
            # Filter text files only
            text_extensions = {'.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.txt', '.yaml', '.yml'}
            files = [f for f in files if f.suffix.lower() in text_extensions or f.suffix == '']
            
            results = []
            flags = 0 if case_sensitive else re.IGNORECASE
            
            for file_path in files:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='replace')
                    lines = content.splitlines()
                    
                    for i, line in enumerate(lines):
                        if re.search(pattern, line, flags):
                            # Add context lines
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            
                            context = []
                            for j in range(start, end):
                                marker = "►" if j == i else " "
                                context.append(f"{j+1:4d}{marker} {lines[j]}")
                            
                            results.append({
                                'file': str(file_path.relative_to(path)),
                                'line': i + 1,
                                'context': '\n'.join(context)
                            })
                            
                except Exception:
                    continue  # Skip files that can't be read
            
            if not results:
                return f"❌ No matches found for pattern: {pattern}"
            
            # Display results
            for result in results[:10]:  # Limit to first 10 results
                console.print(Panel(
                    result['context'],
                    title=f"🔍 {result['file']}:{result['line']}",
                    border_style="green"
                ))
            
            if len(results) > 10:
                console.print(f"... and {len(results) - 10} more matches")
            
            return f"✅ Found {len(results)} matches for '{pattern}'"
            
        except Exception as e:
            return f"❌ Search error: {str(e)}"
    
    # ===============================
    # DEVELOPMENT TOOLS
    # ===============================
    
    def run_bash(self, command: str, timeout: int = 30) -> str:
        """Execute bash command - Claude Code style."""
        try:
            # Safety check for dangerous commands
            dangerous = ['rm -rf', 'format', 'del /s', 'rmdir /s']
            if any(danger in command.lower() for danger in dangerous):
                return f"❌ Dangerous command blocked: {command}"
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
            
            output = result.stdout
            error = result.stderr
            
            if result.returncode == 0:
                if output:
                    console.print(Panel(output, title=f"💻 {command}", border_style="green"))
                return f"✅ Command executed successfully (exit code: {result.returncode})"
            else:
                if error:
                    console.print(Panel(error, title=f"❌ {command}", border_style="red"))
                return f"❌ Command failed (exit code: {result.returncode})"
                
        except subprocess.TimeoutExpired:
            return f"⏰ Command timed out after {timeout} seconds: {command}"
        except Exception as e:
            return f"❌ Error executing command: {str(e)}"
    
    # ===============================
    # WEB OPERATIONS (like Claude Code)
    # ===============================
    
    def web_search(self, query: str, max_results: int = 5) -> str:
        """Web search - Claude Code style."""
        try:
            import requests
            from urllib.parse import quote_plus
            
            # Use DuckDuckGo Instant Answer API (free, no API key needed)
            search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            
            response = requests.get(search_url, timeout=10)
            data = response.json()
            
            results = []
            
            # Get instant answer
            if data.get('AbstractText'):
                results.append({
                    'title': data.get('AbstractSource', 'Instant Answer'),
                    'snippet': data.get('AbstractText'),
                    'url': data.get('AbstractURL', '')
                })
            
            # Get related topics
            for topic in data.get('RelatedTopics', [])[:max_results-len(results)]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' '),
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', '')
                    })
            
            if not results:
                return f"❌ No search results found for: {query}"
            
            # Display results
            for i, result in enumerate(results, 1):
                console.print(Panel(
                    f"{result['snippet']}\n\n🔗 {result['url']}" if result['url'] else result['snippet'],
                    title=f"🔍 {i}. {result['title']}",
                    border_style="cyan"
                ))
            
            return f"✅ Found {len(results)} search results for '{query}'"
            
        except Exception as e:
            return f"❌ Search error: {str(e)}"
    
    def web_fetch(self, url: str) -> str:
        """Fetch web content - Claude Code style."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract main content (remove scripts, styles, etc.)
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Get text content
            content = soup.get_text()
            
            # Clean up content
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            clean_content = '\n'.join(lines[:50])  # Limit to first 50 lines
            
            # Display content
            console.print(Panel(
                f"**{title_text}**\n\n{clean_content}\n\n🔗 Source: {url}",
                title="🌐 Web Content",
                border_style="blue"
            ))
            
            return f"✅ Fetched content from {url}"
            
        except Exception as e:
            return f"❌ Fetch error: {str(e)}"
    
    # ===============================
    # TASK MANAGEMENT (like TodoWrite)
    # ===============================
    
    def add_task(self, task_description: str, priority: str = "normal") -> str:
        """Add task to current list - Claude Code style."""
        task = {
            'id': len(self.current_task_list) + 1,
            'description': task_description,
            'status': 'pending',
            'priority': priority
        }
        self.current_task_list.append(task)
        return f"✅ Added task #{task['id']}: {task_description}"
    
    def complete_task(self, task_id: int) -> str:
        """Mark task as completed - Claude Code style."""
        for task in self.current_task_list:
            if task['id'] == task_id:
                task['status'] = 'completed'
                return f"✅ Completed task #{task_id}: {task['description']}"
        return f"❌ Task #{task_id} not found"
    
    def list_tasks(self) -> str:
        """List all tasks - Claude Code style."""
        if not self.current_task_list:
            console.print("📝 No tasks in current list")
            return "No tasks found"
        
        pending_tasks = [t for t in self.current_task_list if t['status'] == 'pending']
        completed_tasks = [t for t in self.current_task_list if t['status'] == 'completed']
        
        # Display pending tasks
        if pending_tasks:
            console.print("\n🔄 **Pending Tasks:**")
            for task in pending_tasks:
                priority_emoji = {"high": "🔥", "normal": "📝", "low": "💭"}
                emoji = priority_emoji.get(task['priority'], "📝")
                console.print(f"  {emoji} #{task['id']}: {task['description']}")
        
        # Display completed tasks
        if completed_tasks:
            console.print("\n✅ **Completed Tasks:**")
            for task in completed_tasks[-5:]:  # Show last 5 completed
                console.print(f"  ✅ #{task['id']}: {task['description']}")
        
        return f"📊 {len(pending_tasks)} pending, {len(completed_tasks)} completed"
    
    def clear_completed_tasks(self) -> str:
        """Clear completed tasks - Claude Code style."""
        completed_count = len([t for t in self.current_task_list if t['status'] == 'completed'])
        self.current_task_list = [t for t in self.current_task_list if t['status'] != 'completed']
        return f"🗑️ Cleared {completed_count} completed tasks"


# Global instance for CLI
claude_commands = ClaudeCommands()