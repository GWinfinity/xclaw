"""
Tesla Vehicle

Vehicle-specific operations and data retrieval.
"""

import asyncio
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from .models import VehicleData
from .exceptions import VehicleUnavailableError, CommandFailedError

if TYPE_CHECKING:
    from .client import TeslaFleetClient


class Vehicle:
    """
    Represents a Tesla vehicle.
    
    Provides methods for controlling and monitoring the vehicle.
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
        
        # Cached vehicle data
        self._vehicle_data: Optional[VehicleData] = None
        self._data_timestamp: Optional[datetime] = None
    
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
    
    async def get_vehicle_data(self, wake_up_if_needed: bool = True) -> VehicleData:
        """
        Get complete vehicle data.
        
        Args:
            wake_up_if_needed: Whether to wake up vehicle if asleep
            
        Returns:
            VehicleData object
        """
        if self.state != "online" and wake_up_if_needed:
            await self.wake_up()
        
        data = await self._request("GET", "/vehicle_data")
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
    
    async def set_steering_wheel_heater(self, on: bool) -> bool:
        """Set steering wheel heater on/off."""
        result = await self._request(
            "POST",
            "/command/remote_steering_wheel_heater_request",
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
            lat: Current latitude (required for close)
            lon: Current longitude (required for close)
        """
        data = {"command": command}
        if lat is not None:
            data["lat"] = lat
        if lon is not None:
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
    
    def __repr__(self) -> str:
        return f"<Vehicle {self.display_name} ({self.vin})>"
