"""
Safety Guardrails for xClaw

Provides rate limiting, command validation, and safety checks
for vehicle operations. Inspired by Hermes Agent's security model.
"""

import time
import json
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta

from .persistent_memory import PersistentMemory
from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_commands_per_minute: int = 10
    max_commands_per_hour: int = 60
    cooldown_seconds: Dict[str, int] = field(default_factory=lambda: {
        "unlock_doors": 5,
        "honk_horn": 3,
        "flash_lights": 3,
        "remote_start_drive": 10,
    })


@dataclass
class SafetyConfig:
    """Safety configuration."""
    require_confirmation: Set[str] = field(default_factory=lambda: {
        "unlock_doors",
        "remote_start_drive",
        "set_valet_mode",
        "speed_limit_deactivate",
    })
    risk_levels: Dict[str, str] = field(default_factory=lambda: {
        "lock_doors": "low",
        "unlock_doors": "medium",
        "honk_horn": "low",
        "flash_lights": "low",
        "start_climate": "low",
        "stop_climate": "low",
        "set_temperature": "low",
        "start_charging": "low",
        "stop_charging": "low",
        "set_charge_limit": "low",
        "open_trunk": "medium",
        "open_frunk": "medium",
        "set_sentry_mode": "low",
        "vent_windows": "low",
        "close_windows": "low",
        "remote_start_drive": "high",
        "set_valet_mode": "high",
        "speed_limit_activate": "high",
        "speed_limit_deactivate": "high",
        "speed_limit_set_limit": "medium",
        "set_seat_heater": "low",
        "set_steering_wheel_heater": "low",
        "trigger_homelink": "medium",
        "schedule_software_update": "medium",
        "cancel_software_update": "medium",
    })


class RateLimiter:
    """
    Token bucket rate limiter for vehicle commands.
    
    Prevents excessive API calls and protects against abuse.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._user_commands: Dict[str, List[float]] = defaultdict(list)
        self._last_command_time: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    def check_rate_limit(
        self,
        user_id: str,
        command: str,
    ) -> Tuple[bool, str]:
        """
        Check if a command is within rate limits.
        
        Returns:
            (allowed, reason) tuple
        """
        now = time.time()
        
        # Check cooldown for specific command
        cooldown = self.config.cooldown_seconds.get(command, 0)
        if cooldown > 0:
            last_time = self._last_command_time[user_id].get(command, 0)
            elapsed = now - last_time
            if elapsed < cooldown:
                remaining = cooldown - elapsed
                return False, f"命令冷却中，请等待 {remaining:.0f} 秒"
        
        # Clean old entries
        self._user_commands[user_id] = [
            t for t in self._user_commands[user_id]
            if now - t < 3600  # Keep last hour
        ]
        
        # Check per-minute limit
        recent_minute = [t for t in self._user_commands[user_id] if now - t < 60]
        if len(recent_minute) >= self.config.max_commands_per_minute:
            return False, f"每分钟命令数已达上限 ({self.config.max_commands_per_minute})"
        
        # Check per-hour limit
        if len(self._user_commands[user_id]) >= self.config.max_commands_per_hour:
            return False, f"每小时命令数已达上限 ({self.config.max_commands_per_hour})"
        
        # Record command
        self._user_commands[user_id].append(now)
        self._last_command_time[user_id][command] = now
        
        return True, ""
    
    def reset(self, user_id: str):
        """Reset rate limits for a user."""
        self._user_commands.pop(user_id, None)
        self._last_command_time.pop(user_id, None)


class SafetyGuard:
    """
    Safety guardrail system for vehicle commands.
    
    Features:
    - Command risk assessment
    - Confirmation requirements
    - Rate limiting
    - Audit logging
    - Dangerous operation detection
    """
    
    def __init__(
        self,
        memory: Optional[PersistentMemory] = None,
        rate_config: Optional[RateLimitConfig] = None,
        safety_config: Optional[SafetyConfig] = None,
    ):
        self.memory = memory
        self.rate_limiter = RateLimiter(rate_config)
        self.config = safety_config or SafetyConfig()
        self._pending_confirmations: Dict[str, Dict] = {}
    
    def validate_command(
        self,
        user_id: str,
        command: str,
        arguments: Dict = None,
    ) -> Tuple[bool, str, str]:
        """
        Validate a command before execution.
        
        Returns:
            (allowed, reason, risk_level) tuple
        """
        # Check rate limits
        allowed, reason = self.rate_limiter.check_rate_limit(user_id, command)
        if not allowed:
            self._log_audit(user_id, command, arguments, "rate_limited", "low")
            return False, reason, "low"
        
        # Get risk level
        risk_level = self.config.risk_levels.get(command, "low")
        
        # Check if confirmation is required
        if command in self.config.require_confirmation:
            if not self._has_confirmation(user_id, command):
                self._log_audit(user_id, command, arguments, "confirmation_required", risk_level)
                return False, "此操作需要确认", risk_level
        
        # Log the command
        self._log_audit(user_id, command, arguments, "allowed", risk_level)
        
        return True, "", risk_level
    
    def request_confirmation(self, user_id: str, command: str) -> str:
        """
        Request confirmation for a dangerous command.
        
        Returns:
            Confirmation token for later verification
        """
        import hashlib
        token = hashlib.md5(
            f"{user_id}:{command}:{time.time()}".encode()
        ).hexdigest()[:8]
        
        self._pending_confirmations[f"{user_id}:{command}"] = {
            "token": token,
            "expires": time.time() + 30,  # 30 second expiry
            "command": command,
        }
        
        return token
    
    def confirm(self, user_id: str, command: str, token: str) -> bool:
        """
        Confirm a pending command.
        
        Returns:
            True if confirmation is valid
        """
        key = f"{user_id}:{command}"
        pending = self._pending_confirmations.get(key)
        
        if not pending:
            return False
        
        if time.time() > pending["expires"]:
            del self._pending_confirmations[key]
            return False
        
        if pending["token"] != token:
            return False
        
        del self._pending_confirmations[key]
        return True
    
    def _has_confirmation(self, user_id: str, command: str) -> bool:
        """Check if command has been confirmed."""
        key = f"{user_id}:{command}"
        pending = self._pending_confirmations.get(key)
        
        if not pending:
            return False
        
        if time.time() > pending["expires"]:
            del self._pending_confirmations[key]
            return False
        
        return True
    
    def _log_audit(
        self,
        user_id: str,
        command: str,
        arguments: Dict,
        result: str,
        risk_level: str,
    ):
        """Log command to audit log."""
        if self.memory:
            self.memory.log_audit(
                user_id=user_id,
                action=command,
                target="vehicle",
                parameters=arguments or {},
                result=result,
                risk_level=risk_level,
            )
        
        logger.info(
            "safety_check",
            user_id=user_id,
            command=command,
            result=result,
            risk_level=risk_level,
        )
    
    def get_audit_summary(
        self,
        user_id: str,
        hours: int = 24,
    ) -> Dict:
        """Get audit summary for a user."""
        if not self.memory:
            return {"error": "Memory not available"}
        
        logs = self.memory.get_audit_log(user_id=user_id, hours=hours)
        
        summary = {
            "total_commands": len(logs),
            "by_risk_level": defaultdict(int),
            "by_action": defaultdict(int),
            "rate_limited": 0,
            "confirmations_required": 0,
        }
        
        for log in logs:
            summary["by_risk_level"][log["risk_level"]] += 1
            summary["by_action"][log["action"]] += 1
            if log["result"] == "rate_limited":
                summary["rate_limited"] += 1
            if log["result"] == "confirmation_required":
                summary["confirmations_required"] += 1
        
        return dict(summary)
