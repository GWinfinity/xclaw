"""
Vehicle Monitor

Real-time vehicle monitoring using Fleet Telemetry.
"""

import asyncio
import json
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class VehicleEvent:
    """Vehicle telemetry event."""
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]


class VehicleMonitor:
    """
    Monitor vehicle state using Fleet Telemetry.
    
    Note: This requires Fleet Telemetry setup with Tesla.
    """
    
    def __init__(self, vehicle_context):
        self.vehicle_context = vehicle_context
        self._running = False
        self._callbacks: list[Callable[[VehicleEvent], None]] = []
        self._last_data: Optional[Dict[str, Any]] = None
    
    def on_event(self, callback: Callable[[VehicleEvent], None]):
        """Register event callback."""
        self._callbacks.append(callback)
    
    async def start(self, interval: int = 60):
        """
        Start monitoring vehicle.
        
        Args:
            interval: Polling interval in seconds (for REST API fallback)
        """
        self._running = True
        print(f"🚗 开始监控车辆 (间隔: {interval}秒)")
        
        while self._running:
            try:
                await self._check_vehicle()
            except Exception as e:
                print(f"⚠️ 监控错误: {e}")
            
            await asyncio.sleep(interval)
    
    def stop(self):
        """Stop monitoring."""
        self._running = False
        print("🛑 停止监控车辆")
    
    async def _check_vehicle(self):
        """Check vehicle state and emit events."""
        try:
            vehicle = await self.vehicle_context.get_vehicle()
            data = await vehicle.get_vehicle_data(wake_up_if_needed=False)
            
            current_data = {
                "battery_level": data.charge_state.battery_level,
                "charging_state": data.charge_state.charging_state.value,
                "locked": data.vehicle_state.locked,
                "sentry_mode": data.vehicle_state.sentry_mode,
                "inside_temp": data.climate_state.inside_temp,
                "is_climate_on": data.climate_state.is_climate_on,
                "latitude": data.drive_state.latitude,
                "longitude": data.drive_state.longitude,
                "speed": data.drive_state.speed,
            }
            
            if self._last_data:
                # Check for changes
                changes = self._detect_changes(self._last_data, current_data)
                for change_type, change_data in changes.items():
                    event = VehicleEvent(
                        timestamp=datetime.now(),
                        event_type=change_type,
                        data=change_data
                    )
                    await self._emit_event(event)
            
            self._last_data = current_data
            
        except Exception as e:
            # Vehicle might be offline
            pass
    
    def _detect_changes(
        self,
        old: Dict[str, Any],
        new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect changes between old and new data."""
        changes = {}
        
        # Battery level changes
        if old.get("battery_level") != new.get("battery_level"):
            changes["battery_change"] = {
                "old": old.get("battery_level"),
                "new": new.get("battery_level"),
            }
        
        # Charging state changes
        if old.get("charging_state") != new.get("charging_state"):
            changes["charging_change"] = {
                "old": old.get("charging_state"),
                "new": new.get("charging_state"),
            }
        
        # Lock state changes
        if old.get("locked") != new.get("locked"):
            changes["lock_change"] = {
                "locked": new.get("locked"),
            }
        
        # Climate changes
        if old.get("is_climate_on") != new.get("is_climate_on"):
            changes["climate_change"] = {
                "is_on": new.get("is_climate_on"),
            }
        
        # Location changes (if moving)
        old_lat = old.get("latitude")
        old_lon = old.get("longitude")
        new_lat = new.get("latitude")
        new_lon = new.get("longitude")
        
        if old_lat and old_lon and new_lat and new_lon:
            distance = self._haversine_distance(old_lat, old_lon, new_lat, new_lon)
            if distance > 0.1:  # Moved more than 100m
                changes["location_change"] = {
                    "distance_km": round(distance, 2),
                    "speed": new.get("speed"),
                }
        
        return changes
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two coordinates in km."""
        import math
        
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def _emit_event(self, event: VehicleEvent):
        """Emit event to all callbacks."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"⚠️ 回调错误: {e}")


class NotificationHandler:
    """Handle notifications for vehicle events."""
    
    def __init__(self, bot, chat_id: str):
        self.bot = bot
        self.chat_id = chat_id
    
    async def on_event(self, event: VehicleEvent):
        """Handle vehicle event."""
        messages = {
            "battery_change": self._battery_message,
            "charging_change": self._charging_message,
            "lock_change": self._lock_message,
            "climate_change": self._climate_message,
            "location_change": self._location_message,
        }
        
        handler = messages.get(event.event_type)
        if handler:
            message = handler(event.data)
            await self.bot.send_message(chat_id=self.chat_id, text=message)
    
    def _battery_message(self, data: Dict) -> str:
        old = data.get("old")
        new = data.get("new")
        delta = new - old
        emoji = "🔋" if delta < 0 else "⚡"
        return f"{emoji} 电池电量: {old}% → {new}% ({'+' if delta > 0 else ''}{delta}%)"
    
    def _charging_message(self, data: Dict) -> str:
        old = data.get("old")
        new = data.get("new")
        if new == "Charging":
            return "🔌 开始充电"
        elif new == "Complete":
            return "✅ 充电完成"
        elif new == "Stopped":
            return "⏹️ 充电停止"
        return f"充电状态: {old} → {new}"
    
    def _lock_message(self, data: Dict) -> str:
        locked = data.get("locked")
        return "🔒 车辆已锁定" if locked else "🔓 车辆已解锁"
    
    def _climate_message(self, data: Dict) -> str:
        is_on = data.get("is_on")
        return "❄️ 空调已开启" if is_on else "⭕ 空调已关闭"
    
    def _location_message(self, data: Dict) -> str:
        distance = data.get("distance_km")
        speed = data.get("speed")
        speed_str = f" 速度: {speed} km/h" if speed else ""
        return f"🚗 车辆移动: {distance} km{speed_str}"
