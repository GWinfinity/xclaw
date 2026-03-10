"""
NanoClaw Core - 核心运行时

一个极简的 Agent 运行时，支持：
- 技能注册与调用
- 上下文管理
- 事件驱动
- 基础任务编排
"""

import json
import time
import traceback
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nanoclaw")


class EventType(Enum):
    """事件类型"""
    SKILL_CALLED = "skill_called"
    SKILL_COMPLETED = "skill_completed"
    SKILL_FAILED = "skill_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    STATE_CHANGED = "state_changed"


@dataclass
class Event:
    """事件"""
    type: EventType
    source: str
    data: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp
        }


@dataclass 
class Context:
    """
    执行上下文
    
    保存 Agent 的状态和共享数据
    """
    session_id: str = field(default_factory=lambda: f"sess_{int(time.time()*1000)}")
    state: Dict = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def get(self, key: str, default=None):
        """获取状态值"""
        return self.state.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置状态值"""
        self.state[key] = value
        self._add_history('set', {'key': key, 'value': value})
    
    def update(self, data: Dict):
        """批量更新状态"""
        self.state.update(data)
        self._add_history('update', data)
    
    def _add_history(self, action: str, data: Dict):
        """添加历史记录"""
        self.history.append({
            'timestamp': time.time(),
            'action': action,
            'data': data
        })
        # 限制历史大小
        if len(self.history) > 1000:
            self.history = self.history[-500:]
    
    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'state': self.state,
            'history_count': len(self.history),
            'metadata': self.metadata
        }


class Skill:
    """
    技能基类
    
    所有可调用能力都包装为 Skill
    """
    
    def __init__(self, 
                 name: str,
                 description: str = "",
                 func: Optional[Callable] = None,
                 metadata: Optional[Dict] = None):
        self.name = name
        self.description = description
        self.func = func
        self.metadata = metadata or {}
        self.call_count = 0
        self.total_time = 0.0
    
    def execute(self, context: Context, **kwargs) -> Any:
        """执行技能"""
        if self.func is None:
            raise RuntimeError(f"Skill {self.name} has no implementation")
        
        start = time.time()
        self.call_count += 1
        
        try:
            # 注入 context
            if 'context' in self.func.__code__.co_varnames:
                result = self.func(context=context, **kwargs)
            else:
                result = self.func(**kwargs)
            
            elapsed = time.time() - start
            self.total_time += elapsed
            
            return {
                'success': True,
                'result': result,
                'elapsed_ms': elapsed * 1000
            }
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Skill {self.name} failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'elapsed_ms': elapsed * 1000
            }
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'metadata': self.metadata,
            'call_count': self.call_count,
            'avg_time_ms': (self.total_time / max(self.call_count, 1)) * 1000
        }


class NanoClaw:
    """
    NanoClaw Agent 运行时
    
    极简设计，核心功能：
    1. 技能注册与发现
    2. 上下文管理
    3. 事件驱动
    4. 基础任务链
    """
    
    def __init__(self, name: str = "nanoclaw"):
        self.name = name
        self.skills: Dict[str, Skill] = {}
        self.context = Context()
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.middleware: List[Callable] = []
        
        logger.info(f"NanoClaw '{name}' initialized")
    
    # ═════════════════════════════════════════════════════════════════
    # 技能管理
    # ═════════════════════════════════════════════════════════════════
    
    def skill(self, name: Optional[str] = None, description: str = ""):
        """
        装饰器：注册技能
        
        Usage:
            @agent.skill("my_skill")
            def my_func(context, x, y):
                return x + y
        """
        def decorator(func: Callable):
            skill_name = name or func.__name__
            skill = Skill(
                name=skill_name,
                description=description,
                func=func
            )
            self.register_skill(skill)
            return func
        return decorator
    
    def register_skill(self, skill: Skill) -> 'NanoClaw':
        """注册技能"""
        self.skills[skill.name] = skill
        logger.debug(f"Registered skill: {skill.name}")
        return self
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)
    
    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self.skills.keys())
    
    def call(self, skill_name: str, **kwargs) -> Dict:
        """
        调用技能
        
        Args:
            skill_name: 技能名称
            **kwargs: 传递给技能的参数
            
        Returns:
            调用结果字典
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return {
                'success': False,
                'error': f"Skill '{skill_name}' not found"
            }
        
        # 触发事件
        self._emit_event(EventType.SKILL_CALLED, skill_name, {
            'skill': skill_name,
            'args': kwargs
        })
        
        # 执行
        result = skill.execute(self.context, **kwargs)
        
        # 触发完成/失败事件
        if result['success']:
            self._emit_event(EventType.SKILL_COMPLETED, skill_name, {
                'skill': skill_name,
                'result': result
            })
        else:
            self._emit_event(EventType.SKILL_FAILED, skill_name, {
                'skill': skill_name,
                'error': result.get('error')
            })
        
        return result
    
    # ═════════════════════════════════════════════════════════════════
    # 事件系统
    # ═════════════════════════════════════════════════════════════════
    
    def on(self, event_type: EventType, handler: Callable):
        """订阅事件"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: EventType, source: str, data: Dict):
        """触发事件"""
        event = Event(type=event_type, source=source, data=data)
        
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    # ═════════════════════════════════════════════════════════════════
    # 任务链
    # ═════════════════════════════════════════════════════════════════
    
    def chain(self, *skill_calls: Dict) -> List[Dict]:
        """
        顺序执行技能链
        
        Args:
            *skill_calls: 技能调用配置列表
                [{'skill': 'skill_name', 'args': {...}}, ...]
        
        Returns:
            结果列表
        """
        results = []
        
        for call in skill_calls:
            skill_name = call.get('skill')
            args = call.get('args', {})
            
            result = self.call(skill_name, **args)
            results.append(result)
            
            # 失败时中断
            if not result['success'] and call.get('break_on_error', True):
                logger.warning(f"Chain broken at {skill_name}")
                break
        
        return results
    
    def parallel(self, *skill_calls: Dict) -> List[Dict]:
        """
        并行执行技能 (简化版，实际应使用线程/进程池)
        
        注意：当前为顺序执行，生产环境建议用 concurrent.futures
        """
        results = []
        for call in skill_calls:
            result = self.call(call['skill'], **call.get('args', {}))
            results.append(result)
        return results
    
    # ═════════════════════════════════════════════════════════════════
    # 状态管理
    # ═════════════════════════════════════════════════════════════════
    
    def remember(self, key: str, value: Any):
        """记忆数据"""
        self.context.set(key, value)
        self._emit_event(EventType.STATE_CHANGED, 'memory', {key: value})
    
    def recall(self, key: str, default=None):
        """回忆数据"""
        return self.context.get(key, default)
    
    def think(self, thought: str):
        """记录思考过程 (用于调试/可解释性)"""
        thoughts = self.context.get('_thoughts', [])
        thoughts.append({
            'timestamp': time.time(),
            'thought': thought
        })
        self.context.set('_thoughts', thoughts)
        logger.info(f"[Thought] {thought}")
    
    # ═════════════════════════════════════════════════════════════════
    # 工具方法
    # ═════════════════════════════════════════════════════════════════
    
    def info(self) -> Dict:
        """获取运行时信息"""
        return {
            'name': self.name,
            'skills': {name: skill.to_dict() for name, skill in self.skills.items()},
            'context': self.context.to_dict()
        }
    
    def export_session(self, filepath: str):
        """导出会话"""
        with open(filepath, 'w') as f:
            json.dump(self.info(), f, indent=2, default=str)
    
    def reset(self):
        """重置运行时"""
        self.context = Context()
        logger.info("NanoClaw reset")
