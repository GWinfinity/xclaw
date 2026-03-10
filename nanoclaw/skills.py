"""
NanoClaw Skills - 技能辅助模块

提供技能注册表和包装器的额外功能
"""

from typing import Dict, List, Optional, Callable
import json
from pathlib import Path

from .core import Skill, Context


class SkillRegistry:
    """
    高级技能注册表
    
    支持持久化和批量操作
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.skills: Dict[str, Skill] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        
        if self.storage_path:
            self._load()
    
    def register(self, skill: Skill) -> 'SkillRegistry':
        """注册技能"""
        self.skills[skill.name] = skill
        return self
    
    def get(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)
    
    def list(self) -> List[str]:
        """列出所有技能"""
        return list(self.skills.keys())
    
    def save(self) -> bool:
        """保存到磁盘"""
        if not self.storage_path:
            return False
        
        try:
            data = {
                name: {
                    'name': skill.name,
                    'description': skill.description,
                    'metadata': skill.metadata,
                    'call_count': skill.call_count
                }
                for name, skill in self.skills.items()
            }
            
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def _load(self) -> None:
        """从磁盘加载"""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # 注意：这里只加载元数据，实际函数需要重新注册
            for name, skill_data in data.items():
                # 创建占位 Skill（没有 func）
                skill = Skill(
                    name=skill_data['name'],
                    description=skill_data.get('description', ''),
                    metadata=skill_data.get('metadata', {})
                )
                skill.call_count = skill_data.get('call_count', 0)
                self.skills[name] = skill
                
        except Exception:
            pass


class SkillWrapper:
    """
    技能包装器
    
    为现有函数/类添加技能功能
    """
    
    @staticmethod
    def from_function(func: Callable, 
                     name: Optional[str] = None,
                     description: Optional[str] = None) -> Skill:
        """从函数创建技能"""
        return Skill(
            name=name or func.__name__,
            description=description or func.__doc__ or "",
            func=func
        )
    
    @staticmethod
    def from_class(cls, 
                  name: Optional[str] = None,
                  method_name: str = "execute") -> Skill:
        """从类创建技能（调用指定方法）"""
        def wrapper(context: Context, **kwargs):
            instance = cls()
            method = getattr(instance, method_name)
            return method(context=context, **kwargs)
        
        return Skill(
            name=name or cls.__name__,
            description=cls.__doc__ or "",
            func=wrapper
        )
