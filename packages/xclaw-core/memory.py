"""
Conversation Memory

Manages conversation history for the AI agent.
"""

from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Conversation:
    """A conversation with a user."""
    messages: List[Dict[str, str]] = field(default_factory=list)
    max_messages: int = 50
    
    def add_user_message(self, content: str):
        """Add a user message."""
        self.messages.append({"role": "user", "content": content})
        self._trim()
    
    def add_assistant_message(self, content: str):
        """Add an assistant message."""
        self.messages.append({"role": "assistant", "content": content})
        self._trim()
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get recent messages."""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def clear(self):
        """Clear conversation."""
        self.messages = []
    
    def _trim(self):
        """Trim conversation to max size."""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]


class ConversationMemory:
    """
    In-memory conversation storage.
    
    For production, this should be replaced with Redis or database storage.
    """
    
    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}
        self._default_conversation = Conversation()
    
    def add_user_message(self, content: str, user_id: Optional[str] = None):
        """Add a user message."""
        conv = self._get_conversation(user_id)
        conv.add_user_message(content)
    
    def add_assistant_message(self, content: str, user_id: Optional[str] = None):
        """Add an assistant message."""
        conv = self._get_conversation(user_id)
        conv.add_assistant_message(content)
    
    def get_messages(
        self,
        user_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Get conversation messages."""
        conv = self._get_conversation(user_id)
        return conv.get_messages(limit)
    
    def clear(self, user_id: Optional[str] = None):
        """Clear conversation."""
        if user_id:
            self._conversations.pop(user_id, None)
        else:
            self._default_conversation.clear()
    
    def _get_conversation(self, user_id: Optional[str] = None) -> Conversation:
        """Get or create conversation."""
        if user_id is None:
            return self._default_conversation
        
        if user_id not in self._conversations:
            self._conversations[user_id] = Conversation()
        return self._conversations[user_id]
