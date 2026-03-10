"""
NanoClaw - 轻量级 Agent 运行时

设计原则：
- 极简核心 (~500行代码)
- 零外部依赖 (仅标准库)
- 支持 Skills 和任务编排
- 与 genesis-cloud-sim 无缝集成
"""

from .core import NanoClaw, Skill, Context, Event
from .skills import SkillRegistry, SkillWrapper
from .integration import GenesisIntegration, SimSkill

__version__ = "0.1.0"

__all__ = [
    # Core
    'NanoClaw',
    'Skill', 
    'Context',
    'Event',
    
    # Skills
    'SkillRegistry',
    'SkillWrapper',
    
    # Integration
    'GenesisIntegration',
    'SimSkill',
]
