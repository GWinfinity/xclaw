"""
Context Compression

Compresses old conversation context to stay within token limits.
Inspired by Hermes Agent's context compression system.
"""

import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class CompressionConfig:
    """Configuration for context compression."""
    max_tokens: int = 8000
    keep_recent_messages: int = 10
    summarize_threshold: int = 20
    summary_max_tokens: int = 500


class ContextCompressor:
    """
    Compresses conversation context to stay within token limits.
    
    Strategies:
    1. Keep recent messages intact
    2. Summarize older messages using LLM
    3. Preserve important context (tool calls, errors)
    4. Store compressed summaries in memory
    """
    
    def __init__(self, config: Optional[CompressionConfig] = None):
        self.config = config or CompressionConfig()
    
    def estimate_tokens(self, messages: List[Dict]) -> int:
        """Estimate token count for messages."""
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            # Rough estimate: 1 token ≈ 2 chars for Chinese, 4 chars for English
        return total_chars // 2
    
    def needs_compression(self, messages: List[Dict]) -> bool:
        """Check if messages need compression."""
        if len(messages) > self.config.summarize_threshold:
            return True
        if self.estimate_tokens(messages) > self.config.max_tokens:
            return True
        return False
    
    def compress(
        self,
        messages: List[Dict],
        summary: Optional[str] = None,
    ) -> List[Dict]:
        """
        Compress messages by summarizing older ones.
        
        Args:
            messages: Full message list
            summary: Optional pre-generated summary
            
        Returns:
            Compressed message list
        """
        if not self.needs_compression(messages):
            return messages
        
        keep_recent = self.config.keep_recent_messages
        
        # Split into old and recent
        old_messages = messages[:-keep_recent]
        recent_messages = messages[-keep_recent:]
        
        # Create summary of old messages
        if summary is None:
            summary = self._create_summary(old_messages)
        
        # Build compressed messages
        compressed = []
        
        if summary:
            compressed.append({
                "role": "system",
                "content": f"[之前的对话摘要] {summary}"
            })
        
        # Preserve any tool call context from old messages
        tool_context = self._extract_tool_context(old_messages)
        if tool_context:
            compressed.append({
                "role": "system",
                "content": f"[工具调用历史] {tool_context}"
            })
        
        compressed.extend(recent_messages)
        
        logger.info(
            "context_compressed",
            original_count=len(messages),
            compressed_count=len(compressed),
            summary_length=len(summary) if summary else 0,
        )
        
        return compressed
    
    def _create_summary(self, messages: List[Dict]) -> str:
        """Create a summary of messages."""
        if not messages:
            return ""
        
        # Extract key information
        user_messages = []
        assistant_messages = []
        tool_calls = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user" and content:
                user_messages.append(content)
            elif role == "assistant" and content:
                assistant_messages.append(content)
            elif role == "tool":
                tool_calls.append(content)
        
        # Build summary
        summary_parts = []
        
        if user_messages:
            summary_parts.append(f"用户提到了: {'; '.join(user_messages[-3:])}")
        
        if tool_calls:
            summary_parts.append(f"执行了 {len(tool_calls)} 次工具调用")
        
        return " | ".join(summary_parts)
    
    def _extract_tool_context(self, messages: List[Dict]) -> str:
        """Extract important tool call context from messages."""
        tool_results = []
        
        for msg in messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                if content:
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict):
                            # Extract key fields
                            key_fields = {
                                k: v for k, v in data.items()
                                if k in ("success", "error", "battery_level",
                                         "charging_state", "locked", "sentry_mode")
                            }
                            if key_fields:
                                tool_results.append(json.dumps(key_fields))
                    except json.JSONDecodeError:
                        pass
        
        if tool_results:
            return "; ".join(tool_results[-5:])  # Keep last 5
        return ""
    
    def extract_important_context(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        Extract important context that should be preserved.
        
        Returns:
            Dictionary of important context
        """
        context = {
            "vehicle_state": None,
            "recent_actions": [],
            "user_preferences": {},
        }
        
        for msg in messages:
            if msg.get("role") == "tool":
                try:
                    data = json.loads(msg.get("content", "{}"))
                    if "battery_level" in data:
                        context["vehicle_state"] = data
                except json.JSONDecodeError:
                    pass
            
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                # Extract preferences
                if "温度" in content:
                    context["user_preferences"]["temperature_mentioned"] = True
                if "充电" in content:
                    context["user_preferences"]["charging_mentioned"] = True
        
        return context
