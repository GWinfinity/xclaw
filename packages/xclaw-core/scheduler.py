"""
Task Scheduler for xClaw

Provides scheduled task execution for vehicle operations.
Inspired by Hermes Agent's cron system.

Use cases:
- Pre-heat climate at a specific time
- Schedule charging to complete by departure time
- Periodic vehicle status checks
- Geofence-based triggers
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable, Any, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .persistent_memory import PersistentMemory
from .logging import get_logger

logger = get_logger(__name__)


class TriggerType(str, Enum):
    CRON = "cron"
    TIME = "time"
    VEHICLE_STATE = "vehicle_state"
    GEOFENCE = "geofence"


class ActionType(str, Enum):
    CLIMATE_ON = "climate_on"
    CLIMATE_OFF = "climate_off"
    SET_TEMPERATURE = "set_temperature"
    CHARGE_START = "charge_start"
    CHARGE_STOP = "charge_stop"
    SET_CHARGE_LIMIT = "set_charge_limit"
    LOCK_DOORS = "lock_doors"
    UNLOCK_DOORS = "unlock_doors"
    SET_SENTRY_MODE = "set_sentry_mode"
    WAKE_VEHICLE = "wake_vehicle"
    CUSTOM = "custom"


@dataclass
class ScheduledTask:
    """A scheduled task definition."""
    id: Optional[int] = None
    user_id: str = ""
    name: str = ""
    description: str = ""
    trigger_type: TriggerType = TriggerType.TIME
    trigger_config: Dict = field(default_factory=dict)
    action_type: ActionType = ActionType.CUSTOM
    action_config: Dict = field(default_factory=dict)
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None


class TaskScheduler:
    """
    Task scheduler for vehicle operations.
    
    Features:
    - Time-based scheduling (at specific time, after delay)
    - Recurring tasks (cron-like expressions)
    - Vehicle state triggers (battery below X%, temperature above Y)
    - Geofence triggers (arriving/leaving a location)
    """
    
    def __init__(self, memory: Optional[PersistentMemory] = None):
        self.memory = memory
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._handlers: Dict[str, Callable[..., Awaitable]] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default action handlers."""
        self._handlers = {
            ActionType.CLIMATE_ON.value: self._handle_climate_on,
            ActionType.CLIMATE_OFF.value: self._handle_climate_off,
            ActionType.SET_TEMPERATURE.value: self._handle_set_temperature,
            ActionType.CHARGE_START.value: self._handle_charge_start,
            ActionType.CHARGE_STOP.value: self._handle_charge_stop,
            ActionType.SET_CHARGE_LIMIT.value: self._handle_set_charge_limit,
            ActionType.LOCK_DOORS.value: self._handle_lock_doors,
            ActionType.UNLOCK_DOORS.value: self._handle_unlock_doors,
            ActionType.SET_SENTRY_MODE.value: self._handle_set_sentry_mode,
            ActionType.WAKE_VEHICLE.value: self._handle_wake_vehicle,
        }
    
    def register_handler(self, action_type: str, handler: Callable[..., Awaitable]):
        """Register a custom action handler."""
        self._handlers[action_type] = handler
    
    async def start(self, check_interval: int = 60):
        """
        Start the scheduler.
        
        Args:
            check_interval: Seconds between checking for due tasks
        """
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop(check_interval))
        logger.info("scheduler_started", check_interval=check_interval)
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("scheduler_stopped")
    
    async def _run_loop(self, check_interval: int):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_run_tasks()
            except Exception as e:
                logger.error("scheduler_error", error=str(e))
            await asyncio.sleep(check_interval)
    
    async def _check_and_run_tasks(self):
        """Check for due tasks and execute them."""
        if not self.memory:
            return
        
        due_tasks = self.memory.get_due_tasks()
        
        for task_row in due_tasks:
            try:
                task = ScheduledTask(
                    id=task_row["id"],
                    user_id=task_row["user_id"],
                    name=task_row["name"],
                    action_type=ActionType(task_row["action_type"]),
                    action_config=json.loads(task_row["action_config"]),
                    trigger_type=TriggerType(task_row["trigger_type"]),
                    trigger_config=json.loads(task_row["trigger_config"]),
                )
                
                await self._execute_task(task)
                
                # Calculate next run time
                next_run = self._calculate_next_run(task)
                self.memory.update_task_run(task.id, next_run)
                
            except Exception as e:
                logger.error("task_execution_error", task_id=task_row["id"], error=str(e))
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        handler = self._handlers.get(task.action_type.value)
        
        if not handler:
            logger.warning("no_handler_for_action", action=task.action_type.value)
            return
        
        logger.info("executing_task", task_id=task.id, name=task.name, action=task.action_type.value)
        
        try:
            await handler(task.user_id, task.action_config)
            logger.info("task_completed", task_id=task.id, name=task.name)
        except Exception as e:
            logger.error("task_failed", task_id=task.id, error=str(e))
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[str]:
        """Calculate the next run time for a task."""
        if task.trigger_type == TriggerType.TIME:
            # One-time task, no next run
            return None
        
        if task.trigger_type == TriggerType.CRON:
            # Simple interval-based recurrence
            interval_hours = task.trigger_config.get("interval_hours", 24)
            next_time = datetime.utcnow() + timedelta(hours=interval_hours)
            return next_time.isoformat()
        
        return None
    
    # ==================== Task Creation Helpers ====================
    
    def schedule_climate(
        self,
        user_id: str,
        time_str: str,
        temperature: float = 22.0,
        name: str = "定时空调",
    ) -> int:
        """
        Schedule climate control at a specific time.
        
        Args:
            user_id: User ID
            time_str: Time in ISO format or relative (e.g., "+30m", "+1h")
            temperature: Target temperature
            name: Task name
        """
        trigger_config = {"time": time_str}
        
        return self.memory.create_scheduled_task(
            user_id=user_id,
            name=name,
            action_type=ActionType.SET_TEMPERATURE.value,
            action_config={"temperature": temperature},
            description=f"在 {time_str} 设置温度为 {temperature}°C",
            trigger_type=TriggerType.TIME.value,
            trigger_config=trigger_config,
        )
    
    def schedule_charging(
        self,
        user_id: str,
        target_time: str,
        target_percent: int = 80,
        name: str = "定时充电",
    ) -> int:
        """
        Schedule charging to complete by a target time.
        
        Args:
            user_id: User ID
            target_time: Target completion time
            target_percent: Target charge percentage
            name: Task name
        """
        return self.memory.create_scheduled_task(
            user_id=user_id,
            name=name,
            action_type=ActionType.CHARGE_START.value,
            action_config={"target_percent": target_percent},
            description=f"在 {target_time} 前充电至 {target_percent}%",
            trigger_type=TriggerType.TIME.value,
            trigger_config={"time": target_time},
        )
    
    def schedule_recurring_check(
        self,
        user_id: str,
        interval_hours: int = 6,
        name: str = "定期车辆检查",
    ) -> int:
        """
        Schedule recurring vehicle status check.
        
        Args:
            user_id: User ID
            interval_hours: Hours between checks
            name: Task name
        """
        return self.memory.create_scheduled_task(
            user_id=user_id,
            name=name,
            action_type=ActionType.WAKE_VEHICLE.value,
            action_config={},
            description=f"每 {interval_hours} 小时检查车辆状态",
            trigger_type=TriggerType.CRON.value,
            trigger_config={"interval_hours": interval_hours},
        )
    
    # ==================== Default Action Handlers ====================
    
    async def _handle_climate_on(self, user_id: str, config: Dict):
        """Handle climate on action."""
        logger.info("scheduled_climate_on", user_id=user_id)
        # This will be connected to TeslaToolSet
    
    async def _handle_climate_off(self, user_id: str, config: Dict):
        """Handle climate off action."""
        logger.info("scheduled_climate_off", user_id=user_id)
    
    async def _handle_set_temperature(self, user_id: str, config: Dict):
        """Handle set temperature action."""
        temp = config.get("temperature", 22.0)
        logger.info("scheduled_set_temperature", user_id=user_id, temperature=temp)
    
    async def _handle_charge_start(self, user_id: str, config: Dict):
        """Handle charge start action."""
        logger.info("scheduled_charge_start", user_id=user_id)
    
    async def _handle_charge_stop(self, user_id: str, config: Dict):
        """Handle charge stop action."""
        logger.info("scheduled_charge_stop", user_id=user_id)
    
    async def _handle_set_charge_limit(self, user_id: str, config: Dict):
        """Handle set charge limit action."""
        percent = config.get("percent", 80)
        logger.info("scheduled_set_charge_limit", user_id=user_id, percent=percent)
    
    async def _handle_lock_doors(self, user_id: str, config: Dict):
        """Handle lock doors action."""
        logger.info("scheduled_lock_doors", user_id=user_id)
    
    async def _handle_unlock_doors(self, user_id: str, config: Dict):
        """Handle unlock doors action."""
        logger.info("scheduled_unlock_doors", user_id=user_id)
    
    async def _handle_set_sentry_mode(self, user_id: str, config: Dict):
        """Handle set sentry mode action."""
        enabled = config.get("enabled", True)
        logger.info("scheduled_set_sentry_mode", user_id=user_id, enabled=enabled)
    
    async def _handle_wake_vehicle(self, user_id: str, config: Dict):
        """Handle wake vehicle action."""
        logger.info("scheduled_wake_vehicle", user_id=user_id)
