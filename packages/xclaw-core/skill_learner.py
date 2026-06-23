"""
Skill Auto-Learning System

Automatically learns reusable skills from successful task completions.
Inspired by Hermes Agent's skill system.

When the agent successfully completes a complex multi-step task,
the skill learner extracts the pattern and stores it as a reusable skill.
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .persistent_memory import PersistentMemory
from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class SkillPattern:
    """A learned skill pattern."""
    name: str
    description: str
    trigger_patterns: List[str]
    tool_sequence: List[Dict[str, Any]]
    success_count: int = 0
    examples: List[str] = field(default_factory=list)


class SkillLearner:
    """
    Automatic skill learning from successful interactions.
    
    How it works:
    1. Monitor tool call sequences in successful conversations
    2. Identify repeated patterns (same tools, similar order)
    3. Extract trigger phrases and conditions
    4. Store as reusable skills in memory
    5. Match future requests to learned skills
    """
    
    # Minimum occurrences before a pattern becomes a skill
    MIN_OCCURRENCES = 2
    
    # Maximum tools in a skill sequence
    MAX_SEQUENCE_LENGTH = 5
    
    def __init__(self, memory: Optional[PersistentMemory] = None):
        self.memory = memory
        self._pending_patterns: Dict[str, List[List[Dict]]] = {}
        self._load_existing_skills()
    
    def _load_existing_skills(self):
        """Load existing skills from memory."""
        if not self.memory:
            return
        # Skills are loaded on-demand via find_matching_skills
    
    def observe_interaction(
        self,
        user_id: str,
        user_message: str,
        tool_calls: List[Dict],
        success: bool,
    ):
        """
        Observe an interaction for potential skill learning.
        
        Args:
            user_id: User ID
            user_message: Original user message
            tool_calls: List of tool calls made
            success: Whether the interaction was successful
        """
        if not success or len(tool_calls) < 2:
            return
        
        if len(tool_calls) > self.MAX_SEQUENCE_LENGTH:
            return
        
        # Create a pattern key from the tool sequence
        pattern_key = self._create_pattern_key(tool_calls)
        
        if pattern_key not in self._pending_patterns:
            self._pending_patterns[pattern_key] = []
        
        self._pending_patterns[pattern_key].append({
            "user_message": user_message,
            "tool_calls": tool_calls,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Check if we have enough occurrences to create a skill
        if len(self._pending_patterns[pattern_key]) >= self.MIN_OCCURRENCES:
            self._try_create_skill(pattern_key)
    
    def _create_pattern_key(self, tool_calls: List[Dict]) -> str:
        """Create a unique key for a tool call pattern."""
        # Use tool names in order as the pattern key
        tool_names = [tc.get("name", "") for tc in tool_calls]
        return "->".join(tool_names)
    
    def _try_create_skill(self, pattern_key: str):
        """Try to create a skill from observed patterns."""
        observations = self._pending_patterns[pattern_key]
        
        if len(observations) < self.MIN_OCCURRENCES:
            return
        
        # Extract common trigger phrases
        trigger_patterns = self._extract_trigger_patterns(observations)
        
        if not trigger_patterns:
            return
        
        # Create the skill
        tool_sequence = observations[0]["tool_calls"]
        skill_name = self._generate_skill_name(tool_sequence)
        description = self._generate_skill_description(tool_sequence, trigger_patterns)
        
        skill = SkillPattern(
            name=skill_name,
            description=description,
            trigger_patterns=trigger_patterns,
            tool_sequence=tool_sequence,
            success_count=len(observations),
            examples=[obs["user_message"] for obs in observations[:3]],
        )
        
        # Store the skill
        if self.memory:
            self.memory.store_skill(
                name=skill.name,
                description=skill.description,
                trigger_patterns=skill.trigger_patterns,
                tool_sequence=skill.tool_sequence,
            )
        
        logger.info(
            "skill_learned",
            skill_name=skill.name,
            trigger_patterns=skill.trigger_patterns,
            tool_count=len(skill.tool_sequence),
        )
        
        # Clear pending patterns for this key
        del self._pending_patterns[pattern_key]
    
    def _extract_trigger_patterns(self, observations: List[Dict]) -> List[str]:
        """Extract common trigger phrases from observations."""
        messages = [obs["user_message"] for obs in observations]
        
        # Find common words/phrases
        patterns = []
        
        # Simple approach: find common keywords
        word_counts = {}
        for msg in messages:
            words = set(self._tokenize(msg))
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Words that appear in most observations
        threshold = len(messages) * 0.6
        common_words = [
            word for word, count in word_counts.items()
            if count >= threshold and len(word) > 1
        ]
        
        if common_words:
            patterns.append(" ".join(common_words[:5]))
        
        # Also extract full phrases as patterns
        for msg in messages:
            # Clean and normalize
            clean_msg = re.sub(r'[^\w\s]', '', msg).strip()
            if len(clean_msg) > 3 and len(clean_msg) < 50:
                patterns.append(clean_msg)
        
        return list(set(patterns))[:5]  # Limit to 5 patterns
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for Chinese and English."""
        # Split on whitespace and punctuation, keep Chinese characters
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        return tokens
    
    def _generate_skill_name(self, tool_sequence: List[Dict]) -> str:
        """Generate a name for the skill."""
        tool_names = [tc.get("name", "unknown") for tc in tool_sequence]
        return "_".join(tool_names[:3])
    
    def _generate_skill_description(
        self,
        tool_sequence: List[Dict],
        trigger_patterns: List[str],
    ) -> str:
        """Generate a description for the skill."""
        tool_names = [tc.get("name", "unknown") for tc in tool_sequence]
        tools_str = " → ".join(tool_names)
        return f"自动学习的技能: {tools_str}"
    
    def find_matching_skill(self, user_message: str) -> Optional[Dict]:
        """
        Find a skill that matches the user's message.
        
        Args:
            user_message: User's message to match against
            
        Returns:
            Matching skill or None
        """
        if not self.memory:
            return None
        
        matches = self.memory.find_matching_skills(user_message)
        
        if matches:
            # Return the best match
            return matches[0]
        
        return None
    
    def record_skill_outcome(self, skill_name: str, success: bool):
        """Record the outcome of using a skill."""
        if self.memory:
            self.memory.record_skill_usage(skill_name, success)
    
    def get_learned_skills(self) -> List[Dict]:
        """Get all learned skills."""
        if not self.memory:
            return []
        
        # This would need a method in PersistentMemory to get all skills
        return []
