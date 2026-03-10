"""
Vehicle Context

Manages vehicle state and provides access to Tesla API client.
"""

import os
from typing import Optional

from packages.tesla_client import TeslaFleetClient, Vehicle


class VehicleContext:
    """
    Context for a specific vehicle.
    
    Provides:
    - Access to TeslaFleetClient
    - Vehicle instance management
    - Cached vehicle data
    
    Usage:
        context = VehicleContext(vin="5YJ3E1EA8PF...")
        vehicle = await context.get_vehicle()
        data = await context.get_vehicle_data()
    """
    
    def __init__(
        self,
        vin: Optional[str] = None,
        client: Optional[TeslaFleetClient] = None,
    ):
        """
        Initialize vehicle context.
        
        Args:
            vin: Vehicle VIN (or from env TESLA_VIN)
            client: TeslaFleetClient instance (or creates new one)
        """
        self.vin = vin or os.getenv("TESLA_VIN")
        self._client = client
        self._vehicle: Optional[Vehicle] = None
        self._cached_data = None
    
    async def _get_client(self) -> TeslaFleetClient:
        """Get or create Tesla client."""
        if self._client is None:
            self._client = TeslaFleetClient()
        return self._client
    
    async def get_vehicle(self) -> Vehicle:
        """
        Get the vehicle instance.
        
        Returns:
            Vehicle object
            
        Raises:
            ValueError: If vehicle not found
        """
        if self._vehicle is None:
            client = await self._get_client()
            
            if self.vin:
                self._vehicle = await client.get_vehicle(self.vin)
            else:
                # Get first available vehicle
                vehicles = await client.get_vehicles()
                if vehicles:
                    self._vehicle = vehicles[0]
                    self.vin = self._vehicle.vin
            
            if self._vehicle is None:
                raise ValueError("No vehicle found. Check TESLA_VIN or vehicle access.")
        
        return self._vehicle
    
    async def get_vehicle_data(self, refresh: bool = False):
        """
        Get vehicle data.
        
        Args:
            refresh: Force refresh cached data
            
        Returns:
            VehicleData object
        """
        if self._cached_data is None or refresh:
            vehicle = await self.get_vehicle()
            self._cached_data = await vehicle.get_vehicle_data()
        return self._cached_data
    
    async def refresh_data(self):
        """Refresh cached vehicle data."""
        self._cached_data = None
        return await self.get_vehicle_data()
    
    @property
    def display_name(self) -> Optional[str]:
        """Get vehicle display name."""
        if self._vehicle:
            return self._vehicle.display_name
        return None
    
    async def close(self):
        """Close client connection."""
        if self._client:
            await self._client.close()
