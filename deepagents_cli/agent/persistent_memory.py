"""
Persistent Memory System for DeepAgents CLI.
Remembers conversations, context, and user patterns across sessions.
"""
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""
    timestamp: datetime
    user_input: str
    ai_response: str
    context: Dict[str, Any]
    session_id: str


@dataclass
class ProjectContext:
    """Represents context about a specific project."""
    project_path: str
    project_name: str
    last_accessed: datetime
    key_files: List[str]
    project_type: str
    notes: List[str]
    decisions: List[str]


class PersistentMemory:
    """Manages persistent memory across DeepAgents sessions."""
    
    def __init__(self, memory_dir: str = None):
        if memory_dir is None:
            memory_dir = Path.home() / ".deepagents" / "memory"
        
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.memory_dir / "conversations.db"
        self.context_file = self.memory_dir / "project_contexts.json"
        self.preferences_file = self.memory_dir / "user_preferences.json"
        
        self.current_session_id = self._generate_session_id()
        self._init_database()
        
        # Load existing data
        self.project_contexts: Dict[str, ProjectContext] = self._load_project_contexts()
        self.user_preferences: Dict[str, Any] = self._load_user_preferences()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _init_database(self):
        """Initialize SQLite database for conversations."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    context_json TEXT,
                    project_path TEXT,
                    topic_hash TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON conversations(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_path 
                ON conversations(project_path)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topic_hash 
                ON conversations(topic_hash)
            """)
    
    def store_conversation_turn(self, user_input: str, ai_response: str, 
                              context: Dict[str, Any] = None) -> None:
        """Store a conversation turn in memory."""
        if context is None:
            context = {}
        
        # Extract project path if present
        project_path = None
        for path_candidate in [user_input, context.get("working_directory")]:
            if path_candidate and (
                path_candidate.startswith("C:") or 
                path_candidate.startswith("/") or 
                "CascadeProjects" in str(path_candidate)
            ):
                project_path = str(Path(path_candidate).resolve())
                break
        
        # Generate topic hash for grouping related conversations
        topic_hash = self._generate_topic_hash(user_input, ai_response)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversations 
                (session_id, timestamp, user_input, ai_response, context_json, project_path, topic_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.current_session_id,
                datetime.now().isoformat(),
                user_input,
                ai_response,
                json.dumps(context),
                project_path,
                topic_hash
            ))
    
    def _generate_topic_hash(self, user_input: str, ai_response: str) -> str:
        """Generate hash to group related conversation topics."""
        # Extract key terms for topic grouping
        combined_text = f"{user_input} {ai_response}".lower()
        
        # Common coding keywords for grouping
        keywords = [
            "auth", "login", "jwt", "token", "password", "security",
            "database", "sql", "query", "model", "schema",
            "api", "rest", "endpoint", "route", "middleware",
            "react", "component", "hook", "state", "props",
            "python", "django", "flask", "fastapi",
            "test", "unit", "integration", "mock",
            "deploy", "docker", "kubernetes", "ci", "cd"
        ]
        
        topic_words = []
        for keyword in keywords:
            if keyword in combined_text:
                topic_words.append(keyword)
        
        # Generate hash from topic words
        if topic_words:
            topic_string = "_".join(sorted(topic_words[:3]))  # Use top 3 keywords
            return hashlib.md5(topic_string.encode()).hexdigest()[:8]
        
        return "general"
    
    def get_conversation_history(self, limit: int = 10, 
                               project_path: str = None,
                               topic_hash: str = None,
                               days_back: int = 7) -> List[ConversationTurn]:
        """Retrieve conversation history with filters."""
        query = """
            SELECT session_id, timestamp, user_input, ai_response, context_json, project_path
            FROM conversations 
            WHERE timestamp > ?
        """
        params = [(datetime.now() - timedelta(days=days_back)).isoformat()]
        
        if project_path:
            query += " AND project_path = ?"
            params.append(project_path)
        
        if topic_hash:
            query += " AND topic_hash = ?"
            params.append(topic_hash)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        conversations = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                session_id, timestamp, user_input, ai_response, context_json, proj_path = row
                context = json.loads(context_json) if context_json else {}
                
                conversations.append(ConversationTurn(
                    timestamp=datetime.fromisoformat(timestamp),
                    user_input=user_input,
                    ai_response=ai_response,
                    context=context,
                    session_id=session_id
                ))
        
        return conversations
    
    def update_project_context(self, project_path: str, **updates) -> None:
        """Update context information for a project."""
        project_path = str(Path(project_path).resolve())
        
        if project_path not in self.project_contexts:
            self.project_contexts[project_path] = ProjectContext(
                project_path=project_path,
                project_name=Path(project_path).name,
                last_accessed=datetime.now(),
                key_files=[],
                project_type="unknown",
                notes=[],
                decisions=[]
            )
        
        context = self.project_contexts[project_path]
        context.last_accessed = datetime.now()
        
        # Update fields
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        self._save_project_contexts()
    
    def get_project_context(self, project_path: str) -> Optional[ProjectContext]:
        """Get context for a specific project."""
        project_path = str(Path(project_path).resolve())
        return self.project_contexts.get(project_path)
    
    def add_project_note(self, project_path: str, note: str) -> None:
        """Add a note about a project."""
        if project_path not in self.project_contexts:
            self.update_project_context(project_path)
        
        self.project_contexts[project_path].notes.append({
            "timestamp": datetime.now().isoformat(),
            "note": note
        })
        self._save_project_contexts()
    
    def add_project_decision(self, project_path: str, decision: str) -> None:
        """Record a decision made about a project."""
        if project_path not in self.project_contexts:
            self.update_project_context(project_path)
        
        self.project_contexts[project_path].decisions.append({
            "timestamp": datetime.now().isoformat(),
            "decision": decision
        })
        self._save_project_contexts()
    
    def learn_user_preference(self, category: str, preference: str, value: Any) -> None:
        """Learn and store user preferences."""
        if category not in self.user_preferences:
            self.user_preferences[category] = {}
        
        self.user_preferences[category][preference] = {
            "value": value,
            "learned_at": datetime.now().isoformat(),
            "confidence": 1.0
        }
        self._save_user_preferences()
    
    def extract_and_learn_user_info(self, user_input: str) -> None:
        """Extract and learn user information from conversations."""
        import re
        
        # Extract name patterns
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"i am (\w+)",
            r"call me (\w+)",
            r"this is (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                name = match.group(1).title()
                self.learn_user_preference("personal", "name", name)
                break
        
        # Extract other preferences
        if "i prefer" in user_input.lower():
            # Could extract coding preferences, tools, etc.
            pass
    
    def get_user_name(self) -> str:
        """Get the user's name if known."""
        return self.get_user_preference("personal", "name") or "there"
    
    def get_user_preference(self, category: str, preference: str) -> Any:
        """Get a user preference if it exists."""
        return self.user_preferences.get(category, {}).get(preference, {}).get("value")
    
    def get_contextual_memory_prompt(self, user_input: str = None, project_path: str = None) -> str:
        """Generate a memory context prompt for the AI."""
        memory_context = []
        
        # User identity
        user_name = self.get_user_name()
        if user_name != "there":
            memory_context.append(f"## 👤 User: {user_name}")
            memory_context.append("")
        
        # Recent conversation context - MORE DETAILED
        recent_conversations = self.get_conversation_history(limit=5, project_path=project_path)
        if recent_conversations:
            memory_context.append("## 📝 Recent Conversation Memory:")
            for i, conv in enumerate(reversed(recent_conversations), 1):
                time_str = conv.timestamp.strftime("%H:%M")
                memory_context.append(f"**{i}. [{time_str}] {user_name}**: {conv.user_input}")
                
                # Show key parts of AI response
                ai_summary = conv.ai_response
                if len(ai_summary) > 300:
                    # Extract key actions/decisions
                    if "created" in ai_summary.lower() or "wrote" in ai_summary.lower():
                        lines = ai_summary.split('\n')
                        key_lines = [line for line in lines if 
                                   any(word in line.lower() for word in ['created', 'wrote', 'generated', 'added', 'updated'])]
                        if key_lines:
                            ai_summary = '\n'.join(key_lines[:3])
                        else:
                            ai_summary = ai_summary[:300] + "..."
                
                memory_context.append(f"**AI Response**: {ai_summary}")
                memory_context.append("")
        
        # Files recently worked on
        recent_file_actions = self._extract_recent_file_actions(recent_conversations)
        if recent_file_actions:
            memory_context.append("## 📄 Files Recently Worked On:")
            for action in recent_file_actions:
                memory_context.append(f"  • {action}")
            memory_context.append("")
        
        # Project context if available
        if project_path:
            project_ctx = self.get_project_context(project_path)
            if project_ctx:
                memory_context.append(f"## 📁 Project Context: {project_ctx.project_name}")
                memory_context.append(f"**Type**: {project_ctx.project_type}")
                memory_context.append(f"**Last accessed**: {project_ctx.last_accessed.strftime('%Y-%m-%d %H:%M')}")
                
                if project_ctx.key_files:
                    memory_context.append(f"**Key files**: {', '.join(project_ctx.key_files[:5])}")
                
                if project_ctx.decisions:
                    memory_context.append("**Recent decisions**:")
                    for decision in project_ctx.decisions[-2:]:
                        memory_context.append(f"  • {decision['decision']}")
                
                memory_context.append("")
        
        # User preferences context
        personal_prefs = self.user_preferences.get("personal", {})
        coding_prefs = self.user_preferences.get("coding", {})
        
        if personal_prefs or coding_prefs:
            memory_context.append("## 🎯 What I Remember About You:")
            
            for pref_name, pref_data in personal_prefs.items():
                if pref_name != "name":  # Already shown above
                    memory_context.append(f"**{pref_name}**: {pref_data['value']}")
            
            for pref_name, pref_data in coding_prefs.items():
                memory_context.append(f"**{pref_name}**: {pref_data['value']}")
            memory_context.append("")
        
        if memory_context:
            return "\n".join(memory_context)
        
        return ""
    
    def _extract_recent_file_actions(self, conversations: List[ConversationTurn]) -> List[str]:
        """Extract recent file actions from conversations."""
        import re
        
        actions = []
        file_patterns = [
            r"created (\w+\.\w+)",
            r"wrote (\w+\.\w+)", 
            r"generated (\w+\.\w+)",
            r"added (\w+\.\w+)",
            r"updated (\w+\.\w+)",
            r"EnhancementPlan\.md",
            r"\w+\.py",
            r"\w+\.js", 
            r"\w+\.md"
        ]
        
        for conv in conversations[:3]:  # Look at last 3 conversations
            response = conv.ai_response.lower()
            
            # Look for file creation/modification
            for pattern in file_patterns:
                matches = re.findall(pattern, response)
                for match in matches:
                    if isinstance(match, str):
                        actions.append(f"Recently worked on: {match}")
            
            # Look for specific action phrases
            if "enhancement plan" in response:
                actions.append("Created EnhancementPlan.md")
            if "created" in response and "file" in response:
                actions.append("Created new project files")
        
        return list(set(actions))  # Remove duplicates
    
    def _load_project_contexts(self) -> Dict[str, ProjectContext]:
        """Load project contexts from file."""
        if not self.context_file.exists():
            return {}
        
        try:
            with open(self.context_file, 'r') as f:
                data = json.load(f)
            
            contexts = {}
            for path, ctx_data in data.items():
                contexts[path] = ProjectContext(
                    project_path=ctx_data["project_path"],
                    project_name=ctx_data["project_name"],
                    last_accessed=datetime.fromisoformat(ctx_data["last_accessed"]),
                    key_files=ctx_data.get("key_files", []),
                    project_type=ctx_data.get("project_type", "unknown"),
                    notes=ctx_data.get("notes", []),
                    decisions=ctx_data.get("decisions", [])
                )
            return contexts
        except Exception:
            return {}
    
    def _save_project_contexts(self) -> None:
        """Save project contexts to file."""
        data = {}
        for path, context in self.project_contexts.items():
            data[path] = {
                "project_path": context.project_path,
                "project_name": context.project_name,
                "last_accessed": context.last_accessed.isoformat(),
                "key_files": context.key_files,
                "project_type": context.project_type,
                "notes": context.notes,
                "decisions": context.decisions
            }
        
        with open(self.context_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences from file."""
        if not self.preferences_file.exists():
            return {}
        
        try:
            with open(self.preferences_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_user_preferences(self) -> None:
        """Save user preferences to file."""
        with open(self.preferences_file, 'w') as f:
            json.dump(self.user_preferences, f, indent=2)


# Global memory instance
memory_system = PersistentMemory()