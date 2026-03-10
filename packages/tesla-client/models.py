"""
Tesla Fleet API Data Models

Pydantic models for Tesla vehicle data structures.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ChargingState(str, Enum):
    """Charging state enumeration."""
    DISCONNECTED = "Disconnected"
    NO_POWER = "NoPower"
    STARTING = "Starting"
    CHARGING = "Charging"
    COMPLETE = "Complete"
    STOPPED = "Stopped"


class ShiftState(str, Enum):
    """Gear shift state."""
    PARK = "P"
    REVERSE = "R"
    NEUTRAL = "N"
    DRIVE = "D"


class ChargeState(BaseModel):
    """Battery and charging information."""
    battery_heater_on: Optional[bool] = None
    battery_level: int = Field(..., description="Battery level percentage (0-100)")
    battery_range: float = Field(..., description="Estimated range in miles")
    charge_amps: Optional[int] = None
    charge_current_request: int
    charge_current_request_max: int
    charge_enable_request: bool
    charge_energy_added: float
    charge_limit_soc: int
    charge_limit_soc_max: int
    charge_limit_soc_min: int
    charge_limit_soc_std: int
    charge_miles_added_ideal: float
    charge_miles_added_rated: float
    charge_port_cold_weather_mode: Optional[bool] = None
    charge_port_door_open: bool
    charge_port_latch: str
    charge_rate: float
    charge_to_max_range: bool
    charger_actual_current: int
    charger_phases: Optional[int] = None
    charger_pilot_current: int
    charger_power: int
    charger_voltage: int
    charging_state: ChargingState
    conn_charge_cable: Optional[str] = None
    est_battery_range: float
    fast_charger_brand: str
    fast_charger_present: bool
    fast_charger_type: str
    ideal_battery_range: float
    max_range_charge_counter: int
    minutes_to_full_charge: int
    not_enough_power_to_heat: Optional[bool] = None
    scheduled_charging_pending: bool
    scheduled_charging_start_time: Optional[datetime] = None
    time_to_full_charge: float
    timestamp: datetime
    trip_charging: bool
    usable_battery_level: int
    user_charge_enable_request: Optional[bool] = None

    class Config:
        json_encoders = {
            datetime: lambda v: int(v.timestamp() * 1000)
        }


class ClimateState(BaseModel):
    """Climate control information."""
    battery_heater: Optional[bool] = None
    battery_heater_no_power: Optional[bool] = None
    climate_keeper_mode: Optional[str] = None
    defrost_mode: Optional[int] = None
    driver_temp_setting: float
    fan_status: Optional[int] = None
    inside_temp: Optional[float] = None
    is_auto_conditioning_on: Optional[bool] = None
    is_climate_on: bool
    is_front_defroster_on: Optional[bool] = None
    is_preconditioning: Optional[bool] = None
    is_rear_defroster_on: bool
    left_temp_direction: Optional[int] = None
    max_avail_temp: float
    min_avail_temp: float
    outside_temp: Optional[float] = None
    passenger_temp_setting: float
    remote_heater_control_enabled: Optional[bool] = None
    right_temp_direction: Optional[int] = None
    seat_heater_left: Optional[int] = None
    seat_heater_rear_center: Optional[int] = None
    seat_heater_rear_left: Optional[int] = None
    seat_heater_rear_right: Optional[int] = None
    seat_heater_right: Optional[int] = None
    side_mirror_heaters: Optional[bool] = None
    steering_wheel_heater: Optional[bool] = None
    timestamp: datetime
    wiper_blade_heater: Optional[bool] = None


class DriveState(BaseModel):
    """Driving and location information."""
    gps_as_of: Optional[int] = None
    heading: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    native_latitude: Optional[float] = None
    native_location_supported: Optional[int] = None
    native_longitude: Optional[float] = None
    native_type: Optional[str] = None
    power: Optional[int] = None
    shift_state: Optional[ShiftState] = None
    speed: Optional[float] = None
    timestamp: datetime


class GuiSettings(BaseModel):
    """GUI and display settings."""
    gui_24_hour_time: bool
    gui_charge_rate_units: str
    gui_distance_units: str
    gui_range_display: str
    gui_temperature_units: str
    gui_tirepressure_units: str
    show_range_units: bool
    timestamp: datetime


class VehicleState(BaseModel):
    """Vehicle status information."""
    api_version: Optional[int] = None
    autopark_state_v2: Optional[str] = None
    autopark_style: Optional[str] = None
    calendar_supported: bool
    car_version: str
    center_display_state: Optional[int] = None
    df: Optional[int] = None  # Driver front door
    dr: Optional[int] = None  # Driver rear door
    fd_window: Optional[int] = None  # Front driver window
    fp_window: Optional[int] = None  # Front passenger window
    ft: Optional[int] = None  # Front trunk
    homelink_device_count: Optional[int] = None
    homelink_nearby: Optional[bool] = None
    is_user_present: bool
    last_autopark_error: Optional[str] = None
    locked: bool
    media_info: Optional[Dict[str, Any]] = None
    media_state: Optional[Dict[str, Any]] = None
    notifications_supported: bool
    odometer: float
    parsed_calendar_supported: bool
    pf: Optional[int] = None  # Passenger front door
    pr: Optional[int] = None  # Passenger rear door
    rd_window: Optional[int] = None  # Rear driver window
    remote_start: bool
    remote_start_enabled: bool
    remote_start_supported: bool
    rp_window: Optional[int] = None  # Rear passenger window
    rt: Optional[int] = None  # Rear trunk
    santa_mode: Optional[int] = None
    sentry_mode: Optional[bool] = None
    sentry_mode_available: Optional[bool] = None
    software_update: Optional[Dict[str, Any]] = None
    speed_limit_mode: Optional[Dict[str, Any]] = None
    timestamp: datetime
    valet_mode: bool
    valet_pin_needed: bool
    vehicle_name: Optional[str] = None


class VehicleConfig(BaseModel):
    """Vehicle configuration information."""
    can_accept_navigation_requests: bool
    can_actuate_trunks: bool
    car_special_type: str
    car_type: str
    charge_port_type: str
    dashcam_clip_save_supported: Optional[bool] = None
    default_charge_to_max: bool
    driver_assist: Optional[str] = None
    ece_restrictions: Optional[bool] = None
    efficiency_package: Optional[str] = None
    eu_vehicle: bool
    exterior_color: str
    has_air_suspension: bool
    has_ludicrous_mode: bool
    has_seat_cooling: Optional[bool] = None
    headlamp_type: Optional[str] = None
    interior_trim_type: Optional[str] = None
    key_version: Optional[int] = None
    motorized_charge_port: bool
    plg: Optional[bool] = None  # Power liftgate
    pws: Optional[bool] = None  # Pedestrian warning system
    rear_drive_unit: Optional[str] = None
    rear_seat_heaters: Optional[int] = None
    rear_seat_type: Optional[int] = None
    rhd: bool  # Right hand drive
    roof_color: str
    seat_type: Optional[int] = None
    spoiler_type: Optional[str] = None
    sun_roof_installed: Optional[int] = None
    third_row_seats: str
    timestamp: datetime
    trim_badging: Optional[str] = None
    use_range_badging: bool
    utc_offset: Optional[int] = None
    webcam_supported: Optional[bool] = None
    wheel_type: str


class VehicleData(BaseModel):
    """Complete vehicle data response."""
    id: int
    user_id: int
    vehicle_id: int
    vin: str
    display_name: str
    option_codes: Optional[str] = None
    color: Optional[str] = None
    access_type: Optional[str] = None
    tokens: Optional[List[str]] = None
    state: str  # online, asleep, offline, etc.
    in_service: bool
    id_s: str
    calendar_enabled: bool
    api_version: int
    backseat_token: Optional[str] = None
    backseat_token_updated_at: Optional[datetime] = None
    charge_state: ChargeState
    climate_state: ClimateState
    drive_state: DriveState
    gui_settings: GuiSettings
    vehicle_state: VehicleState
    vehicle_config: VehicleConfig


class TokenResponse(BaseModel):
    """OAuth token response."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        from datetime import timedelta
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.expires_in)
