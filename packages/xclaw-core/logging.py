"""
Structured Logging for xClaw

Provides structured logging using structlog for observability.
Following Hermes Agent's observability patterns.
"""

import logging
import sys
from typing import Any, Dict, Optional

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    service_name: str = "xclaw",
) -> None:
    """
    Setup structured logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ("json" or "text")
        service_name: Service name for log entries
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if STRUCTLOG_AVAILABLE:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.CallsiteParameterAdder(
                [structlog.processors.CallsiteParameter.FILENAME,
                 structlog.processors.CallsiteParameter.FUNC_NAME,
                 structlog.processors.CallsiteParameter.LINENO]
            ),
        ]
        
        if format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Add service name to global context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(service=service_name)
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s %(message)s",
            stream=sys.stdout,
        )


def get_logger(name: str) -> Any:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    return logging.getLogger(name)


class VehicleLogger:
    """
    Vehicle-specific structured logger.
    
    Logs vehicle operations with context for debugging and auditing.
    """
    
    def __init__(self, vin: str, logger_name: str = "xclaw.vehicle"):
        self.vin = vin
        self.logger = get_logger(logger_name)
    
    def _bind(self, **kwargs) -> Any:
        """Bind vehicle context to logger."""
        if STRUCTLOG_AVAILABLE:
            return self.logger.bind(vin=self.vin, **kwargs)
        return self.logger
    
    def command_sent(self, command: str, parameters: Dict = None):
        """Log a vehicle command being sent."""
        self._bind(command=command).info(
            "vehicle_command_sent",
            parameters=parameters or {},
        )
    
    def command_result(self, command: str, success: bool, error: str = None):
        """Log a vehicle command result."""
        log = self._bind(command=command, success=success)
        if success:
            log.info("vehicle_command_success")
        else:
            log.warning("vehicle_command_failed", error=error)
    
    def state_changed(self, field: str, old_value: Any, new_value: Any):
        """Log a vehicle state change."""
        self._bind(field=field).info(
            "vehicle_state_changed",
            old_value=str(old_value),
            new_value=str(new_value),
        )
    
    def data_fetched(self, data_type: str, duration_ms: float):
        """Log vehicle data fetch."""
        self._bind(data_type=data_type).debug(
            "vehicle_data_fetched",
            duration_ms=duration_ms,
        )
    
    def error(self, operation: str, error: Exception):
        """Log a vehicle error."""
        self._bind(operation=operation).error(
            "vehicle_error",
            error_type=type(error).__name__,
            error_message=str(error),
        )


class AgentLogger:
    """
    Agent-specific structured logger.
    
    Logs agent operations for debugging and performance monitoring.
    """
    
    def __init__(self, logger_name: str = "xclaw.agent"):
        self.logger = get_logger(logger_name)
    
    def process_start(self, user_id: str, message_preview: str):
        """Log agent process start."""
        self.logger.info(
            "agent_process_start",
            user_id=user_id,
            message_preview=message_preview[:100],
        )
    
    def process_end(self, user_id: str, duration_ms: float, tool_calls: int):
        """Log agent process end."""
        self.logger.info(
            "agent_process_end",
            user_id=user_id,
            duration_ms=duration_ms,
            tool_calls=tool_calls,
        )
    
    def llm_call(self, provider: str, model: str, tokens_used: int = 0, duration_ms: float = 0):
        """Log LLM API call."""
        self.logger.info(
            "llm_call",
            provider=provider,
            model=model,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
    
    def tool_executed(self, tool_name: str, success: bool, duration_ms: float):
        """Log tool execution."""
        self.logger.info(
            "tool_executed",
            tool_name=tool_name,
            success=success,
            duration_ms=duration_ms,
        )
    
    def memory_operation(self, operation: str, details: Dict = None):
        """Log memory operation."""
        self.logger.debug(
            "memory_operation",
            operation=operation,
            **(details or {}),
        )
    
    def skill_learned(self, skill_name: str, trigger: str):
        """Log skill learning."""
        self.logger.info(
            "skill_learned",
            skill_name=skill_name,
            trigger=trigger,
        )
    
    def safety_alert(self, alert_type: str, details: Dict):
        """Log safety alert."""
        self.logger.warning(
            "safety_alert",
            alert_type=alert_type,
            **details,
        )
