"""
Safety and stability controls for DeepAgents CLI.
"""
import time
import threading
from typing import Dict, List, Any
from functools import wraps


class ConversationSafety:
    """Safety mechanisms to prevent runaway conversations."""
    
    def __init__(self):
        self.max_turns_per_minute = 10
        self.max_tool_calls_per_turn = 5
        self.max_response_length = 5000
        self.turn_history: List[Dict] = []
        self.current_tool_calls = 0
        
    def reset_turn(self):
        """Reset counters for new conversation turn."""
        self.current_tool_calls = 0
        
    def check_rate_limit(self) -> bool:
        """Check if we're exceeding conversation rate limits."""
        now = time.time()
        # Remove turns older than 1 minute
        self.turn_history = [
            turn for turn in self.turn_history 
            if now - turn['timestamp'] < 60
        ]
        
        if len(self.turn_history) >= self.max_turns_per_minute:
            return False
        return True
        
    def record_turn(self):
        """Record a conversation turn."""
        self.turn_history.append({
            'timestamp': time.time(),
            'tool_calls': self.current_tool_calls
        })
        
    def check_tool_limit(self) -> bool:
        """Check if we've exceeded tool call limit for this turn."""
        return self.current_tool_calls < self.max_tool_calls_per_turn
        
    def increment_tool_calls(self):
        """Increment tool call counter."""
        self.current_tool_calls += 1


# Global safety instance
safety = ConversationSafety()


def safe_tool(func):
    """Decorator to add safety checks to tool calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not safety.check_tool_limit():
            return "⚠️ Tool call limit reached for this turn. Please try a simpler request."
        
        safety.increment_tool_calls()
        
        try:
            result = func(*args, **kwargs)
            # Truncate very long results
            if isinstance(result, str) and len(result) > safety.max_response_length:
                result = result[:safety.max_response_length] + "\n\n⚠️ Output truncated for safety."
            return result
        except Exception as e:
            return f"⚠️ Tool error: {str(e)}"
    
    return wrapper


class ContextLoader:
    """Intelligently load project context when given a folder."""
    
    @staticmethod
    def analyze_folder(path: str) -> str:
        """Analyze a folder and provide intelligent context using unrestricted tools."""
        # Import the unrestricted tools
        from .claude_file_tools import list_directory_unrestricted, read_file_unrestricted
        
        # Use unrestricted directory listing 
        dir_listing = list_directory_unrestricted(path, show_hidden=False, max_items=20)
        
        if dir_listing.startswith("Directory not found") or dir_listing.startswith("Not a directory"):
            return f"❌ {dir_listing}"
        
        analysis = []
        analysis.append(f"📁 **Intelligent Project Analysis**\n")
        
        # Show directory structure
        analysis.append(dir_listing)
        analysis.append("")
        
        # Try to read README file if it exists
        from pathlib import Path
        folder_path = Path(path)
        
        readme_files = ['README.md', 'README.txt', 'README.rst', 'readme.md', 'Readme.md']
        for readme_name in readme_files:
            readme_path = folder_path / readme_name
            if readme_path.exists():
                analysis.append("📖 **README Found - Let me read it:**")
                readme_content = read_file_unrestricted(str(readme_path), end_line=50)  # First 50 lines
                analysis.append(readme_content[:1000] + "..." if len(readme_content) > 1000 else readme_content)
                break
        
        analysis.append(f"\n💡 **I now have full access to analyze this project:**")
        analysis.append("  • Read any file with complete context")
        analysis.append("  • Search across the entire codebase") 
        analysis.append("  • Execute commands for analysis or testing")
        analysis.append("  • Provide detailed architectural insights")
        analysis.append("  • Generate documentation or refactor code")
        
        analysis.append(f"\n🎯 **What specific aspect would you like me to examine?**")
        
        return "\n".join(analysis)


def create_emergency_prompt() -> str:
    """Create a safety-focused system prompt."""
    return """You are DeepAgents, a helpful AI coding assistant. 

CRITICAL SAFETY RULES:
1. Be concise and focused - avoid long, rambling responses
2. Ask clarifying questions if requests are unclear
3. Use tools sparingly - max 3 tool calls per response
4. If a tool fails, don't retry endlessly - explain and suggest alternatives
5. When given a folder path, use the ContextLoader to analyze it intelligently

CONVERSATION STYLE:
- Be helpful but brief
- Ask "What would you like me to do?" if unclear
- Provide actionable suggestions
- Focus on the user's immediate need

Remember: Quality over quantity. Better to give a focused, helpful response than overwhelm the user."""