"""
Tesla Vehicle Platform Detection

Multi-source vehicle platform detection based on VIN and Fleet API
vehicle_config fields. Decouples MCU, HW, and model platform.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


# VIN year mapping (position 10)
VIN_YEAR_MAP = {
    "J": 2018, "K": 2019, "L": 2020, "M": 2021,
    "N": 2022, "P": 2023, "R": 2024, "S": 2025,
    "T": 2026, "V": 2027, "W": 2028, "X": 2029,
    "Y": 2030,
    # Older years (less common for current API)
    "A": 2010, "B": 2011, "C": 2012, "D": 2013,
    "E": 2014, "F": 2015, "G": 2016, "H": 2017,
}

# WMI to manufacturing region
WMI_REGION_MAP = {
    "5YJ": "usa_fremont",
    "7SA": "usa_fremont",
    "7G2": "usa_austin",  # Cybertruck
    "LRW": "china",
    "XP7": "germany",
    "SFZ": "uk",  # Roadster
}

# car_type from vehicle_config to normalized model type
CAR_TYPE_TO_MODEL = {
    "model3": "model3",
    "modely": "modely",
    "models": "models",
    "models2": "models",  # Model S refresh / Raven / Plaid
    "modelx": "modelx",
    "modelx2": "modelx",  # Model X refresh / Plaid
    "cybertruck": "cybertruck",
    "semi": "semi",
    "roadster": "roadster",
}

# driver_assist from vehicle_config to HW version
DRIVER_ASSIST_TO_HW = {
    "MonoCam": "hw1",
    "ParkerPascal": "hw2",
    "ParkerPascal2_5": "hw2_5",
    "TeslaAP3": "hw3",
    "TeslaAP4": "hw4",
}


@dataclass
class PlatformInfo:
    """Normalized Tesla vehicle platform information."""

    model_type: str = "unknown"
    model_year: int = 0
    mcu_version: str = "unknown"
    hw_version: str = "unknown"
    platform_code: str = "unknown"  # e.g., "highland", "juniper", "pre_refresh"
    refresh_generation: str = "unknown"  # "pre_refresh" | "highland" | "juniper" | "refresh"
    manufacturing_region: str = "unknown"  # "usa_fremont" | "china" | "germany" | "uk"
    has_seat_cooling: bool = False
    has_bioweapon_mode: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_mcu3(self) -> bool:
        return self.mcu_version == "mcu3"

    @property
    def has_hw4(self) -> bool:
        return self.hw_version == "hw4"

    @property
    def is_highland(self) -> bool:
        return self.model_type == "model3" and self.refresh_generation == "highland"

    @property
    def is_juniper(self) -> bool:
        return self.model_type == "modely" and self.refresh_generation == "juniper"

    @property
    def is_refreshed(self) -> bool:
        return self.refresh_generation in ("highland", "juniper", "refresh")

    @property
    def is_cybertruck(self) -> bool:
        return self.model_type == "cybertruck"

    @property
    def is_m3_platform(self) -> bool:
        """Model 3 / Model Y platform (no lat/lon required for window close)."""
        return self.model_type in ("model3", "modely")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "model_year": self.model_year,
            "mcu_version": self.mcu_version,
            "hw_version": self.hw_version,
            "platform_code": self.platform_code,
            "refresh_generation": self.refresh_generation,
            "manufacturing_region": self.manufacturing_region,
            "has_seat_cooling": self.has_seat_cooling,
            "has_bioweapon_mode": self.has_bioweapon_mode,
        }


def parse_vin_year(vin: Optional[str]) -> int:
    """Parse model year from VIN position 10."""
    if not vin or len(vin) < 10:
        return 0
    return VIN_YEAR_MAP.get(vin[9].upper(), 0)


def parse_vin_region(vin: Optional[str]) -> str:
    """Parse manufacturing region from VIN WMI (positions 1-3)."""
    if not vin or len(vin) < 3:
        return "unknown"
    return WMI_REGION_MAP.get(vin[:3].upper(), "unknown")


def parse_vin_model(vin: Optional[str]) -> str:
    """Parse model type from VIN position 4."""
    if not vin or len(vin) < 4:
        return "unknown"
    model_char = vin[3].upper()
    mapping = {
        "S": "models",
        "X": "modelx",
        "3": "model3",
        "Y": "modely",
        "R": "roadster",
        "C": "cybertruck",  # Cybertruck VIN position 4 is reportedly C
    }
    return mapping.get(model_char, "unknown")


def _infer_mcu_version(model_type: str, model_year: int, vehicle_config: Optional[Dict[str, Any]]) -> str:
    """Infer MCU version from model, year, and optional config hints."""
    # If we have enough evidence from vehicle_config, use it.
    # There is no direct MCU field in Fleet API, so we infer from year/model.

    if model_type in ("cybertruck",):
        return "mcu3"

    if model_type in ("models", "modelx"):
        # Refreshed Model S/X started in late 2021 with MCU3
        if model_year >= 2021:
            return "mcu3"
        if model_year >= 2018:
            return "mcu2"
        return "mcu1"

    if model_type in ("model3", "modely"):
        # MCU3 phased in around late 2021 / early 2022
        if model_year >= 2022:
            return "mcu3"
        if model_year >= 2017:
            return "mcu2"
        return "unknown"

    return "unknown"


def _infer_refresh_generation(
    model_type: str,
    model_year: int,
    vehicle_config: Optional[Dict[str, Any]],
) -> str:
    """Infer refresh generation."""
    config = vehicle_config or {}

    # Use car_type / trim_badging hints when available
    car_type = config.get("car_type", "").lower()
    if car_type in ("models2", "modelx2"):
        return "refresh"

    if model_type == "model3":
        # Model 3 Highland started production late 2023
        if model_year >= 2024:
            return "highland"
        return "pre_refresh"

    if model_type == "modely":
        # Model Y Juniper started production 2025
        if model_year >= 2025:
            return "juniper"
        return "pre_refresh"

    if model_type in ("models", "modelx"):
        # Model S/X refresh started 2021
        if model_year >= 2021:
            return "refresh"
        return "pre_refresh"

    if model_type == "cybertruck":
        return "refresh"

    return "unknown"


def _resolve_hw_version(vehicle_config: Optional[Dict[str, Any]]) -> str:
    """Resolve HW version from vehicle_config.driver_assist."""
    if not vehicle_config:
        return "unknown"
    driver_assist = vehicle_config.get("driver_assist")
    if driver_assist:
        return DRIVER_ASSIST_TO_HW.get(driver_assist, "unknown")
    return "unknown"


def _resolve_model_type(vin: Optional[str], vehicle_config: Optional[Dict[str, Any]]) -> str:
    """Resolve model type from vehicle_config.car_type or VIN."""
    if vehicle_config:
        car_type = vehicle_config.get("car_type", "").lower()
        if car_type in CAR_TYPE_TO_MODEL:
            return CAR_TYPE_TO_MODEL[car_type]
    return parse_vin_model(vin)


def _resolve_seat_cooling(platform: PlatformInfo, vehicle_config: Optional[Dict[str, Any]]) -> bool:
    """Resolve seat cooling availability."""
    if vehicle_config and "has_seat_cooling" in vehicle_config:
        return bool(vehicle_config["has_seat_cooling"])

    # Fallback: refreshed Model 3/Y and Model S/X refresh have seat cooling
    if platform.refresh_generation in ("highland", "juniper", "refresh"):
        return True
    return False


def _resolve_bioweapon_mode(platform: PlatformInfo, vehicle_config: Optional[Dict[str, Any]]) -> bool:
    """Resolve Bioweapon Defense Mode availability."""
    if vehicle_config:
        # Bioweapon mode is available on Model S/X (all generations), refreshed Model 3/Y,
        # and Cybertruck.
        if platform.model_type in ("models", "modelx", "cybertruck"):
            return True
        if platform.refresh_generation in ("highland", "juniper", "refresh"):
            return True
        return False

    # Fallback
    if platform.model_type in ("models", "modelx", "cybertruck"):
        return True
    return platform.refresh_generation in ("highland", "juniper")


def detect_platform(
    vin: Optional[str],
    vehicle_config: Optional[Dict[str, Any]] = None,
) -> PlatformInfo:
    """
    Detect Tesla platform from VIN and optional vehicle_config.

    Args:
        vin: Vehicle Identification Number
        vehicle_config: vehicle_config dict from Fleet API (optional)

    Returns:
        PlatformInfo with normalized platform details
    """
    config = vehicle_config or {}

    model_type = _resolve_model_type(vin, config)
    model_year = parse_vin_year(vin)
    region = parse_vin_region(vin)

    # Refresh generation first (needed for MCU inference fallback)
    refresh_generation = _infer_refresh_generation(model_type, model_year, config)

    # HW version from real API field when available
    hw_version = _resolve_hw_version(config)

    # MCU version inferred from year/model (no direct API field)
    mcu_version = _infer_mcu_version(model_type, model_year, config)

    # Override MCU for specific known cases
    if refresh_generation in ("highland", "juniper", "refresh"):
        mcu_version = "mcu3"

    platform_code = refresh_generation

    platform = PlatformInfo(
        model_type=model_type,
        model_year=model_year,
        mcu_version=mcu_version,
        hw_version=hw_version,
        platform_code=platform_code,
        refresh_generation=refresh_generation,
        manufacturing_region=region,
        raw={"vin": vin, "vehicle_config": config},
    )

    platform.has_seat_cooling = _resolve_seat_cooling(platform, config)
    platform.has_bioweapon_mode = _resolve_bioweapon_mode(platform, config)

    return platform
