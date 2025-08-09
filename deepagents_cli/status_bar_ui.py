"""
Simple persistent status bar for DeepAgents CLI
"""
import os
import sys
import threading
import time
from deepagents_cli.agent.status_line import get_status_line


class PersistentStatusBar:
    """Simple persistent status bar using terminal positioning."""
    
    def __init__(self):
        self.running = False
        self.last_status = ""
        
    def get_terminal_height(self) -> int:
        """Get terminal height."""
        try:
            return os.get_terminal_size().rows
        except:
            return 24  # Default
            
    def move_to_bottom(self):
        """Move cursor to bottom line."""
        height = self.get_terminal_height()
        sys.stdout.write(f"\033[{height};1H")
        sys.stdout.flush()
        
    def clear_bottom_line(self):
        """Clear the bottom line."""
        self.move_to_bottom()
        sys.stdout.write("\033[K")  # Clear to end of line
        sys.stdout.flush()
        
    def draw_status_bar(self):
        """Draw the status bar at bottom."""
        status_text = get_status_line()
        
        # Only update if status changed
        if status_text != self.last_status:
            self.clear_bottom_line()
            
            # Draw status with background color
            sys.stdout.write(f"\033[44m {status_text} \033[0m")
            sys.stdout.flush()
            
            self.last_status = status_text
            
    def start_updates(self):
        """Start background status updates."""
        self.running = True
        
        def update_loop():
            while self.running:
                # Save cursor position
                sys.stdout.write("\033[s")
                
                # Update status bar
                self.draw_status_bar()
                
                # Restore cursor position
                sys.stdout.write("\033[u")
                sys.stdout.flush()
                
                time.sleep(1)
                
        threading.Thread(target=update_loop, daemon=True).start()
        
    def stop(self):
        """Stop status updates."""
        self.running = False
        self.clear_bottom_line()


# Global instance
status_bar = PersistentStatusBar()


def start_status_bar():
    """Start the persistent status bar."""
    status_bar.start_updates()


def stop_status_bar():
    """Stop the persistent status bar."""
    status_bar.stop()