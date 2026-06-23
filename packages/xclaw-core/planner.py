"""
Multi-Step Planning Engine

Enables the agent to plan and execute complex multi-step operations.
Inspired by Hermes Agent's iterative planning capabilities.

Example:
    User: "明天早上8点出门前，把车预热到24度，充到80%"
    Plan:
    1. Schedule climate for 7:45 AM at 24°C
    2. Schedule charging to reach 80% by 7:45 AM
    3. Confirm schedule to user
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .logging import get_logger

logger = get_logger(__name__)


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in a plan."""
    id: int
    description: str
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    status: PlanStepStatus = PlanStepStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    depends_on: List[int] = field(default_factory=list)


@dataclass
class Plan:
    """A multi-step execution plan."""
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    current_step: int = 0
    status: str = "pending"
    context: Dict[str, Any] = field(default_factory=dict)


class Planner:
    """
    Multi-step planning engine for complex vehicle operations.
    
    Features:
    - Decompose complex requests into ordered steps
    - Handle dependencies between steps
    - Self-correct on failures
    - Learn from successful plans
    """
    
    # Common multi-step patterns
    PATTERNS = {
        "morning_routine": {
            "triggers": ["早上", "出门", "上班", "morning"],
            "steps": [
                {"tool": "wake_vehicle", "desc": "唤醒车辆"},
                {"tool": "start_climate", "desc": "开启空调"},
                {"tool": "set_temperature", "desc": "设置温度"},
            ]
        },
        "charging_setup": {
            "triggers": ["充电", "charge", "电量"],
            "steps": [
                {"tool": "get_vehicle_data", "desc": "检查当前电量"},
                {"tool": "set_charge_limit", "desc": "设置充电限制"},
                {"tool": "start_charging", "desc": "开始充电"},
            ]
        },
        "secure_vehicle": {
            "triggers": ["安全", "锁车", "secure", "离开"],
            "steps": [
                {"tool": "close_windows", "desc": "关闭车窗"},
                {"tool": "lock_doors", "desc": "锁上车门"},
                {"tool": "set_sentry_mode", "desc": "开启哨兵模式", "args": {"enabled": True}},
            ]
        },
        "prepare_drive": {
            "triggers": ["开车", "出发", "drive", "出发"],
            "steps": [
                {"tool": "get_vehicle_data", "desc": "检查车辆状态"},
                {"tool": "start_climate", "desc": "开启空调"},
                {"tool": "unlock_doors", "desc": "解锁车门"},
            ]
        },
    }
    
    def __init__(self):
        self._learned_plans: Dict[str, Plan] = {}
    
    def analyze_request(self, user_message: str) -> Optional[Plan]:
        """
        Analyze a user request and create a plan if it's multi-step.
        
        Args:
            user_message: User's natural language request
            
        Returns:
            Plan if multi-step, None if single-step
        """
        msg_lower = user_message.lower()
        
        # Check for scheduling keywords (always multi-step)
        scheduling_keywords = ["定时", "schedule", "到时候", "之前", "以后", "明天", "tomorrow"]
        is_scheduling = any(kw in msg_lower for kw in scheduling_keywords)
        
        # Check for compound requests
        compound_indicators = ["然后", "并且", "同时", "还有", "再", "and", "then", "also"]
        is_compound = any(ind in msg_lower for ind in compound_indicators)
        
        # Check for known patterns
        matched_pattern = None
        for pattern_name, pattern in self.PATTERNS.items():
            for trigger in pattern["triggers"]:
                if trigger in msg_lower:
                    matched_pattern = pattern_name
                    break
            if matched_pattern:
                break
        
        if is_scheduling or is_compound or matched_pattern:
            return self._create_plan(user_message, matched_pattern)
        
        return None
    
    def _create_plan(self, user_message: str, pattern_name: Optional[str] = None) -> Plan:
        """Create a plan from user message and optional pattern."""
        plan = Plan(goal=user_message)
        
        if pattern_name and pattern_name in self.PATTERNS:
            pattern = self.PATTERNS[pattern_name]
            for i, step in enumerate(pattern["steps"]):
                plan.steps.append(PlanStep(
                    id=i,
                    description=step["desc"],
                    tool_name=step["tool"],
                    arguments=step.get("args", {}),
                ))
        else:
            # Generic multi-step decomposition
            plan.steps = self._decompose_generic(user_message)
        
        # Add a final confirmation step
        plan.steps.append(PlanStep(
            id=len(plan.steps),
            description="向用户确认执行结果",
            tool_name="confirm_result",
        ))
        
        return plan
    
    def _decompose_generic(self, user_message: str) -> List[PlanStep]:
        """Decompose a generic multi-step request."""
        steps = []
        msg_lower = user_message.lower()
        
        # Always start with getting vehicle data for context
        steps.append(PlanStep(
            id=0,
            description="获取车辆当前状态",
            tool_name="get_vehicle_data",
        ))
        
        # Detect climate-related actions
        if any(kw in msg_lower for kw in ["空调", "温度", "热", "冷", "climate", "temp"]):
            steps.append(PlanStep(
                id=len(steps),
                description="控制空调系统",
                tool_name="start_climate",
            ))
            if any(kw in msg_lower for kw in ["设置", "调到", "set"]):
                steps.append(PlanStep(
                    id=len(steps),
                    description="设置目标温度",
                    tool_name="set_temperature",
                ))
        
        # Detect charging-related actions
        if any(kw in msg_lower for kw in ["充电", "电量", "charge"]):
            steps.append(PlanStep(
                id=len(steps),
                description="管理充电",
                tool_name="start_charging",
            ))
        
        # Detect security-related actions
        if any(kw in msg_lower for kw in ["锁", "安全", "哨兵", "lock", "sentry"]):
            steps.append(PlanStep(
                id=len(steps),
                description="安全控制",
                tool_name="lock_doors",
            ))
        
        return steps
    
    def get_next_step(self, plan: Plan) -> Optional[PlanStep]:
        """Get the next pending step in the plan."""
        for step in plan.steps:
            if step.status == PlanStepStatus.PENDING:
                # Check dependencies
                deps_met = all(
                    plan.steps[dep].status == PlanStepStatus.COMPLETED
                    for dep in step.depends_on
                )
                if deps_met:
                    return step
        return None
    
    def mark_step_completed(self, plan: Plan, step_id: int, result: Dict):
        """Mark a step as completed."""
        for step in plan.steps:
            if step.id == step_id:
                step.status = PlanStepStatus.COMPLETED
                step.result = result
                break
    
    def mark_step_failed(self, plan: Plan, step_id: int, error: str):
        """Mark a step as failed."""
        for step in plan.steps:
            if step.id == step_id:
                step.status = PlanStepStatus.FAILED
                step.error = error
                break
    
    def is_plan_complete(self, plan: Plan) -> bool:
        """Check if all steps in the plan are completed."""
        return all(
            step.status in (PlanStepStatus.COMPLETED, PlanStepStatus.SKIPPED)
            for step in plan.steps
        )
    
    def get_plan_summary(self, plan: Plan) -> str:
        """Get a human-readable summary of the plan."""
        lines = [f"📋 计划: {plan.goal}"]
        lines.append(f"状态: {plan.status}")
        lines.append("步骤:")
        
        for step in plan.steps:
            status_icon = {
                PlanStepStatus.PENDING: "⏳",
                PlanStepStatus.EXECUTING: "🔄",
                PlanStepStatus.COMPLETED: "✅",
                PlanStepStatus.FAILED: "❌",
                PlanStepStatus.SKIPPED: "⏭️",
            }.get(step.status, "❓")
            
            lines.append(f"  {status_icon} {step.description}")
            if step.error:
                lines.append(f"     错误: {step.error}")
        
        return "\n".join(lines)
    
    def suggest_recovery(self, plan: Plan, failed_step: PlanStep) -> List[str]:
        """
        Suggest recovery actions when a step fails.
        
        Returns:
            List of recovery suggestions
        """
        suggestions = []
        
        if failed_step.tool_name == "wake_vehicle":
            suggestions.append("车辆可能处于深度睡眠，建议等待30秒后重试")
            suggestions.append("检查车辆是否在信号覆盖区域")
        
        elif failed_step.tool_name == "start_charging":
            suggestions.append("确认充电枪已正确连接")
            suggestions.append("检查充电桩是否正常工作")
        
        elif failed_step.tool_name == "lock_doors":
            suggestions.append("确认所有车门已关闭")
            suggestions.append("检查车辆是否处于可锁定状态")
        
        elif failed_step.tool_name == "set_temperature":
            suggestions.append("确认空调系统已开启")
            suggestions.append("检查温度设置范围 (16-30°C)")
        
        if not suggestions:
            suggestions.append("请稍后重试")
            suggestions.append("检查车辆网络连接")
        
        return suggestions
