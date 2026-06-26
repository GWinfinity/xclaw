"""
xClaw Core - AI Agent for Tesla Vehicle Control

Provides natural language understanding and intelligent control
of Tesla vehicles through AI agents.

Inspired by Hermes Agent's architecture for self-evolving AI agents.
"""

from .agent import XClawAgent
from .tools import TeslaToolSet
from .memory import ConversationMemory
from .context import VehicleContext
from .persistent_memory import PersistentMemory
from .logging import setup_logging, get_logger, VehicleLogger, AgentLogger
from .safety import SafetyGuard, RateLimiter
from .scheduler import TaskScheduler
from .context_compressor import ContextCompressor
from .planner import Planner
from .skill_learner import SkillLearner

__version__ = "0.2.0"
__all__ = [
    "XClawAgent",
    "TeslaToolSet",
    "ConversationMemory",
    "VehicleContext",
    "PersistentMemory",
    "setup_logging",
    "get_logger",
    "VehicleLogger",
    "AgentLogger",
    "SafetyGuard",
    "RateLimiter",
    "TaskScheduler",
    "ContextCompressor",
    "Planner",
    "SkillLearner",
]
