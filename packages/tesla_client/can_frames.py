"""
Tesla CAN Frame Definitions and Parser

Constants and parsers derived from community research (flipper-tesla-fsd,
commaai/opendbc, ev-open-can-tools). This module is read-only and only
manipulates UI/configuration frames when explicitly requested by higher
layers.

All IDs are in standard (11-bit) format unless noted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ============== CAN IDs ==============
# RX / state reading
CAN_ID_GTW_CAR_CONFIG = 0x398  # GTW_carConfig: HW detection
CAN_ID_GTW_CAR_STATE = 0x318  # GTW_carState: OTA detection
CAN_ID_DAS_STATUS = 0x39B  # DAS_status: AP state, nag level (HW4/Highland)
CAN_ID_ISA_SPEED = 0x399  # ISA_speedLimit on HW4; DAS_status on HW3/Legacy
CAN_ID_BMS_HV_BUS = 0x132  # BMS_hvBusStatus
CAN_ID_BMS_SOC = 0x292  # BMS_socStatus
CAN_ID_BMS_THERMAL = 0x312  # BMS_thermalStatus
CAN_ID_UI_RATED_CONSUMPTION = 0x33A  # UI_ratedConsumption (Wh/km)
CAN_ID_EPAS_STATUS = 0x370  # EPAS3P_sysStatus (Party CAN)

# TX / modification targets (use with extreme caution)
CAN_ID_UI_AUTOPILOT_CONTROL = 0x3FD  # UI_autopilotControl (FSD unlock bits)
CAN_ID_UI_DRIVER_ASSIST = 0x3F8  # UI_driverAssistControl
CAN_ID_DAS_CONFIG = 0x331  # DAS_autopilotConfig (TLSSC restore)
CAN_ID_GTW_CONFIG = 0x7FF  # GTW_carConfig replay/override
CAN_ID_UI_TRIP_PLANNING = 0x082  # UI_tripPlanning (precondition)
CAN_ID_VCLEFT_SWITCH = 0x3C2  # VCLEFT_switchStatus (ScrollPress AP, beta)
CAN_ID_UI_AP_LEGACY = 0x3EE  # UI_autopilotControl Legacy HW1/HW2


class TeslaHWVersion(str, Enum):
    """Autopilot hardware version."""

    HW1 = "hw1"
    HW2 = "hw2"
    HW2_5 = "hw2_5"
    HW3 = "hw3"
    HW4 = "hw4"
    UNKNOWN = "unknown"


class AutopilotState(str, Enum):
    """DAS autopilot engagement state."""

    OFF = "off"
    STANDBY = "standby"
    ENGAGED = "engaged"
    UNKNOWN = "unknown"


class ShiftState(str, Enum):
    """Gear shift state (from Fleet API fallback)."""

    PARK = "P"
    REVERSE = "R"
    NEUTRAL = "N"
    DRIVE = "D"
    UNKNOWN = "?"


@dataclass
class VehicleCANState:
    """Aggregated vehicle state parsed from CAN frames."""

    # Platform
    hw_version: TeslaHWVersion = TeslaHWVersion.UNKNOWN
    das_hw: int = -1

    # Battery
    battery_voltage: Optional[float] = None  # V
    battery_current: Optional[float] = None  # A
    battery_soc: Optional[float] = None  # %
    battery_temp_min: Optional[float] = None  # C
    battery_temp_max: Optional[float] = None  # C
    wh_per_km: Optional[float] = None

    # Drive
    speed: Optional[float] = None  # km/h ( Fleet API preferred)
    steering_angle: Optional[float] = None  # deg
    motor_torque: Optional[float] = None  # Nm
    brake_pressed: Optional[bool] = None
    shift_state: ShiftState = ShiftState.UNKNOWN

    # Autopilot
    autopilot_state: AutopilotState = AutopilotState.UNKNOWN
    hands_on_level: Optional[int] = None
    lane_change_state: Optional[int] = None
    blind_spot_warning: Optional[bool] = None
    fcw_enabled: Optional[bool] = None
    vision_speed_limit: Optional[float] = None

    # GTW
    gtw_autopilot_tier: Optional[str] = None
    ota_in_progress: bool = False

    # Diagnostics / counters
    epas_counter: Optional[int] = None
    modified_frame_count: int = 0

    # Metadata
    last_updated: Dict[int, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "hw_version": self.hw_version.value,
            "das_hw": self.das_hw,
            "battery_voltage": self.battery_voltage,
            "battery_current": self.battery_current,
            "battery_soc": self.battery_soc,
            "battery_temp_min": self.battery_temp_min,
            "battery_temp_max": self.battery_temp_max,
            "wh_per_km": self.wh_per_km,
            "speed": self.speed,
            "steering_angle": self.steering_angle,
            "motor_torque": self.motor_torque,
            "brake_pressed": self.brake_pressed,
            "shift_state": self.shift_state.value,
            "autopilot_state": self.autopilot_state.value,
            "hands_on_level": self.hands_on_level,
            "lane_change_state": self.lane_change_state,
            "blind_spot_warning": self.blind_spot_warning,
            "fcw_enabled": self.fcw_enabled,
            "vision_speed_limit": self.vision_speed_limit,
            "gtw_autopilot_tier": self.gtw_autopilot_tier,
            "ota_in_progress": self.ota_in_progress,
            "epas_counter": self.epas_counter,
            "modified_frame_count": self.modified_frame_count,
        }


class TeslaCANParser:
    """
    Parse Tesla CAN frames into structured vehicle state.

    This parser is intentionally conservative: it only decodes signals that
    are well-documented and useful for an AI copilot / diagnostic dashboard.
    """

    def __init__(self):
        self.state = VehicleCANState()

    def parse_frame(self, can_id: int, data: bytes, timestamp: float = 0.0) -> None:
        """Parse a single CAN frame and update internal state."""
        if len(data) > 8:
            return  # Invalid CAN frame

        self.state.last_updated[can_id] = timestamp

        if can_id == CAN_ID_GTW_CAR_CONFIG:
            self._parse_gtw_car_config(data)
        elif can_id == CAN_ID_DAS_STATUS:
            self._parse_das_status(data)
        elif can_id == CAN_ID_BMS_HV_BUS:
            self._parse_bms_hv_bus(data)
        elif can_id == CAN_ID_BMS_SOC:
            self._parse_bms_soc(data)
        elif can_id == CAN_ID_BMS_THERMAL:
            self._parse_bms_thermal(data)
        elif can_id == CAN_ID_UI_RATED_CONSUMPTION:
            self._parse_rated_consumption(data)
        elif can_id == CAN_ID_EPAS_STATUS:
            self._parse_epas_status(data)
        elif can_id == CAN_ID_GTW_CAR_STATE:
            self._parse_gtw_car_state(data)
        # 0x399 is HW-dependent; skip ambiguous parsing here

    def _parse_gtw_car_config(self, data: bytes) -> None:
        """
        Parse GTW_carConfig (0x398) for HW detection.

        GTW_dasHw is typically in byte 0 bits 6-7.
        """
        if len(data) < 1:
            return

        byte0 = data[0]
        das_hw = (byte0 >> 6) & 0x03
        self.state.das_hw = das_hw

        # Mapping based on community docs; may vary by firmware
        mapping = {
            0: TeslaHWVersion.HW1,
            1: TeslaHWVersion.HW2,
            2: TeslaHWVersion.HW3,
            3: TeslaHWVersion.HW4,
        }
        self.state.hw_version = mapping.get(das_hw, TeslaHWVersion.UNKNOWN)

    def _parse_das_status(self, data: bytes) -> None:
        """
        Parse DAS_status (0x39B) for AP state and nag level.

        This is a simplified parser; real signal layouts vary by firmware.
        """
        if len(data) < 2:
            return

        # Byte 0 bits 0-3 commonly encode DAS_autopilotState
        ap_state_raw = data[0] & 0x0F
        ap_map = {
            0: AutopilotState.OFF,
            1: AutopilotState.STANDBY,
            2: AutopilotState.ENGAGED,
            3: AutopilotState.ENGAGED,
        }
        self.state.autopilot_state = ap_map.get(ap_state_raw, AutopilotState.UNKNOWN)

        # Byte 1 bits commonly encode handsOnLevel
        if len(data) > 1:
            self.state.hands_on_level = data[1] & 0x03

    def _parse_bms_hv_bus(self, data: bytes) -> None:
        """Parse BMS_hvBusStatus (0x132)."""
        if len(data) < 6:
            return

        # BMS_hvVoltage: bytes 0-11 bits, 0.1 V / bit, unsigned
        voltage_raw = int.from_bytes(data[0:2], "little") & 0xFFF
        self.state.battery_voltage = voltage_raw * 0.1

        # BMS_hvCurrent: bytes 2-15 bits, signed, 0.1 A / bit (approx)
        current_raw = int.from_bytes(data[2:4], "little", signed=True)
        self.state.battery_current = current_raw * 0.1

    def _parse_bms_soc(self, data: bytes) -> None:
        """Parse BMS_socStatus (0x292)."""
        if len(data) < 2:
            return

        # BMS_soc: byte 0, 0.5% / bit (example)
        soc_raw = data[0]
        self.state.battery_soc = min(soc_raw * 0.5, 100.0)

    def _parse_bms_thermal(self, data: bytes) -> None:
        """Parse BMS_thermalStatus (0x312)."""
        if len(data) < 4:
            return

        # Placeholder scaling; real offsets vary by pack
        self.state.battery_temp_min = data[0] - 40.0
        self.state.battery_temp_max = data[1] - 40.0

    def _parse_rated_consumption(self, data: bytes) -> None:
        """Parse UI_ratedConsumption (0x33A) Wh/km."""
        if len(data) < 2:
            return

        raw = int.from_bytes(data[0:2], "little") & 0x7FF
        self.state.wh_per_km = raw * 0.1

    def _parse_epas_status(self, data: bytes) -> None:
        """Parse EPAS3P_sysStatus (0x370)."""
        if len(data) < 6:
            return

        # Counter commonly in low bits of byte 5
        self.state.epas_counter = data[5] & 0x0F

        # Steering angle / torque would need precise signal layout
        # Left as placeholder for future expansion

    def _parse_gtw_car_state(self, data: bytes) -> None:
        """Parse GTW_carState (0x318) for OTA in progress."""
        if len(data) < 2:
            return

        # Byte 1 bit 0 commonly indicates OTA active
        self.state.ota_in_progress = bool(data[1] & 0x01)

    def get_state(self) -> VehicleCANState:
        """Return a copy of current state."""
        from copy import deepcopy

        return deepcopy(self.state)

    def reset(self) -> None:
        """Reset parser state."""
        self.state = VehicleCANState()


# ============== TX Frame Builders (UI-only, safe subset) ==============
# These build frames that can be injected. They do NOT represent a
# recommendation to do so; higher layers must enforce listen-only default.


def build_fsd_unlock_frame(
    base_frame: bytes,
    hw_version: TeslaHWVersion,
    enable: bool = True,
) -> bytes:
    """
    Build UI_autopilotControl (0x3FD) frame with FSD enable bits.

    Args:
        base_frame: Original 8-byte frame from the bus.
        hw_version: Detected Autopilot hardware version.
        enable: True to set FSD bits, False to clear.

    Returns:
        Modified 8-byte frame.
    """
    data = bytearray(base_frame)
    if len(data) != 8:
        raise ValueError("Tesla CAN frame must be 8 bytes")

    if hw_version == TeslaHWVersion.HW4:
        # HW4: bit46 + bit60, bit47 speed profile
        if enable:
            data[5] |= 0x40  # bit46
            data[7] |= 0x10  # bit60
        else:
            data[5] &= ~0x40
            data[7] &= ~0x10
    elif hw_version in (TeslaHWVersion.HW3, TeslaHWVersion.HW2_5, TeslaHWVersion.HW2):
        # HW3: bit46
        if enable:
            data[5] |= 0x40
        else:
            data[5] &= ~0x40
    elif hw_version == TeslaHWVersion.HW1:
        # Legacy uses 0x3EE, not 0x3FD
        raise NotImplementedError("HW1 uses CAN_ID_UI_AP_LEGACY (0x3EE)")

    return bytes(data)


def build_tlssc_restore_frame(
    base_frame: bytes,
    enable: bool = True,
) -> bytes:
    """
    Build DAS_autopilotConfig (0x331) frame setting tier to SELF_DRIVING.

    This is the TLSSC Restore feature documented in flipper-tesla-fsd for
    VIN-banned vehicles. Use only for research/educational purposes.
    """
    data = bytearray(base_frame)
    if len(data) != 8:
        raise ValueError("Tesla CAN frame must be 8 bytes")

    # Simplified: set DAS_autopilot to SELF_DRIVING in lower bits
    if enable:
        data[0] = (data[0] & 0xF8) | 0x03
    else:
        data[0] = (data[0] & 0xF8) | 0x01

    return bytes(data)


def build_nag_echo_frame(
    base_frame: bytes,
    counter: int,
    torque: float = 1.5,
) -> bytes:
    """
    Build EPAS3P_sysStatus (0x370) echo frame with counter+1 and torque.

    Args:
        base_frame: Original 8-byte frame.
        counter: EPAS counter value to inject.
        torque: Torque value in Nm (1.0 - 3.3).
    """
    data = bytearray(base_frame)
    if len(data) != 8:
        raise ValueError("Tesla CAN frame must be 8 bytes")

    # Placeholder bit positions; real layout requires firmware-specific DBC
    data[5] = (data[5] & 0xF0) | (counter & 0x0F)
    # Torque scaling example: 0.1 Nm / bit, offset 0
    torque_raw = max(10, min(33, int(torque * 10)))
    data[2] = torque_raw

    return bytes(data)


# ============== Helpers ==============


def get_can_id_name(can_id: int) -> str:
    """Return human-readable name for a Tesla CAN ID."""
    names = {
        CAN_ID_GTW_CAR_CONFIG: "GTW_carConfig",
        CAN_ID_GTW_CAR_STATE: "GTW_carState",
        CAN_ID_DAS_STATUS: "DAS_status",
        CAN_ID_ISA_SPEED: "ISA_speedLimit/DAS_status",
        CAN_ID_BMS_HV_BUS: "BMS_hvBusStatus",
        CAN_ID_BMS_SOC: "BMS_socStatus",
        CAN_ID_BMS_THERMAL: "BMS_thermalStatus",
        CAN_ID_UI_RATED_CONSUMPTION: "UI_ratedConsumption",
        CAN_ID_EPAS_STATUS: "EPAS3P_sysStatus",
        CAN_ID_UI_AUTOPILOT_CONTROL: "UI_autopilotControl",
        CAN_ID_UI_DRIVER_ASSIST: "UI_driverAssistControl",
        CAN_ID_DAS_CONFIG: "DAS_autopilotConfig",
        CAN_ID_GTW_CONFIG: "GTW_carConfig(TX)",
        CAN_ID_UI_TRIP_PLANNING: "UI_tripPlanning",
        CAN_ID_VCLEFT_SWITCH: "VCLEFT_switchStatus",
        CAN_ID_UI_AP_LEGACY: "UI_autopilotControl(Legacy)",
    }
    return names.get(can_id, f"UNKNOWN_0x{can_id:03X}")
