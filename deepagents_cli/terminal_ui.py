"""
DeepAgents Terminal UI that exactly matches Claude Code

Features:
- Persistent status bar at bottom
- Text entry above status bar  
- Autocomplete menu between entry and status
- No reprinting of UI elements
"""
import os
import sys
import threading
import time
import termios
import tty
from typing import List, Optional
from deepagents_cli.agent.status_line import get_status_line
from deepagents_cli.agent.autocomplete import get_matching_commands, COMMANDS

class TerminalUI:
    """Terminal UI that matches Claude Code exactly."""
    
    def __init__(self):
        self.width = os.get_terminal_size().columns
        self.height = os.get_terminal_size().rows
        self.input_line = ""
        self.cursor_pos = 0
        self.conversation_lines = []
        self.autocomplete_visible = False
        self.autocomplete_options = []
        self.running = False
        
    def clear_screen(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="")
        
    def move_cursor(self, row, col):
        """Move cursor to specific position."""
        print(f"\033[{row};{col}H", end="")
        
    def save_cursor(self):
        """Save cursor position."""
        print("\033[s", end="")
        
    def restore_cursor(self):
        """Restore cursor position."""
        print("\033[u", end="")
        
    def hide_cursor(self):
        """Hide the cursor."""
        print("\033[?25l", end="")
        
    def show_cursor(self):
        """Show the cursor."""
        print("\033[?25h", end="")
        
    def clear_line(self, row):
        """Clear a specific line."""
        self.move_cursor(row, 1)
        print("\033[K", end="")
        
    def draw_status_bar(self):
        """Draw the persistent status bar at bottom."""
        status_text = get_status_line()
        status_row = self.height
        
        # Clear the status line
        self.clear_line(status_row)
        
        # Draw status bar (truncate if too long)
        if len(status_text) > self.width - 4:
            status_text = status_text[:self.width - 7] + "..."
            
        self.move_cursor(status_row, 1)
        print(f"\033[46m {status_text:<{self.width-2}} \033[0m", end="")
        
    def draw_input_area(self):
        """Draw the input area above status bar."""
        input_row = self.height - 2  # Leave space for status bar
        
        # Clear input line
        self.clear_line(input_row)
        
        # Draw input prompt and text
        self.move_cursor(input_row, 1)
        prompt = "You: "
        display_text = self.input_line
        
        # Truncate if too long
        available_width = self.width - len(prompt) - 2
        if len(display_text) > available_width:
            start_pos = max(0, self.cursor_pos - available_width + 10)
            display_text = display_text[start_pos:start_pos + available_width]
            
        print(f"\033[33m{prompt}\033[0m{display_text}", end="")
        
        # Position cursor
        cursor_col = len(prompt) + min(self.cursor_pos, available_width) + 1
        self.move_cursor(input_row, cursor_col)
        
    def draw_autocomplete(self):
        """Draw autocomplete menu between input and status."""
        if not self.autocomplete_visible or not self.autocomplete_options:
            return
            
        # Start from row above input area
        start_row = self.height - 3 - len(self.autocomplete_options)
        
        # Ensure we don't go above conversation area
        if start_row < 1:
            start_row = 1
            
        for i, (cmd, desc) in enumerate(self.autocomplete_options[:10]):  # Max 10 options
            row = start_row + i
            if row >= self.height - 2:  # Don't overlap input area
                break
                
            self.clear_line(row)
            self.move_cursor(row, 1)
            
            # Format command option
            cmd_text = f"/{cmd}"
            if len(cmd_text) > 15:
                cmd_text = cmd_text[:12] + "..."
                
            desc_text = desc
            available_desc_width = self.width - 18
            if len(desc_text) > available_desc_width:
                desc_text = desc_text[:available_desc_width - 3] + "..."
                
            print(f"\033[42m {cmd_text:<15} \033[0m {desc_text}", end="")
            
    def clear_autocomplete(self):
        """Clear the autocomplete area."""
        if not self.autocomplete_visible:
            return
            
        # Clear lines where autocomplete was shown
        start_row = max(1, self.height - 3 - 10)  # Max 10 options
        for row in range(start_row, self.height - 2):
            self.clear_line(row)
            
        self.autocomplete_visible = False
        self.autocomplete_options = []
        
    def update_autocomplete(self):
        """Update autocomplete based on current input."""
        if self.input_line.startswith('/'):
            command_part = self.input_line[1:]  # Remove leading /
            
            # Get matching commands
            matches = []
            for cmd, desc in COMMANDS.items():
                if cmd.startswith(command_part.lower()):
                    matches.append((cmd, desc))
                    
            if matches and (not command_part or len(matches) > 1 or command_part not in COMMANDS):
                self.autocomplete_visible = True
                self.autocomplete_options = matches[:10]  # Limit to 10
            else:
                self.clear_autocomplete()
        else:
            self.clear_autocomplete()
            
    def draw_conversation(self):
        """Draw conversation area."""
        # Conversation takes up most of the screen
        conversation_height = self.height - 4  # Leave room for input and status
        
        # Clear conversation area
        for row in range(1, conversation_height + 1):
            self.clear_line(row)
            
        # Show recent messages
        display_lines = self.conversation_lines[-(conversation_height - 2):] if len(self.conversation_lines) > conversation_height - 2 else self.conversation_lines
        
        for i, line in enumerate(display_lines):
            if i >= conversation_height - 2:
                break
            row = i + 1
            self.move_cursor(row, 1)
            # Truncate long lines
            if len(line) > self.width - 2:
                line = line[:self.width - 5] + "..."
            print(line, end="")
            
    def add_conversation_line(self, text: str, sender: str = "system"):
        """Add a line to the conversation."""
        if sender == "user":
            formatted = f"\033[33mYou:\033[0m {text}"
        elif sender == "assistant":
            formatted = f"\033[37mDeepAgents:\033[0m {text}"
        else:
            formatted = text
            
        # Split long lines
        max_width = self.width - 2
        if len(formatted) > max_width:
            words = formatted.split()
            current_line = ""
            for word in words:
                if len(current_line + " " + word) <= max_width:
                    current_line += (" " if current_line else "") + word
                else:
                    if current_line:
                        self.conversation_lines.append(current_line)
                    current_line = word
            if current_line:
                self.conversation_lines.append(current_line)
        else:
            self.conversation_lines.append(formatted)
            
        # Keep conversation manageable
        if len(self.conversation_lines) > 1000:
            self.conversation_lines = self.conversation_lines[-500:]
            
    def refresh_display(self):
        """Refresh the entire display."""
        self.draw_conversation()
        self.draw_autocomplete()
        self.draw_input_area()
        self.draw_status_bar()
        sys.stdout.flush()
        
    def start_status_updates(self):
        """Start background thread to update status bar."""
        def update_loop():
            while self.running:
                self.save_cursor()
                self.draw_status_bar()
                self.restore_cursor()
                sys.stdout.flush()
                time.sleep(1)
                
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        
    def get_char(self):
        """Get a single character from input."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char
        
    def handle_input(self) -> Optional[str]:
        """Handle character input and return complete line when Enter is pressed."""
        while True:
            char = self.get_char()
            
            if ord(char) == 3:  # Ctrl+C
                raise KeyboardInterrupt
            elif ord(char) == 4:  # Ctrl+D (EOF)
                raise EOFError
            elif ord(char) == 13:  # Enter
                result = self.input_line
                self.input_line = ""
                self.cursor_pos = 0
                self.clear_autocomplete()
                return result
            elif ord(char) == 127 or ord(char) == 8:  # Backspace
                if self.cursor_pos > 0:
                    self.input_line = self.input_line[:self.cursor_pos-1] + self.input_line[self.cursor_pos:]
                    self.cursor_pos -= 1
                    self.update_autocomplete()
                    self.refresh_display()
            elif ord(char) == 27:  # Escape sequence (arrow keys, etc.)
                next_char = self.get_char()
                if next_char == '[':
                    arrow = self.get_char()
                    if arrow == 'D':  # Left arrow
                        if self.cursor_pos > 0:
                            self.cursor_pos -= 1
                            self.draw_input_area()
                    elif arrow == 'C':  # Right arrow
                        if self.cursor_pos < len(self.input_line):
                            self.cursor_pos += 1
                            self.draw_input_area()
            elif ord(char) >= 32 and ord(char) <= 126:  # Printable characters
                self.input_line = self.input_line[:self.cursor_pos] + char + self.input_line[self.cursor_pos:]
                self.cursor_pos += 1
                self.update_autocomplete()
                self.refresh_display()
                
    def start(self):
        """Start the terminal UI."""
        self.running = True
        
        # Setup terminal
        self.clear_screen()
        self.hide_cursor()
        
        # Initial display
        self.add_conversation_line("🧠 DeepAgents CLI — type :help for commands.", "system")
        self.add_conversation_line("(Your text is yellow, DeepAgents responses are white)", "system")
        
        # Start status updates
        self.start_status_updates()
        
        try:
            self.refresh_display()
            self.show_cursor()
            
            while self.running:
                user_input = self.handle_input()
                if user_input is not None:
                    yield user_input
                    # Add user input to conversation
                    self.add_conversation_line(user_input, "user")
                    self.refresh_display()
                    
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self.stop()
            
    def add_response(self, response: str):
        """Add assistant response to conversation."""
        self.add_conversation_line(response, "assistant")
        self.refresh_display()
        
    def stop(self):
        """Stop the terminal UI."""
        self.running = False
        self.show_cursor()
        self.clear_screen()
        print("Goodbye.")


# Global UI instance
terminal_ui = TerminalUI()