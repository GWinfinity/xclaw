"""
Tesla Tools for AI Agent

Defines tools/functions that the AI agent can use to control Tesla vehicles.
"""

import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .context import VehicleContext


@dataclass
class ToolResult:
    """Result of a tool execution."""
    tool_call_id: Optional[str] = None
    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class TeslaToolSet:
    """
    Set of tools for controlling Tesla vehicles.
    
    These tools are exposed to the AI agent through OpenAI function calling.
    """
    
    def __init__(self, vehicle_context: VehicleContext):
        self.vehicle_context = vehicle_context
        self._tools: Dict[str, Callable] = {
            "get_vehicle_data": self._get_vehicle_data,
            "wake_vehicle": self._wake_vehicle,
            "lock_doors": self._lock_doors,
            "unlock_doors": self._unlock_doors,
            "honk_horn": self._honk_horn,
            "flash_lights": self._flash_lights,
            "start_climate": self._start_climate,
            "stop_climate": self._stop_climate,
            "set_temperature": self._set_temperature,
            "start_charging": self._start_charging,
            "stop_charging": self._stop_charging,
            "set_charge_limit": self._set_charge_limit,
            "open_charge_port": self._open_charge_port,
            "close_charge_port": self._close_charge_port,
            "open_trunk": self._open_trunk,
            "open_frunk": self._open_frunk,
            "set_sentry_mode": self._set_sentry_mode,
            "vent_windows": self._vent_windows,
            "close_windows": self._close_windows,
        }
    
    def get_openai_functions(self) -> List[Dict[str, Any]]:
        """Get function definitions for OpenAI API."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_vehicle_data",
                    "description": "获取车辆完整数据，包括电池、空调、位置等信息",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "wake_vehicle",
                    "description": "唤醒车辆，如果车辆处于睡眠状态",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lock_doors",
                    "description": "锁定车辆所有车门",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "unlock_doors",
                    "description": "解锁车辆所有车门。注意：这会降低车辆安全性",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "honk_horn",
                    "description": "鸣笛，用于寻找车辆",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "flash_lights",
                    "description": "闪灯，用于寻找车辆",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "start_climate",
                    "description": "开启空调系统",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "stop_climate",
                    "description": "关闭空调系统",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_temperature",
                    "description": "设置车内温度",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "temperature": {
                                "type": "number",
                                "description": "目标温度，摄氏度 (16-30)",
                            },
                        },
                        "required": ["temperature"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "start_charging",
                    "description": "开始充电",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "stop_charging",
                    "description": "停止充电",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_charge_limit",
                    "description": "设置充电限制百分比",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "percent": {
                                "type": "integer",
                                "description": "充电限制百分比 (50-100)",
                            },
                        },
                        "required": ["percent"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "open_charge_port",
                    "description": "打开充电口",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "close_charge_port",
                    "description": "关闭充电口",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "open_trunk",
                    "description": "打开后备箱",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "open_frunk",
                    "description": "打开前备箱",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_sentry_mode",
                    "description": "设置哨兵模式",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enabled": {
                                "type": "boolean",
                                "description": "true 开启哨兵模式，false 关闭",
                            },
                        },
                        "required": ["enabled"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "vent_windows",
                    "description": "微开车窗通风",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "close_windows",
                    "description": "关闭所有车窗",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
        ]
    
    async def execute(self, function_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name."""
        if function_name not in self._tools:
            return ToolResult(
                success=False,
                error=f"Unknown function: {function_name}"
            )
        
        try:
            result = await self._tools[function_name](**arguments)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                data={"exception": type(e).__name__}
            )
    
    # ==================== Tool Implementations ====================
    
    async def _get_vehicle_data(self) -> Dict[str, Any]:
        """Get vehicle data."""
        vehicle = await self.vehicle_context.get_vehicle()
        data = await vehicle.get_vehicle_data()
        
        return {
            "display_name": data.display_name,
            "vin": data.vin,
            "state": data.state,
            "battery_level": data.charge_state.battery_level,
            "battery_range_km": int(data.charge_state.battery_range * 1.60934),
            "charging_state": data.charge_state.charging_state.value,
            "inside_temp": data.climate_state.inside_temp,
            "driver_temp_setting": data.climate_state.driver_temp_setting,
            "is_climate_on": data.climate_state.is_climate_on,
            "locked": data.vehicle_state.locked,
            "sentry_mode": data.vehicle_state.sentry_mode,
            "odometer_km": int(data.vehicle_state.odometer * 1.60934),
        }
    
    async def _wake_vehicle(self) -> Dict[str, Any]:
        """Wake up the vehicle."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.wake_up()
        return {"success": success, "state": vehicle.state}
    
    async def _lock_doors(self) -> Dict[str, Any]:
        """Lock doors."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.lock_doors()
        return {"success": success, "action": "lock"}
    
    async def _unlock_doors(self) -> Dict[str, Any]:
        """Unlock doors."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.unlock_doors()
        return {"success": success, "action": "unlock"}
    
    async def _honk_horn(self) -> Dict[str, Any]:
        """Honk horn."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.honk_horn()
        return {"success": success, "action": "honk"}
    
    async def _flash_lights(self) -> Dict[str, Any]:
        """Flash lights."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.flash_lights()
        return {"success": success, "action": "flash_lights"}
    
    async def _start_climate(self) -> Dict[str, Any]:
        """Start climate control."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.auto_conditioning_start()
        return {"success": success, "action": "start_climate"}
    
    async def _stop_climate(self) -> Dict[str, Any]:
        """Stop climate control."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.auto_conditioning_stop()
        return {"success": success, "action": "stop_climate"}
    
    async def _set_temperature(self, temperature: float) -> Dict[str, Any]:
        """Set temperature."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.set_climate_temperature(temperature)
        return {"success": success, "temperature": temperature}
    
    async def _start_charging(self) -> Dict[str, Any]:
        """Start charging."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.charge_start()
        return {"success": success, "action": "start_charging"}
    
    async def _stop_charging(self) -> Dict[str, Any]:
        """Stop charging."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.charge_stop()
        return {"success": success, "action": "stop_charging"}
    
    async def _set_charge_limit(self, percent: int) -> Dict[str, Any]:
        """Set charge limit."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.set_charge_limit(percent)
        return {"success": success, "charge_limit": percent}
    
    async def _open_charge_port(self) -> Dict[str, Any]:
        """Open charge port."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.charge_port_door_open()
        return {"success": success, "action": "open_charge_port"}
    
    async def _close_charge_port(self) -> Dict[str, Any]:
        """Close charge port."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.charge_port_door_close()
        return {"success": success, "action": "close_charge_port"}
    
    async def _open_trunk(self) -> Dict[str, Any]:
        """Open trunk."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.actuate_trunk("rear")
        return {"success": success, "action": "open_trunk"}
    
    async def _open_frunk(self) -> Dict[str, Any]:
        """Open frunk."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.actuate_trunk("front")
        return {"success": success, "action": "open_frunk"}
    
    async def _set_sentry_mode(self, enabled: bool) -> Dict[str, Any]:
        """Set sentry mode."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.set_sentry_mode(enabled)
        return {"success": success, "sentry_mode": enabled}
    
    async def _vent_windows(self) -> Dict[str, Any]:
        """Vent windows."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.window_control("vent")
        return {"success": success, "action": "vent_windows"}
    
    async def _close_windows(self) -> Dict[str, Any]:
        """Close windows."""
        vehicle = await self.vehicle_context.get_vehicle()
        # Note: close requires location for safety
        data = await vehicle.get_location_data()
        lat = data.get("latitude")
        lon = data.get("longitude")
        success = await vehicle.window_control("close", lat=lat, lon=lon)
        return {"success": success, "action": "close_windows"}
