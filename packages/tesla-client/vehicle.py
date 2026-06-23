"""
Tesla Vehicle

Vehicle-specific operations and data retrieval.
Updated for 2026 Fleet API with full Model 3/Y support.

New commands added:
- Navigation (navigation_gps_request, navigation_sc_request, navigation_waypoints_request)
- Scheduling (add_charge_schedule, add_precondition_schedule, remove_*)
- Climate (set_climate_keeper_mode, set_bioweapon_mode, set_cabin_overheat_protection)
- Seats (remote_auto_seat_climate_request, remote_seat_cooler_request)
- Media (media_toggle_playback, media_next_track, adjust_volume)
- Security (guest_mode, erase_user_data, set_vehicle_name)
"""

import asyncio
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime

from .models import VehicleData
from .exceptions import VehicleUnavailableError, CommandFailedError

if TYPE_CHECKING:
    from .client import TeslaFleetClient


class Vehicle:
    """
    Represents a Tesla vehicle.
    
    Provides methods for controlling and monitoring the vehicle.
    Updated for 2026 Fleet API with full Model 3/Y support.
    """
    
    def __init__(self, client: "TeslaFleetClient", data: Dict[str, Any]):
        """
        Initialize vehicle.
        
        Args:
            client: TeslaFleetClient instance
            data: Vehicle data from API
        """
        self._client = client
        self._data = data
        
        # Basic info
        self.id = data.get("id")
        self.vehicle_id = data.get("vehicle_id")
        self.vin = data.get("vin")
        self.display_name = data.get("display_name")
        self.state = data.get("state")  # online, asleep, offline
        self.in_service = data.get("in_service", False)
        
        # Vehicle type detection
        self.model_type = self._detect_model_type()
        
        # Cached vehicle data
        self._vehicle_data: Optional[VehicleData] = None
        self._data_timestamp: Optional[datetime] = None
    
    def _detect_model_type(self) -> str:
        """Detect vehicle model type from VIN."""
        if not self.vin or len(self.vin) < 7:
            return "unknown"
        
        # VIN position 4-7 indicates model
        vin_mid = self.vin[3:7]
        
        # Model 3: 5YJ3E (2017-2023) or LRW3E (2024+ Highland)
        if "5YJ3" in vin_mid or "LRW3" in vin_mid:
            return "model3"
        # Model Y: 5YJY (2020-2024) or LRWY (2025+ Juniper)
        elif "5YJY" in vin_mid or "LRWY" in vin_mid:
            return "modely"
        # Model S: 5YJS
        elif "5YJS" in vin_mid:
            return "models"
        # Model X: 5YJX
        elif "5YJX" in vin_mid:
            return "modelx"
        # Cybertruck: 7G2C
        elif "7G2C" in vin_mid:
            return "cybertruck"
        
        return "unknown"
    
    def _detect_hardware_generation(self) -> str:
        """Detect hardware generation from VIN and firmware."""
        if not self.vin or len(self.vin) < 10:
            return "unknown"
        
        # VIN 10th character indicates model year
        year_char = self.vin[9]
        
        # New VIN patterns (LRW prefix) = MCU3/HW4
        if self.vin.startswith("LRW"):
            return "hw4_mcu3"
        
        # Old VIN patterns with year >= 2024 = likely HW4
        if year_char in ("R", "S", "T"):  # 2024, 2025, 2026
            return "hw4_mcu3"
        
        # 2023 and earlier = MCU2/HW3
        return "hw3_mcu2"
    
    @property
    def is_model3(self) -> bool:
        """Check if vehicle is Model 3."""
        return self.model_type == "model3"
    
    @property
    def is_modely(self) -> bool:
        """Check if vehicle is Model Y."""
        return self.model_type == "modely"
    
    @property
    def is_highland(self) -> bool:
        """Check if vehicle is Model 3 Highland (2023+ refresh)."""
        return self.model_type == "model3" and self.vin.startswith("LRW")
    
    @property
    def is_juniper(self) -> bool:
        """Check if vehicle is Model Y Juniper (2025+ refresh)."""
        return self.model_type == "modely" and self.vin.startswith("LRW")
    
    @property
    def is_refreshed(self) -> bool:
        """Check if vehicle is a refreshed model (Highland or Juniper)."""
        return self.is_highland or self.is_juniper
    
    @property
    def has_mcu3(self) -> bool:
        """Check if vehicle has MCU3 (AMD Ryzen)."""
        hw = self._detect_hardware_generation()
        return hw == "hw4_mcu3"
    
    @property
    def has_seat_cooling(self) -> bool:
        """Check if vehicle has ventilated seats."""
        # MCU3 vehicles (Highland/Juniper) have ventilated seats
        return self.has_mcu3
    
    @property
    def has_bioweapon_mode(self) -> bool:
        """Check if vehicle has Bioweapon Defense Mode."""
        # Available on refreshed models
        return self.is_refreshed
    
    @property
    def is_m3_platform(self) -> bool:
        """Check if vehicle is on M3/MY platform (no lat/lon required for window close)."""
        return self.model_type in ("model3", "modely")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request for this vehicle."""
        full_endpoint = f"/api/1/vehicles/{self.id}{endpoint}"
        return await self._client._request(method, full_endpoint, **kwargs)
    
    async def wake_up(self, timeout: int = 60) -> bool:
        """
        Wake up the vehicle.
        
        Args:
            timeout: Maximum time to wait for vehicle to wake up (seconds)
            
        Returns:
            True if vehicle is awake, False otherwise
        """
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).seconds < timeout:
            try:
                result = await self._request("POST", "/wake_up")
                self.state = result.get("response", {}).get("state", self.state)
                
                if self.state == "online":
                    return True
                    
            except VehicleUnavailableError:
                pass
            
            await asyncio.sleep(2)
        
        return False
    
    async def get_vehicle_data(
        self,
        wake_up_if_needed: bool = True,
        endpoints: Optional[str] = None,
    ) -> VehicleData:
        """
        Get complete vehicle data.
        
        Args:
            wake_up_if_needed: Whether to wake up vehicle if asleep
            endpoints: Specific endpoints to query (e.g., "charge_state;climate_state")
            
        Returns:
            VehicleData object
        """
        if self.state != "online" and wake_up_if_needed:
            await self.wake_up()
        
        endpoint = "/vehicle_data"
        if endpoints:
            endpoint += f"?endpoints={endpoints}"
        
        data = await self._request("GET", endpoint)
        self._vehicle_data = VehicleData(**data.get("response", {}))
        self._data_timestamp = datetime.utcnow()
        return self._vehicle_data
    
    async def get_location_data(self) -> Dict[str, Any]:
        """
        Get vehicle location data only.
        
        Returns:
            Location data dictionary
        """
        data = await self._request("GET", "/vehicle_data?endpoints=location_data")
        return data.get("response", {}).get("drive_state", {})
    
    async def get_charge_state(self) -> Dict[str, Any]:
        """
        Get charging state only.
        
        Returns:
            Charge state dictionary
        """
        data = await self._request("GET", "/vehicle_data?endpoints=charge_state")
        return data.get("response", {}).get("charge_state", {})
    
    async def get_climate_state(self) -> Dict[str, Any]:
        """
        Get climate state only.
        
        Returns:
            Climate state dictionary
        """
        data = await self._request("GET", "/vehicle_data?endpoints=climate_state")
        return data.get("response", {}).get("climate_state", {})
    
    async def get_vehicle_state(self) -> Dict[str, Any]:
        """
        Get vehicle state only.
        
        Returns:
            Vehicle state dictionary
        """
        data = await self._request("GET", "/vehicle_data?endpoints=vehicle_state")
        return data.get("response", {}).get("vehicle_state", {})
    
    # ==================== Vehicle Commands ====================
    
    async def lock_doors(self) -> bool:
        """Lock the vehicle doors."""
        result = await self._request("POST", "/command/door_lock")
        return result.get("response", {}).get("result", False)
    
    async def unlock_doors(self) -> bool:
        """Unlock the vehicle doors."""
        result = await self._request("POST", "/command/door_unlock")
        return result.get("response", {}).get("result", False)
    
    async def honk_horn(self) -> bool:
        """Honk the horn."""
        result = await self._request("POST", "/command/honk_horn")
        return result.get("response", {}).get("result", False)
    
    async def flash_lights(self) -> bool:
        """Flash the lights."""
        result = await self._request("POST", "/command/flash_lights")
        return result.get("response", {}).get("result", False)
    
    # ==================== Climate Commands ====================
    
    async def auto_conditioning_start(self) -> bool:
        """Start auto conditioning (HVAC)."""
        result = await self._request("POST", "/command/auto_conditioning_start")
        return result.get("response", {}).get("result", False)
    
    async def auto_conditioning_stop(self) -> bool:
        """Stop auto conditioning (HVAC)."""
        result = await self._request("POST", "/command/auto_conditioning_stop")
        return result.get("response", {}).get("result", False)
    
    async def set_climate_temperature(
        self,
        driver_temp: float,
        passenger_temp: Optional[float] = None
    ) -> bool:
        """
        Set climate temperature.
        
        Args:
            driver_temp: Driver side temperature (in Celsius)
            passenger_temp: Passenger side temperature (defaults to driver_temp)
        """
        if passenger_temp is None:
            passenger_temp = driver_temp
        
        result = await self._request(
            "POST",
            "/command/set_temps",
            json={
                "driver_temp": driver_temp,
                "passenger_temp": passenger_temp,
            }
        )
        return result.get("response", {}).get("result", False)
    
    async def set_seat_heater(
        self,
        seat: int,  # 0=front left, 1=front right, 2=rear left, 4=rear center, 5=rear right
        level: int  # 0-3 (0=off, 3=high)
    ) -> bool:
        """
        Set seat heater level.
        
        Args:
            seat: Seat position (0-5)
            level: Heat level (0-3)
        """
        result = await self._request(
            "POST",
            "/command/remote_seat_heater_request",
            json={"heater": seat, "level": level}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_seat_cooler(
        self,
        seat: int,  # 0=front left, 1=front right
        level: int  # 0-3 (0=off, 3=max)
    ) -> bool:
        """
        Set seat cooling level (Model 3/Y with ventilated seats).
        
        Args:
            seat: Seat position (0-1)
            level: Cooling level (0-3)
        """
        result = await self._request(
            "POST",
            "/command/remote_seat_cooler_request",
            json={"seat_position": seat, "seat_cooler_level": level}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_auto_seat_climate(
        self,
        seat: int,
        auto: bool,
        temp: Optional[float] = None,
    ) -> bool:
        """
        Set automatic seat heating/cooling.
        Requires preconditioning or climate keeper to be on.
        
        Args:
            seat: Seat position (0-5)
            auto: Enable/disable auto mode
            temp: Target seat temperature (optional)
        """
        data = {"seat_position": seat, "auto_seat": int(auto)}
        if temp is not None:
            data["seat_temp"] = temp
        result = await self._request(
            "POST",
            "/command/remote_auto_seat_climate_request",
            json=data
        )
        return result.get("response", {}).get("result", False)
    
    async def set_steering_wheel_heater(self, on: bool) -> bool:
        """Set steering wheel heater on/off."""
        result = await self._request(
            "POST",
            "/command/remote_steering_wheel_heater_request",
            json={"on": on}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_steering_wheel_heat_level(self, level: int) -> bool:
        """
        Set steering wheel heat level (0-3).
        Requires preconditioning or climate keeper to be on.
        """
        result = await self._request(
            "POST",
            "/command/remote_steering_wheel_heat_level_request",
            json={"level": level}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_auto_steering_wheel_heat(self, auto: bool) -> bool:
        """
        Set automatic steering wheel heating.
        Requires preconditioning or climate keeper to be on.
        """
        result = await self._request(
            "POST",
            "/command/remote_auto_steering_wheel_heat_climate_request",
            json={"auto_steering_wheel_heat": int(auto)}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_climate_keeper_mode(self, mode: int) -> bool:
        """
        Set climate keeper mode.
        
        Args:
            mode: 0=Off, 1=Keep Mode, 2=Dog Mode, 3=Camp Mode
        """
        result = await self._request(
            "POST",
            "/command/set_climate_keeper_mode",
            json={"climate_keeper_mode": mode}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_bioweapon_mode(self, on: bool) -> bool:
        """Toggle Bioweapon Defense Mode."""
        result = await self._request(
            "POST",
            "/command/set_bioweapon_mode",
            json={"on": on}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_cabin_overheat_protection(self, on: bool) -> bool:
        """Toggle Cabin Overheat Protection."""
        result = await self._request(
            "POST",
            "/command/set_cabin_overheat_protection",
            json={"on": on}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_cop_temp(self, level: int) -> bool:
        """
        Set Cabin Overheat Protection temperature.
        
        Args:
            level: 0=Low (30C), 1=Medium (35C), 2=High (40C)
        """
        result = await self._request(
            "POST",
            "/command/set_cop_temp",
            json={"cop_temp": level}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_preconditioning_max(self, on: bool) -> bool:
        """Set preconditioning to max."""
        result = await self._request(
            "POST",
            "/command/set_preconditioning_max",
            json={"on": on}
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Charging Commands ====================
    
    async def charge_port_door_open(self) -> bool:
        """Open charge port door."""
        result = await self._request("POST", "/command/charge_port_door_open")
        return result.get("response", {}).get("result", False)
    
    async def charge_port_door_close(self) -> bool:
        """Close charge port door."""
        result = await self._request("POST", "/command/charge_port_door_close")
        return result.get("response", {}).get("result", False)
    
    async def charge_start(self) -> bool:
        """Start charging."""
        result = await self._request("POST", "/command/charge_start")
        return result.get("response", {}).get("result", False)
    
    async def charge_stop(self) -> bool:
        """Stop charging."""
        result = await self._request("POST", "/command/charge_stop")
        return result.get("response", {}).get("result", False)
    
    async def charge_standard(self) -> bool:
        """Charge in Standard mode."""
        result = await self._request("POST", "/command/charge_standard")
        return result.get("response", {}).get("result", False)
    
    async def charge_max_range(self) -> bool:
        """Charge in Max Range mode (for long trips)."""
        result = await self._request("POST", "/command/charge_max_range")
        return result.get("response", {}).get("result", False)
    
    async def set_charge_limit(self, percent: int) -> bool:
        """
        Set charge limit percentage.
        
        Args:
            percent: Charge limit (50-100)
        """
        result = await self._request(
            "POST",
            "/command/set_charge_limit",
            json={"percent": percent}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_charging_amps(self, amps: int) -> bool:
        """
        Set charging amps.
        
        Args:
            amps: Amperage (0-32 typically)
        """
        result = await self._request(
            "POST",
            "/command/set_charging_amps",
            json={"charging_amps": amps}
        )
        return result.get("response", {}).get("result", False)
    
    async def add_charge_schedule(
        self,
        time: int,
        days: Optional[List[int]] = None,
        enabled: bool = True,
    ) -> bool:
        """
        Add a charge schedule (replaces set_scheduled_charging for firmware 2024.26+).
        
        Args:
            time: Minutes after midnight (e.g., 120 = 2:00 AM)
            days: List of days (0=Sun, 1=Mon, ..., 6=Sat)
            enabled: Whether schedule is enabled
        """
        data = {"time": time, "enabled": enabled}
        if days:
            data["days"] = days
        result = await self._request(
            "POST",
            "/command/add_charge_schedule",
            json=data
        )
        return result.get("response", {}).get("result", False)
    
    async def remove_charge_schedule(self, schedule_id: int) -> bool:
        """Remove a charge schedule by ID."""
        result = await self._request(
            "POST",
            "/command/remove_charge_schedule",
            json={"id": schedule_id}
        )
        return result.get("response", {}).get("result", False)
    
    async def add_precondition_schedule(
        self,
        time: int,
        days: Optional[List[int]] = None,
        enabled: bool = True,
    ) -> bool:
        """
        Add a precondition schedule (replaces set_scheduled_departure for firmware 2024.26+).
        
        Args:
            time: Minutes after midnight
            days: List of days (0=Sun, 1=Mon, ..., 6=Sat)
            enabled: Whether schedule is enabled
        """
        data = {"time": time, "enabled": enabled}
        if days:
            data["days"] = days
        result = await self._request(
            "POST",
            "/command/add_precondition_schedule",
            json=data
        )
        return result.get("response", {}).get("result", False)
    
    async def remove_precondition_schedule(self, schedule_id: int) -> bool:
        """Remove a precondition schedule by ID."""
        result = await self._request(
            "POST",
            "/command/remove_precondition_schedule",
            json={"id": schedule_id}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_scheduled_charging(self, time: int, enable: bool = True) -> bool:
        """
        Set scheduled charging (legacy, prefer add_charge_schedule for firmware 2024.26+).
        
        Args:
            time: Minutes after midnight
            enable: Enable/disable
        """
        result = await self._request(
            "POST",
            "/command/set_scheduled_charging",
            json={"time": time, "enable": enable}
        )
        return result.get("response", {}).get("result", False)
    
    async def set_scheduled_departure(
        self,
        departure_time: int,
        enable: bool = True,
        preconditioning_enabled: bool = True,
        off_peak_charging_enabled: bool = False,
        end_off_peak_time: Optional[int] = None,
    ) -> bool:
        """
        Set scheduled departure (legacy, prefer add_precondition_schedule for firmware 2024.26+).
        
        Args:
            departure_time: Minutes after midnight
            enable: Enable/disable
            preconditioning_enabled: Enable preconditioning
            off_peak_charging_enabled: Enable off-peak charging
            end_off_peak_time: End of off-peak time (minutes after midnight)
        """
        data = {
            "departure_time": departure_time,
            "enable": enable,
            "preconditioning_enabled": preconditioning_enabled,
            "off_peak_charging_enabled": off_peak_charging_enabled,
        }
        if end_off_peak_time is not None:
            data["end_off_peak_time"] = end_off_peak_time
        result = await self._request(
            "POST",
            "/command/set_scheduled_departure",
            json=data
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Trunk & Frunk Commands ====================
    
    async def actuate_trunk(self, which_trunk: str = "rear") -> bool:
        """
        Open/close trunk or frunk.
        
        Args:
            which_trunk: "rear" for trunk, "front" for frunk
        """
        result = await self._request(
            "POST",
            "/command/actuate_trunk",
            json={"which_trunk": which_trunk}
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Windows Commands ====================
    
    async def window_control(
        self,
        command: str,  # "vent" or "close"
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> bool:
        """
        Control windows (vent or close).
        
        Args:
            command: "vent" or "close"
            lat: Current latitude (required for close on non-M3/MY platform)
            lon: Current longitude (required for close on non-M3/MY platform)
        """
        data = {"command": command}
        # M3/MY platform doesn't require lat/lon for close
        if not self.is_m3_platform and lat is not None:
            data["lat"] = lat
        if not self.is_m3_platform and lon is not None:
            data["lon"] = lon
        
        result = await self._request("POST", "/command/window_control", json=data)
        return result.get("response", {}).get("result", False)
    
    # ==================== Sentry Mode Commands ====================
    
    async def set_sentry_mode(self, on: bool) -> bool:
        """
        Enable/disable Sentry Mode.
        
        Args:
            on: True to enable, False to disable
        """
        result = await self._request(
            "POST",
            "/command/set_sentry_mode",
            json={"on": on}
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Speed Limit Mode Commands ====================
    
    async def speed_limit_activate(self, pin: str) -> bool:
        """Activate Speed Limit Mode."""
        result = await self._request(
            "POST",
            "/command/speed_limit_activate",
            json={"pin": pin}
        )
        return result.get("response", {}).get("result", False)
    
    async def speed_limit_deactivate(self, pin: str) -> bool:
        """Deactivate Speed Limit Mode."""
        result = await self._request(
            "POST",
            "/command/speed_limit_deactivate",
            json={"pin": pin}
        )
        return result.get("response", {}).get("result", False)
    
    async def speed_limit_set_limit(self, limit_mph: int) -> bool:
        """
        Set speed limit.
        
        Args:
            limit_mph: Speed limit in MPH
        """
        result = await self._request(
            "POST",
            "/command/speed_limit_set_limit",
            json={"limit_mph": limit_mph}
        )
        return result.get("response", {}).get("result", False)
    
    async def speed_limit_clear_pin(self, pin: str) -> bool:
        """Clear Speed Limit PIN."""
        result = await self._request(
            "POST",
            "/command/speed_limit_clear_pin",
            json={"pin": pin}
        )
        return result.get("response", {}).get("result", False)
    
    async def speed_limit_clear_pin_admin(self) -> bool:
        """Clear Speed Limit PIN (admin, firmware 2023.38+)."""
        result = await self._request("POST", "/command/speed_limit_clear_pin_admin")
        return result.get("response", {}).get("result", False)
    
    # ==================== Remote Start ====================
    
    async def remote_start_drive(self, password: str) -> bool:
        """
        Enable remote start (keyless driving).
        
        Args:
            password: Tesla account password
        """
        result = await self._request(
            "POST",
            "/command/remote_start_drive",
            json={"password": password}
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Valet Mode ====================
    
    async def set_valet_mode(self, on: bool, pin: Optional[str] = None) -> bool:
        """
        Enable/disable Valet Mode.
        
        Args:
            on: True to enable, False to disable
            pin: 4-digit PIN (required when enabling)
        """
        data = {"on": on}
        if pin:
            data["password"] = pin
        
        result = await self._request("POST", "/command/set_valet_mode", json=data)
        return result.get("response", {}).get("result", False)
    
    async def reset_valet_pin(self) -> bool:
        """Reset Valet Mode PIN (must be disabled first)."""
        result = await self._request("POST", "/command/reset_valet_pin")
        return result.get("response", {}).get("result", False)
    
    # ==================== PIN to Drive ====================
    
    async def set_pin_to_drive(self, pin: str) -> bool:
        """Set PIN to Drive."""
        result = await self._request(
            "POST",
            "/command/set_pin_to_drive",
            json={"on": True, "pin": pin}
        )
        return result.get("response", {}).get("result", False)
    
    async def reset_pin_to_drive_pin(self) -> bool:
        """Reset PIN to Drive (must be disabled)."""
        result = await self._request("POST", "/command/reset_pin_to_drive_pin")
        return result.get("response", {}).get("result", False)
    
    async def clear_pin_to_drive_admin(self) -> bool:
        """Clear PIN to Drive (admin, firmware 2023.44+)."""
        result = await self._request("POST", "/command/clear_pin_to_drive_admin")
        return result.get("response", {}).get("result", False)
    
    # ==================== Homelink ====================
    
    async def trigger_homelink(
        self,
        lat: float,
        lon: float,
        token: Optional[str] = None
    ) -> bool:
        """
        Trigger Homelink (garage door opener).
        
        Args:
            lat: Current latitude
            lon: Current longitude
            token: Optional device token
        """
        data = {"lat": lat, "lon": lon}
        if token:
            data["token"] = token
        
        result = await self._request("POST", "/command/trigger_homelink", json=data)
        return result.get("response", {}).get("result", False)
    
    # ==================== Software Update ====================
    
    async def schedule_software_update(self, offset_sec: int = 0) -> bool:
        """
        Schedule software update.
        
        Args:
            offset_sec: Seconds from now to schedule update
        """
        result = await self._request(
            "POST",
            "/command/schedule_software_update",
            json={"offset_sec": offset_sec}
        )
        return result.get("response", {}).get("result", False)
    
    async def cancel_software_update(self) -> bool:
        """Cancel scheduled software update."""
        result = await self._request("POST", "/command/cancel_software_update")
        return result.get("response", {}).get("result", False)
    
    # ==================== Navigation Commands ====================
    
    async def navigation_gps_request(
        self,
        lat: float,
        lon: float,
        order: int = 0,
    ) -> bool:
        """
        Start navigation to GPS coordinates.
        
        Args:
            lat: Destination latitude
            lon: Destination longitude
            order: Order of multiple stops
        """
        result = await self._request(
            "POST",
            "/command/navigation_gps_request",
            json={"lat": lat, "lon": lon, "order": order}
        )
        return result.get("response", {}).get("result", False)
    
    async def navigation_request(
        self,
        query: str,
        locale: str = "zh-CN",
    ) -> bool:
        """
        Send a location to the in-vehicle navigation system.
        
        Args:
            query: Location query (address or place name)
            locale: Locale for the query
        """
        result = await self._request(
            "POST",
            "/command/navigation_request",
            json={"query": query, "locale": locale}
        )
        return result.get("response", {}).get("result", False)
    
    async def navigation_sc_request(self, id: int) -> bool:
        """
        Start navigation to a supercharger.
        
        Args:
            id: Supercharger ID
        """
        result = await self._request(
            "POST",
            "/command/navigation_sc_request",
            json={"id": id}
        )
        return result.get("response", {}).get("result", False)
    
    async def navigation_waypoints_request(
        self,
        waypoints: List[Dict[str, float]],
    ) -> bool:
        """
        Send a list of waypoints to the vehicle's navigation system.
        
        Args:
            waypoints: List of {"lat": float, "lon": float} dicts
        """
        result = await self._request(
            "POST",
            "/command/navigation_waypoints_request",
            json={"waypoints": waypoints}
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Media Commands ====================
    
    async def media_toggle_playback(self) -> bool:
        """Toggle media play/pause."""
        result = await self._request("POST", "/command/media_toggle_playback")
        return result.get("response", {}).get("result", False)
    
    async def media_next_track(self) -> bool:
        """Next track."""
        result = await self._request("POST", "/command/media_next_track")
        return result.get("response", {}).get("result", False)
    
    async def media_prev_track(self) -> bool:
        """Previous track."""
        result = await self._request("POST", "/command/media_prev_track")
        return result.get("response", {}).get("result", False)
    
    async def media_next_fav(self) -> bool:
        """Next favorite track."""
        result = await self._request("POST", "/command/media_next_fav")
        return result.get("response", {}).get("result", False)
    
    async def media_prev_fav(self) -> bool:
        """Previous favorite track."""
        result = await self._request("POST", "/command/media_prev_fav")
        return result.get("response", {}).get("result", False)
    
    async def adjust_volume(self, volume: float) -> bool:
        """
        Adjust media volume.
        
        Args:
            volume: Volume level (0.0 - 1.0)
        """
        result = await self._request(
            "POST",
            "/command/adjust_volume",
            json={"volume": volume}
        )
        return result.get("response", {}).get("result", False)
    
    async def media_volume_down(self) -> bool:
        """Decrease volume by one."""
        result = await self._request("POST", "/command/media_volume_down")
        return result.get("response", {}).get("result", False)
    
    # ==================== Guest Mode ====================
    
    async def set_guest_mode(self, on: bool) -> bool:
        """
        Toggle Guest Mode (for valets, firmware 2024.14+).
        
        Args:
            on: True to enable, False to disable
        """
        result = await self._request(
            "POST",
            "/command/guest_mode",
            json={"on": on}
        )
        return result.get("response", {}).get("result", False)
    
    async def erase_user_data(self) -> bool:
        """Erase user data from vehicle UI (requires Guest Mode)."""
        result = await self._request("POST", "/command/erase_user_data")
        return result.get("response", {}).get("result", False)
    
    # ==================== Vehicle Name ====================
    
    async def set_vehicle_name(self, name: str) -> bool:
        """
        Change vehicle name.
        
        Args:
            name: New vehicle name
        """
        result = await self._request(
            "POST",
            "/command/set_vehicle_name",
            json={"vehicle_name": name}
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Sunroof ====================
    
    async def sun_roof_control(self, state: str) -> bool:
        """
        Control sunroof (if equipped).
        
        Args:
            state: "stop", "close", or "vent"
        """
        result = await self._request(
            "POST",
            "/command/sun_roof_control",
            json={"state": state}
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Boombox ====================
    
    async def remote_boombox(self, sound: int = 2000) -> bool:
        """
        Play sound through external speaker.
        
        Args:
            sound: Sound ID (0=random fart, 2000=locate ping)
        """
        result = await self._request(
            "POST",
            "/command/remote_boombox",
            json={"sound": sound}
        )
        return result.get("response", {}).get("result", False)
    
    # ==================== Calendar ====================
    
    async def upcoming_calendar_entries(self) -> Dict[str, Any]:
        """Get upcoming calendar entries from vehicle."""
        result = await self._request("POST", "/command/upcoming_calendar_entries")
        return result.get("response", {})
    
    def __repr__(self) -> str:
        return f"<Vehicle {self.display_name} ({self.vin}) [{self.model_type}]>"
