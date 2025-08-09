"""
Claude Code-inspired output formatting and user experience enhancements.
"""
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from contextlib import contextmanager
import time
import re

class ClaudeFormatter:
    """Enhanced formatting to match Claude Code's sophisticated output."""
    
    def __init__(self):
        self.console = Console()
        
    def format_response(self, text: str, context: dict = None) -> None:
        """Format agent response with Claude Code-style enhancements."""
        
        # Detect and handle different content types
        if self._is_code_heavy(text):
            self._format_code_response(text)
        elif self._contains_file_operations(text):
            self._format_file_operation_response(text)
        elif self._contains_error(text):
            self._format_error_response(text)
        else:
            self._format_standard_response(text)
    
    def _format_standard_response(self, text: str) -> None:
        """Standard markdown formatting with enhancements."""
        # Clean up the text
        cleaned = self._clean_agent_artifacts(text)
        
        # Render as markdown with custom styling
        md = Markdown(cleaned, code_theme="monokai")
        self.console.print(md)
    
    def _format_code_response(self, text: str) -> None:
        """Special formatting for code-heavy responses."""
        lines = text.split('\n')
        current_block = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code:
                    # End of code block
                    if current_block:
                        lang = current_block[0].replace('```', '').strip() or 'text'
                        code = '\n'.join(current_block[1:])
                        syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                        self.console.print(Panel(syntax, expand=False))
                    current_block = []
                    in_code = False
                else:
                    # Start of code block
                    current_block = [line]
                    in_code = True
            elif in_code:
                current_block.append(line)
            else:
                if line.strip():
                    self.console.print(line)
    
    def _format_file_operation_response(self, text: str) -> None:
        """Special formatting for file operation responses."""
        # Look for file paths and highlight them
        enhanced_text = re.sub(
            r'([/\\][\w\./\\-]+\.\w+)',
            r'[bold blue]\1[/bold blue]',
            text
        )
        
        # Look for tool operations and format them
        enhanced_text = re.sub(
            r'(Reading|Writing|Creating|Updating|Deleting)\s+([/\\][\w\./\\-]+)',
            r'[green]\1[/green] [bold]\2[/bold]',
            enhanced_text
        )
        
        md = Markdown(enhanced_text, code_theme="monokai")
        self.console.print(md)
    
    def _format_error_response(self, text: str) -> None:
        """Special formatting for error responses."""
        self.console.print(Panel(
            text, 
            title="⚠️ Error", 
            border_style="red",
            expand=False
        ))
    
    def _is_code_heavy(self, text: str) -> bool:
        """Check if response contains significant code content."""
        code_block_count = text.count('```')
        return code_block_count >= 2
    
    def _contains_file_operations(self, text: str) -> bool:
        """Check if response describes file operations."""
        file_ops = ['reading', 'writing', 'creating', 'updating', 'editing', 'saved', 'loaded']
        text_lower = text.lower()
        return any(op in text_lower for op in file_ops)
    
    def _contains_error(self, text: str) -> bool:
        """Check if response contains error information."""
        error_indicators = ['error', 'failed', 'exception', 'traceback', 'cannot', 'unable']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in error_indicators)
    
    def _clean_agent_artifacts(self, text: str) -> str:
        """Remove agent-specific artifacts from text."""
        # Remove tool call indicators and other artifacts
        cleaned = re.sub(r'<function_calls>.*?</function_calls>', '', text, flags=re.DOTALL)
        cleaned = re.sub(r'<.*?>', '', cleaned)
        
        # Clean up multiple newlines
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        
        return cleaned.strip()
    
    @contextmanager
    def progress_indicator(self, description: str):
        """Show progress indicator during long operations."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task(description, total=None)
            try:
                yield progress
            finally:
                progress.remove_task(task)
    
    def format_tool_result(self, tool_name: str, result: str, show_details: bool = True) -> None:
        """Format tool execution results."""
        if show_details:
            self.console.print(f"[dim]🔧 {tool_name}[/dim]")
        
        # Format different types of tool results
        if tool_name.startswith('git_'):
            self._format_git_result(result)
        elif tool_name.startswith('fs_') or 'file' in tool_name.lower():
            self._format_file_result(result)
        else:
            self.console.print(result)
    
    def _format_git_result(self, result: str) -> None:
        """Format git command results."""
        lines = result.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.startswith('✅'):
                formatted_lines.append(f"[green]{line}[/green]")
            elif line.startswith('❌'):
                formatted_lines.append(f"[red]{line}[/red]")
            elif line.startswith('🌿'):
                formatted_lines.append(f"[blue]{line}[/blue]")
            elif line.startswith('📦'):
                formatted_lines.append(f"[yellow]{line}[/yellow]")
            else:
                formatted_lines.append(line)
        
        self.console.print('\n'.join(formatted_lines))
    
    def _format_file_result(self, result: str) -> None:
        """Format file operation results."""
        if '→' in result and result.count('\n') > 5:
            # This looks like a file with line numbers
            self.console.print(Panel(
                result, 
                title="📄 File Content",
                border_style="blue",
                expand=False
            ))
        else:
            self.console.print(result)