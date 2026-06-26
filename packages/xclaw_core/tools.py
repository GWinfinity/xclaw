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
            "get_location": self._get_location,
            "wake_vehicle": self._wake_vehicle,
            "lock_doors": self._lock_doors,
            "unlock_doors": self._unlock_doors,
            "honk_horn": self._honk_horn,
            "flash_lights": self._flash_lights,
            "start_climate": self._start_climate,
            "stop_climate": self._stop_climate,
            "set_temperature": self._set_temperature,
            "set_seat_heater": self._set_seat_heater,
            "set_steering_wheel_heater": self._set_steering_wheel_heater,
            "start_charging": self._start_charging,
            "stop_charging": self._stop_charging,
            "set_charge_limit": self._set_charge_limit,
            "set_charging_amps": self._set_charging_amps,
            "open_charge_port": self._open_charge_port,
            "close_charge_port": self._close_charge_port,
            "open_trunk": self._open_trunk,
            "open_frunk": self._open_frunk,
            "set_sentry_mode": self._set_sentry_mode,
            "vent_windows": self._vent_windows,
            "close_windows": self._close_windows,
            "set_speed_limit": self._set_speed_limit,
            "set_valet_mode": self._set_valet_mode,
            "trigger_homelink": self._trigger_homelink,
            "schedule_software_update": self._schedule_software_update,
            "cancel_software_update": self._cancel_software_update,
            "navigate_to": self._navigate_to,
            "navigate_to_supercharger": self._navigate_to_supercharger,
            "set_climate_keeper_mode": self._set_climate_keeper_mode,
            "set_seat_cooler": self._set_seat_cooler,
            "set_bioweapon_mode": self._set_bioweapon_mode,
            "get_vehicle_info": self._get_vehicle_info,
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
            {
                "type": "function",
                "function": {
                    "name": "get_location",
                    "description": "获取车辆当前位置（经纬度）",
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
                    "name": "set_seat_heater",
                    "description": "设置座椅加热等级",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seat": {
                                "type": "integer",
                                "description": "座椅位置: 0=前排左, 1=前排右, 2=后排左, 3=后排中, 4=后排右",
                            },
                            "level": {
                                "type": "integer",
                                "description": "加热等级: 0=关闭, 1=低, 2=中, 3=高",
                            },
                        },
                        "required": ["seat", "level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_steering_wheel_heater",
                    "description": "设置方向盘加热",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enabled": {
                                "type": "boolean",
                                "description": "true 开启，false 关闭",
                            },
                        },
                        "required": ["enabled"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_charging_amps",
                    "description": "设置充电电流（安培）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amps": {
                                "type": "integer",
                                "description": "充电电流 (0-32 安培)",
                            },
                        },
                        "required": ["amps"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_speed_limit",
                    "description": "设置车辆限速",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit_mph": {
                                "type": "integer",
                                "description": "限速值（英里/小时）",
                            },
                            "pin": {
                                "type": "string",
                                "description": "4位PIN码",
                            },
                        },
                        "required": ["limit_mph", "pin"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_valet_mode",
                    "description": "设置代客模式",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enabled": {
                                "type": "boolean",
                                "description": "true 开启，false 关闭",
                            },
                            "pin": {
                                "type": "string",
                                "description": "4位PIN码（开启时必填）",
                            },
                        },
                        "required": ["enabled"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_homelink",
                    "description": "触发 Homelink 车库门开关",
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
                    "name": "schedule_software_update",
                    "description": "调度软件更新",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "offset_minutes": {
                                "type": "integer",
                                "description": "延迟多少分钟后开始更新（默认0=立即）",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_software_update",
                    "description": "取消已调度的软件更新",
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
                    "name": "navigate_to",
                    "description": "导航到指定位置（地址或坐标）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination": {
                                "type": "string",
                                "description": "目的地地址或名称",
                            },
                        },
                        "required": ["destination"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "navigate_to_supercharger",
                    "description": "导航到超级充电站",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "supercharger_id": {
                                "type": "integer",
                                "description": "超级充电站 ID",
                            },
                        },
                        "required": ["supercharger_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_climate_keeper_mode",
                    "description": "设置气候保持模式",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "integer",
                                "description": "模式: 0=关闭, 1=保持, 2=宠物模式, 3=露营模式",
                            },
                        },
                        "required": ["mode"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_seat_cooler",
                    "description": "设置座椅通风 (仅支持配备通风座椅的车型)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seat": {
                                "type": "integer",
                                "description": "座位位置: 0=前排左, 1=前排右",
                            },
                            "level": {
                                "type": "integer",
                                "description": "通风等级: 0=关闭, 1=低档, 2=中档, 3=高档",
                            },
                        },
                        "required": ["seat", "level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_bioweapon_mode",
                    "description": "设置生物武器防御模式",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enabled": {
                                "type": "boolean",
                                "description": "true 开启，false 关闭",
                            },
                        },
                        "required": ["enabled"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_vehicle_info",
                    "description": "获取车辆硬件信息（车型、硬件版本、支持的功能）",
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
    
    async def _get_location(self) -> Dict[str, Any]:
        """Get vehicle location."""
        vehicle = await self.vehicle_context.get_vehicle()
        data = await vehicle.get_location_data()
        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "heading": data.get("heading"),
            "speed": data.get("speed"),
            "timestamp": data.get("timestamp"),
        }
    
    async def _set_seat_heater(self, seat: int, level: int) -> Dict[str, Any]:
        """Set seat heater."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.set_seat_heater(seat, level)
        seat_names = {0: "前排左", 1: "前排右", 2: "后排左", 3: "后排中", 4: "后排右"}
        return {
            "success": success,
            "seat": seat_names.get(seat, f"座椅{seat}"),
            "level": level,
        }
    
    async def _set_steering_wheel_heater(self, enabled: bool) -> Dict[str, Any]:
        """Set steering wheel heater."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.set_steering_wheel_heater(enabled)
        return {"success": success, "steering_wheel_heater": enabled}
    
    async def _set_charging_amps(self, amps: int) -> Dict[str, Any]:
        """Set charging amps."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.set_charging_amps(amps)
        return {"success": success, "charging_amps": amps}
    
    async def _set_speed_limit(self, limit_mph: int, pin: str) -> Dict[str, Any]:
        """Set speed limit."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.speed_limit_set_limit(limit_mph)
        return {"success": success, "speed_limit_mph": limit_mph}
    
    async def _set_valet_mode(self, enabled: bool, pin: Optional[str] = None) -> Dict[str, Any]:
        """Set valet mode."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.set_valet_mode(enabled, pin)
        return {"success": success, "valet_mode": enabled}
    
    async def _trigger_homelink(self) -> Dict[str, Any]:
        """Trigger homelink."""
        vehicle = await self.vehicle_context.get_vehicle()
        data = await vehicle.get_location_data()
        lat = data.get("latitude")
        lon = data.get("longitude")
        success = await vehicle.trigger_homelink(lat, lon)
        return {"success": success, "action": "trigger_homelink"}
    
    async def _schedule_software_update(self, offset_minutes: int = 0) -> Dict[str, Any]:
        """Schedule software update."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.schedule_software_update(offset_sec=offset_minutes * 60)
        return {"success": success, "offset_minutes": offset_minutes}
    
    async def _cancel_software_update(self) -> Dict[str, Any]:
        """Cancel software update."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.cancel_software_update()
        return {"success": success, "action": "cancel_software_update"}
    
    async def _navigate_to(self, destination: str) -> Dict[str, Any]:
        """Navigate to destination."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.navigation_request(destination)
        return {"success": success, "destination": destination}
    
    async def _navigate_to_supercharger(self, supercharger_id: int) -> Dict[str, Any]:
        """Navigate to supercharger."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.navigation_sc_request(supercharger_id)
        return {"success": success, "supercharger_id": supercharger_id}
    
    async def _set_climate_keeper_mode(self, mode: int) -> Dict[str, Any]:
        """Set climate keeper mode."""
        vehicle = await self.vehicle_context.get_vehicle()
        success = await vehicle.set_climate_keeper_mode(mode)
        mode_names = {0: "关闭", 1: "保持模式", 2: "宠物模式", 3: "露营模式"}
        return {"success": success, "mode": mode_names.get(mode, f"模式{mode}")}
    
    async def _set_seat_cooler(self, seat: int, level: int) -> Dict[str, Any]:
        """Set seat cooler (vehicles with ventilated seats only)."""
        vehicle = await self.vehicle_context.get_vehicle()
        if not getattr(vehicle, 'has_seat_cooling', False):
            return {"success": False, "error": "当前车辆未配备座椅通风功能"}
        if seat not in (0, 1):
            return {"success": False, "error": "座椅通风仅支持前排座位 (0=左, 1=右)"}
        success = await vehicle.set_seat_cooler(seat, level)
        return {"success": success, "seat": seat, "level": level}

    async def _set_bioweapon_mode(self, enabled: bool) -> Dict[str, Any]:
        """Set bioweapon defense mode (supported models only)."""
        vehicle = await self.vehicle_context.get_vehicle()
        if not getattr(vehicle, 'has_bioweapon_mode', False):
            return {"success": False, "error": "当前车辆不支持生物武器防御模式"}
        success = await vehicle.set_bioweapon_mode(enabled)
        return {"success": success, "bioweapon_mode": enabled}

    async def _get_vehicle_info(self) -> Dict[str, Any]:
        """Get vehicle hardware info and supported features."""
        vehicle = await self.vehicle_context.get_vehicle()
        platform = getattr(vehicle, 'platform_info', None)

        # Model name mapping
        model_names = {
            'model3': 'Model 3',
            'modely': 'Model Y',
            'models': 'Model S',
            'modelx': 'Model X',
            'cybertruck': 'Cybertruck',
            'semi': 'Semi',
            'roadster': 'Roadster',
        }

        if platform:
            model_type = platform.model_type
            refresh = platform.refresh_generation
            has_mcu3 = platform.has_mcu3
            has_hw4 = platform.has_hw4
            has_seat_cooling = platform.has_seat_cooling
            has_bioweapon_mode = platform.has_bioweapon_mode
        else:
            # Fallback to legacy properties
            model_type = getattr(vehicle, 'model_type', 'unknown')
            refresh = "unknown"
            has_mcu3 = getattr(vehicle, 'has_mcu3', False)
            has_hw4 = False
            has_seat_cooling = getattr(vehicle, 'has_seat_cooling', False)
            has_bioweapon_mode = getattr(vehicle, 'has_bioweapon_mode', False)

        # Generation name
        generation_names = {
            "highland": "焕新版 (Highland)",
            "juniper": "焕新版 (Juniper)",
            "refresh": "改款 (Refresh)",
            "pre_refresh": "旧款",
            "unknown": "未知",
        }
        generation = generation_names.get(refresh, refresh)

        # Hardware display names
        mcu_names = {
            "mcu1": "MCU1 (NVIDIA Tegra)",
            "mcu2": "MCU2 (Intel Atom)",
            "mcu3": "MCU3 (AMD Ryzen)",
            "unknown": "未知",
        }
        hw_names = {
            "hw1": "HW1 (Mobileye)",
            "hw2": "HW2",
            "hw2_5": "HW2.5",
            "hw3": "HW3 (AI3)",
            "hw4": "HW4 (AI4)",
            "unknown": "未知",
        }

        # Supported features
        features = {
            "基础控制": True,
            "空调控制": True,
            "充电控制": True,
            "座椅加热": True,
            "座椅通风": has_seat_cooling,
            "方向盘加热": True,
            "生物武器防御模式": has_bioweapon_mode,
            "宠物/露营模式": True,
            "新调度命令": has_mcu3,
            "窗户控制(无需坐标)": model_type in ("model3", "modely"),
            "导航命令": True,
            "媒体控制": True,
        }

        return {
            "display_name": vehicle.display_name,
            "vin": vehicle.vin,
            "model": model_names.get(model_type, model_type),
            "generation": generation,
            "mcu": mcu_names.get(getattr(vehicle, 'mcu_version', 'unknown'), "未知"),
            "hw": hw_names.get(getattr(vehicle, 'hw_version', 'unknown'), "未知"),
            "is_refreshed": refresh in ("highland", "juniper", "refresh"),
            "features": features,
        }
