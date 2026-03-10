"""
Tesla Fleet API Client for xClaw

A Python client for Tesla Fleet API, providing easy-to-use interfaces
for vehicle control and data retrieval.
"""

from .client import TeslaFleetClient
from .vehicle import Vehicle
from .exceptions import (
    TeslaAPIError,
    AuthenticationError,
    VehicleUnavailableError,
    RateLimitError,
    CommandFailedError,
)
from .models import (
    VehicleData,
    ChargeState,
    ClimateState,
    DriveState,
    GuiSettings,
    VehicleState,
    VehicleConfig,
)

__version__ = "0.1.0"
__all__ = [
    "TeslaFleetClient",
    "Vehicle",
    "TeslaAPIError",
    "AuthenticationError",
    "VehicleUnavailableError",
    "RateLimitError",
    "CommandFailedError",
    "VehicleData",
    "ChargeState",
    "ClimateState",
    "DriveState",
    "GuiSettings",
    "VehicleState",
    "VehicleConfig",
]
