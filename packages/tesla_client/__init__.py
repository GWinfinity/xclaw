"""
Tesla Client for xClaw

Provides three layers of interaction with Tesla vehicles:

1. Fleet API Client (TeslaFleetClient / Vehicle)
   - Official Tesla REST API for commands and data
   - OAuth2 authentication, token refresh, 2026 endpoint updates

2. CAN Bus Client (BaseCANInterface and implementations)
   - Direct vehicle bus communication for low-latency state and research
   - Supports Mock, SocketCAN, ESP32 serial/TCP bridge, M5StickS3

3. AI Copilot (TeslaAICopilot)
   - Combines Fleet API + CAN state with any xClaw LLM adapter
   - Natural language Q&A, driving advice, safe command execution

Usage:
    # Fleet API only
    from packages.tesla_client import TeslaFleetClient
    client = TeslaFleetClient(region="cn")

    # CAN bus (M5StickS3 + external transceiver)
    from packages.tesla_client import M5StickS3Interface
    can = M5StickS3Interface(port="COM3", listen_only=True)
    await can.start_rx_loop()

    # AI Copilot
    from packages.tesla_client import TeslaAICopilot
    from packages.llm_adapters import LLMFactory
    llm = LLMFactory.create_from_env()
    copilot = TeslaAICopilot(vehicle=vehicle, llm_adapter=llm, can_interface=can)
    response = await copilot.ask("我应该现在充电吗？")
"""

from .client import TeslaFleetClient
from .vehicle import Vehicle
from .exceptions import (
    TeslaAPIError,
    AuthenticationError,
    VehicleUnavailableError,
    RateLimitError,
    CommandFailedError,
    InvalidParameterError,
    ServerError,
)
from .models import (
    VehicleData,
    ChargeState,
    ClimateState,
    DriveState,
    GuiSettings,
    VehicleState,
    VehicleConfig,
    TokenResponse,
)
from .platform import PlatformInfo, detect_platform
from .can_bus import (
    CANFrame,
    CANFrameType,
    BaseCANInterface,
    MockCANInterface,
    SocketCANInterface,
    ESP32SerialBridgeInterface,
    ESP32TCPBridgeInterface,
    M5StickS3Interface,
    create_can_interface,
)
from .can_frames import (
    TeslaCANParser,
    VehicleCANState,
    TeslaHWVersion,
    AutopilotState,
    ShiftState,
    get_can_id_name,
    build_fsd_unlock_frame,
    build_tlssc_restore_frame,
    build_nag_echo_frame,
)
from .ai_copilot import TeslaAICopilot, CopilotResponse

__version__ = "0.2.0"
__all__ = [
    # Fleet API
    "TeslaFleetClient",
    "Vehicle",
    "TeslaAPIError",
    "AuthenticationError",
    "VehicleUnavailableError",
    "RateLimitError",
    "CommandFailedError",
    "InvalidParameterError",
    "ServerError",
    "VehicleData",
    "ChargeState",
    "ClimateState",
    "DriveState",
    "GuiSettings",
    "VehicleState",
    "VehicleConfig",
    "TokenResponse",
    "PlatformInfo",
    "detect_platform",
    # CAN Bus
    "CANFrame",
    "CANFrameType",
    "BaseCANInterface",
    "MockCANInterface",
    "SocketCANInterface",
    "ESP32SerialBridgeInterface",
    "ESP32TCPBridgeInterface",
    "M5StickS3Interface",
    "create_can_interface",
    # CAN Frames
    "TeslaCANParser",
    "VehicleCANState",
    "TeslaHWVersion",
    "AutopilotState",
    "ShiftState",
    "get_can_id_name",
    "build_fsd_unlock_frame",
    "build_tlssc_restore_frame",
    "build_nag_echo_frame",
    # AI Copilot
    "TeslaAICopilot",
    "CopilotResponse",
]
