"""
Persistent Memory System

SQLite-based persistent memory with FTS5 full-text search.
Inspired by Hermes Agent's memory architecture.

Features:
- Cross-session conversation persistence
- FTS5 full-text search across all memories
- User preference learning (USER.md equivalent)
- Vehicle state memory (last known state)
- Automatic memory pruning and summarization
"""

import json
import sqlite3
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: Optional[int] = None
    session_id: str = ""
    user_id: str = ""
    role: str = ""  # user, assistant, system, tool
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    importance: float = 0.5  # 0.0-1.0, higher = more important


@dataclass
class UserPreference:
    """Learned user preference."""
    key: str
    value: str
    confidence: float = 1.0
    learned_at: str = ""
    examples: List[str] = field(default_factory=list)


class PersistentMemory:
    """
    SQLite-based persistent memory with FTS5 full-text search.
    
    Architecture (following Hermes Agent patterns):
    - conversations table: full conversation history
    - memories FTS5 table: searchable memory fragments
    - user_preferences table: learned preferences
    - vehicle_state table: cached vehicle state snapshots
    - skills table: auto-learned skill definitions
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize persistent memory.
        
        Args:
            db_path: Path to SQLite database. Defaults to ~/.xclaw/memory.db
        """
        if db_path is None:
            home = Path.home()
            db_path = str(home / ".xclaw" / "memory.db")
        
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        self._conn.executescript("""
            -- Conversation history
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                importance REAL DEFAULT 0.5,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);
            CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_conv_created ON conversations(created_at);
            
            -- FTS5 full-text search for memories
            CREATE VIRTUAL TABLE IF NOT EXISTS memories USING fts5(
                content,
                tags,
                user_id,
                session_id,
                importance,
                created_at,
                tokenize='unicode61'
            );
            
            -- User preferences (learned from conversations)
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                examples TEXT DEFAULT '[]',
                learned_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, key)
            );
            
            -- Vehicle state snapshots
            CREATE TABLE IF NOT EXISTS vehicle_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vin TEXT NOT NULL,
                state_json TEXT NOT NULL,
                snapshot_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_vstate_vin ON vehicle_state(vin);
            CREATE INDEX IF NOT EXISTS idx_vstate_time ON vehicle_state(snapshot_at);
            
            -- Auto-learned skills
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                trigger_patterns TEXT NOT NULL DEFAULT '[]',
                tool_sequence TEXT NOT NULL DEFAULT '[]',
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            
            -- Audit log for safety
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                parameters TEXT DEFAULT '{}',
                result TEXT,
                risk_level TEXT DEFAULT 'low',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
            CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(created_at);
            
            -- Scheduled tasks
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                cron_expr TEXT,
                trigger_type TEXT NOT NULL DEFAULT 'cron',
                trigger_config TEXT DEFAULT '{}',
                action_type TEXT NOT NULL,
                action_config TEXT NOT NULL DEFAULT '{}',
                enabled INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        self._conn.commit()
    
    # ==================== Conversation History ====================
    
    def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
        importance: float = 0.5,
    ) -> int:
        """Add a message to conversation history."""
        cursor = self._conn.execute(
            """INSERT INTO conversations (session_id, user_id, role, content, metadata, importance)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, role, content, json.dumps(metadata or {}), importance)
        )
        self._conn.commit()
        return cursor.lastrowid
    
    def get_conversation(
        self,
        session_id: str,
        limit: int = 20,
        include_system: bool = False,
    ) -> List[Dict[str, str]]:
        """Get recent conversation messages for LLM context."""
        query = """
            SELECT role, content, metadata, created_at
            FROM conversations
            WHERE session_id = ?
        """
        params = [session_id]
        
        if not include_system:
            query += " AND role != 'system'"
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = self._conn.execute(query, params).fetchall()
        messages = []
        for row in reversed(rows):
            msg = {"role": row["role"], "content": row["content"]}
            meta = json.loads(row["metadata"])
            if "tool_call_id" in meta:
                msg["tool_call_id"] = meta["tool_call_id"]
            if "tool_calls" in meta:
                msg["tool_calls"] = meta["tool_calls"]
            messages.append(msg)
        
        return messages
    
    def get_user_history(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[Dict]:
        """Get all conversation history for a user across sessions."""
        rows = self._conn.execute(
            """SELECT session_id, role, content, created_at
               FROM conversations
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return [dict(row) for row in rows]
    
    # ==================== Memory Search (FTS5) ====================
    
    def store_memory(
        self,
        content: str,
        user_id: str = "",
        session_id: str = "",
        tags: List[str] = None,
        importance: float = 0.5,
    ):
        """Store a searchable memory fragment."""
        self._conn.execute(
            """INSERT INTO memories (content, tags, user_id, session_id, importance, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (content, ",".join(tags or []), user_id, session_id, importance,
             datetime.utcnow().isoformat())
        )
        self._conn.commit()
    
    def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search memories using FTS5 full-text search."""
        sql = """
            SELECT content, tags, user_id, session_id, importance, created_at,
                   rank
            FROM memories
            WHERE memories MATCH ?
        """
        params = [query]
        
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        
        try:
            rows = self._conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            return []
    
    # ==================== User Preferences ====================
    
    def set_preference(
        self,
        user_id: str,
        key: str,
        value: str,
        confidence: float = 1.0,
        examples: List[str] = None,
    ):
        """Store or update a user preference."""
        self._conn.execute(
            """INSERT INTO user_preferences (user_id, key, value, confidence, examples, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, key) DO UPDATE SET
                 value = excluded.value,
                 confidence = excluded.confidence,
                 examples = excluded.examples,
                 updated_at = excluded.updated_at""",
            (user_id, key, value, confidence, json.dumps(examples or []),
             datetime.utcnow().isoformat())
        )
        self._conn.commit()
    
    def get_preferences(self, user_id: str) -> Dict[str, str]:
        """Get all preferences for a user."""
        rows = self._conn.execute(
            "SELECT key, value, confidence FROM user_preferences WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return {row["key"]: row["value"] for row in rows if row["confidence"] > 0.3}
    
    def get_preference(self, user_id: str, key: str) -> Optional[str]:
        """Get a specific preference."""
        row = self._conn.execute(
            "SELECT value FROM user_preferences WHERE user_id = ? AND key = ?",
            (user_id, key)
        ).fetchone()
        return row["value"] if row else None
    
    # ==================== Vehicle State ====================
    
    def save_vehicle_state(self, vin: str, state: Dict[str, Any]):
        """Save a vehicle state snapshot."""
        self._conn.execute(
            "INSERT INTO vehicle_state (vin, state_json) VALUES (?, ?)",
            (vin, json.dumps(state))
        )
        self._conn.commit()
    
    def get_last_vehicle_state(self, vin: str) -> Optional[Dict]:
        """Get the most recent vehicle state snapshot."""
        row = self._conn.execute(
            """SELECT state_json, snapshot_at FROM vehicle_state
               WHERE vin = ? ORDER BY snapshot_at DESC LIMIT 1""",
            (vin,)
        ).fetchone()
        if row:
            state = json.loads(row["state_json"])
            state["_snapshot_at"] = row["snapshot_at"]
            return state
        return None
    
    def get_vehicle_state_history(
        self,
        vin: str,
        hours: int = 24,
    ) -> List[Dict]:
        """Get vehicle state history."""
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        rows = self._conn.execute(
            """SELECT state_json, snapshot_at FROM vehicle_state
               WHERE vin = ? AND snapshot_at >= ?
               ORDER BY snapshot_at DESC""",
            (vin, since)
        ).fetchall()
        return [
            {**json.loads(row["state_json"]), "_snapshot_at": row["snapshot_at"]}
            for row in rows
        ]
    
    # ==================== Skills ====================
    
    def store_skill(
        self,
        name: str,
        description: str,
        trigger_patterns: List[str],
        tool_sequence: List[Dict],
    ):
        """Store an auto-learned skill."""
        self._conn.execute(
            """INSERT INTO skills (name, description, trigger_patterns, tool_sequence)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                 description = excluded.description,
                 trigger_patterns = excluded.trigger_patterns,
                 tool_sequence = excluded.tool_sequence,
                 updated_at = datetime('now')""",
            (name, description, json.dumps(trigger_patterns), json.dumps(tool_sequence))
        )
        self._conn.commit()
    
    def find_matching_skills(self, user_message: str) -> List[Dict]:
        """Find skills that match the user's message."""
        rows = self._conn.execute(
            "SELECT name, description, trigger_patterns, tool_sequence, success_count FROM skills"
        ).fetchall()
        
        matches = []
        msg_lower = user_message.lower()
        for row in rows:
            patterns = json.loads(row["trigger_patterns"])
            for pattern in patterns:
                if pattern.lower() in msg_lower:
                    matches.append({
                        "name": row["name"],
                        "description": row["description"],
                        "tool_sequence": json.loads(row["tool_sequence"]),
                        "success_count": row["success_count"],
                    })
                    break
        
        return sorted(matches, key=lambda x: x["success_count"], reverse=True)
    
    def record_skill_usage(self, name: str, success: bool):
        """Record skill usage outcome."""
        col = "success_count" if success else "failure_count"
        self._conn.execute(
            f"UPDATE skills SET {col} = {col} + 1, updated_at = datetime('now') WHERE name = ?",
            (name,)
        )
        self._conn.commit()
    
    # ==================== Audit Log ====================
    
    def log_audit(
        self,
        user_id: str,
        action: str,
        target: str = "",
        parameters: Dict = None,
        result: str = "",
        risk_level: str = "low",
    ):
        """Log an audit entry."""
        self._conn.execute(
            """INSERT INTO audit_log (user_id, action, target, parameters, result, risk_level)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, action, target, json.dumps(parameters or {}), result, risk_level)
        )
        self._conn.commit()
    
    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Dict]:
        """Get audit log entries."""
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        query = "SELECT * FROM audit_log WHERE created_at >= ?"
        params = [since]
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if action:
            query += " AND action = ?"
            params.append(action)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = self._conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    # ==================== Scheduled Tasks ====================
    
    def create_scheduled_task(
        self,
        user_id: str,
        name: str,
        action_type: str,
        action_config: Dict,
        description: str = "",
        trigger_type: str = "cron",
        trigger_config: Dict = None,
        cron_expr: str = "",
    ) -> int:
        """Create a scheduled task."""
        cursor = self._conn.execute(
            """INSERT INTO scheduled_tasks
               (user_id, name, description, cron_expr, trigger_type, trigger_config, action_type, action_config)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, name, description, cron_expr, trigger_type,
             json.dumps(trigger_config or {}), action_type, json.dumps(action_config))
        )
        self._conn.commit()
        return cursor.lastrowid
    
    def get_due_tasks(self) -> List[Dict]:
        """Get tasks that are due to run."""
        now = datetime.utcnow().isoformat()
        rows = self._conn.execute(
            """SELECT * FROM scheduled_tasks
               WHERE enabled = 1 AND (next_run IS NULL OR next_run <= ?)
               ORDER BY created_at""",
            (now,)
        ).fetchall()
        return [dict(row) for row in rows]
    
    def update_task_run(self, task_id: int, next_run: Optional[str] = None):
        """Update task last run time and next run time."""
        self._conn.execute(
            """UPDATE scheduled_tasks
               SET last_run = datetime('now'), next_run = ?
               WHERE id = ?""",
            (next_run, task_id)
        )
        self._conn.commit()
    
    def get_user_tasks(self, user_id: str) -> List[Dict]:
        """Get all tasks for a user."""
        rows = self._conn.execute(
            "SELECT * FROM scheduled_tasks WHERE user_id = ? ORDER BY created_at",
            (user_id,)
        ).fetchall()
        return [dict(row) for row in rows]
    
    # ==================== Context Compression ====================
    
    def compress_old_conversations(
        self,
        session_id: str,
        keep_recent: int = 10,
        summary: str = "",
    ):
        """Mark old conversations as compressed and store summary."""
        if summary:
            self.store_memory(
                content=summary,
                session_id=session_id,
                tags=["compressed_summary"],
                importance=0.8,
            )
    
    # ==================== Maintenance ====================
    
    def prune_old_data(self, days: int = 90):
        """Prune data older than specified days."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        self._conn.execute(
            "DELETE FROM conversations WHERE created_at < ?", (cutoff,)
        )
        self._conn.execute(
            "DELETE FROM vehicle_state WHERE snapshot_at < ?", (cutoff,)
        )
        self._conn.commit()
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory statistics."""
        stats = {}
        for table in ["conversations", "memories", "user_preferences",
                       "vehicle_state", "skills", "audit_log", "scheduled_tasks"]:
            try:
                row = self._conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
                stats[table] = row["cnt"]
            except sqlite3.OperationalError:
                stats[table] = 0
        return stats
    
    def close(self):
        """Close database connection."""
        self._conn.close()
