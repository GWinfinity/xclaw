"""
Tests for Tesla vehicle platform detection.
"""

import pytest

from .platform import (
    detect_platform,
    parse_vin_year,
    parse_vin_model,
    parse_vin_region,
)


class TestVinParsing:
    """Test VIN parsing helpers."""

    def test_parse_vin_year(self):
        assert parse_vin_year("5YJ3E1EA8JF000000") == 2018
        assert parse_vin_year("5YJ3E1EA8KF000000") == 2019
        assert parse_vin_year("5YJ3E1EA8LF000000") == 2020
        assert parse_vin_year("5YJ3E1EA8MF000000") == 2021
        assert parse_vin_year("5YJ3E1EA8NF000000") == 2022
        assert parse_vin_year("5YJ3E1EA8PF000000") == 2023
        assert parse_vin_year("5YJ3E1EA8RF000000") == 2024
        assert parse_vin_year("5YJ3E1EA8SF000000") == 2025

    def test_parse_vin_year_invalid(self):
        assert parse_vin_year("") == 0
        assert parse_vin_year("123") == 0
        assert parse_vin_year(None) == 0

    def test_parse_vin_model(self):
        assert parse_vin_model("5YJ3E1EA8JF000000") == "model3"
        assert parse_vin_model("5YJYGDEE9LF000000") == "modely"
        assert parse_vin_model("5YJSB6E19JF000000") == "models"
        assert parse_vin_model("5YJXCBE20JF000000") == "modelx"
        assert parse_vin_model("7G2CYCE21PF000000") == "cybertruck"

    def test_parse_vin_region(self):
        assert parse_vin_region("5YJ3E1EA8JF000000") == "usa_fremont"
        assert parse_vin_region("7SAYGDEE9LF000000") == "usa_fremont"
        assert parse_vin_region("LRW3E1EA8PF000000") == "china"
        assert parse_vin_region("XP7YGDEE9LF000000") == "germany"


class TestPlatformDetection:
    """Test platform detection from VIN and vehicle_config."""

    def test_model3_old_pre_refresh(self):
        vin = "5YJ3E1EA8JF000000"  # 2018 Model 3
        info = detect_platform(vin)
        assert info.model_type == "model3"
        assert info.model_year == 2018
        assert info.refresh_generation == "pre_refresh"
        assert info.mcu_version == "mcu2"
        assert info.hw_version == "unknown"  # no vehicle_config
        assert not info.has_seat_cooling
        assert not info.has_bioweapon_mode
        assert info.is_m3_platform

    def test_model3_highland_from_vin(self):
        vin = "LRW3E1EA8RF000000"  # 2024 China Model 3 Highland
        info = detect_platform(vin)
        assert info.model_type == "model3"
        assert info.model_year == 2024
        assert info.refresh_generation == "highland"
        assert info.mcu_version == "mcu3"
        assert info.has_seat_cooling
        assert info.has_bioweapon_mode
        assert info.is_m3_platform

    def test_modely_old_pre_refresh(self):
        vin = "5YJYGDEE9LF000000"  # 2020 Model Y
        info = detect_platform(vin)
        assert info.model_type == "modely"
        assert info.model_year == 2020
        assert info.refresh_generation == "pre_refresh"
        assert info.mcu_version == "mcu2"
        assert not info.has_seat_cooling

    def test_modely_juniper_from_vin(self):
        vin = "LRWYGDEE9SF000000"  # 2025 China Model Y Juniper
        info = detect_platform(vin)
        assert info.model_type == "modely"
        assert info.model_year == 2025
        assert info.refresh_generation == "juniper"
        assert info.mcu_version == "mcu3"
        assert info.has_seat_cooling
        assert info.has_bioweapon_mode

    def test_models_refresh(self):
        vin = "5YJSB6E19MF000000"  # 2021 Model S
        info = detect_platform(vin)
        assert info.model_type == "models"
        assert info.refresh_generation == "refresh"
        assert info.mcu_version == "mcu3"
        assert info.has_bioweapon_mode
        # Seat cooling on Model S refresh is also assumed
        assert info.has_seat_cooling

    def test_modelx_pre_refresh(self):
        vin = "5YJXCBE20JF000000"  # 2018 Model X
        info = detect_platform(vin)
        assert info.model_type == "modelx"
        assert info.refresh_generation == "pre_refresh"
        assert info.mcu_version == "mcu2"
        assert info.has_bioweapon_mode  # Model X always had bioweapon mode

    def test_cybertruck(self):
        vin = "7G2CYCE21PF000000"  # 2023 Cybertruck
        info = detect_platform(vin)
        assert info.model_type == "cybertruck"
        assert info.mcu_version == "mcu3"
        assert info.has_bioweapon_mode


class TestVehicleConfigPriority:
    """Test that vehicle_config fields take priority over VIN inference."""

    def test_has_seat_cooling_from_config(self):
        vin = "5YJ3E1EA8JF000000"  # Old Model 3 VIN
        config = {"has_seat_cooling": True}
        info = detect_platform(vin, config)
        assert info.has_seat_cooling

    def test_has_seat_cooling_false_from_config(self):
        vin = "LRW3E1EA8RF000000"  # Highland VIN
        config = {"has_seat_cooling": False}
        info = detect_platform(vin, config)
        assert not info.has_seat_cooling

    def test_driver_assist_hw_mapping(self):
        vin = "5YJ3E1EA8JF000000"
        assert detect_platform(vin, {"driver_assist": "TeslaAP3"}).hw_version == "hw3"
        assert detect_platform(vin, {"driver_assist": "TeslaAP4"}).hw_version == "hw4"
        assert detect_platform(vin, {"driver_assist": "ParkerPascal"}).hw_version == "hw2"
        assert detect_platform(vin, {"driver_assist": "ParkerPascal2_5"}).hw_version == "hw2_5"

    def test_car_type_priority_over_vin(self):
        # VIN says Model 3, but car_type says cybertruck
        vin = "5YJ3E1EA8JF000000"
        config = {"car_type": "cybertruck"}
        info = detect_platform(vin, config)
        assert info.model_type == "cybertruck"

    def test_models2_refresh_detection(self):
        vin = "5YJSB6E19JF000000"  # 2018 Model S VIN
        config = {"car_type": "models2"}
        info = detect_platform(vin, config)
        assert info.model_type == "models"
        assert info.refresh_generation == "refresh"
        assert info.mcu_version == "mcu3"


class TestPlatformProperties:
    """Test PlatformInfo convenience properties."""

    def test_is_highland(self):
        info = detect_platform("LRW3E1EA8RF000000")
        assert info.is_highland
        assert info.is_refreshed

    def test_is_juniper(self):
        info = detect_platform("LRWYGDEE9SF000000")
        assert info.is_juniper
        assert info.is_refreshed

    def test_has_mcu3_and_hw4(self):
        info = detect_platform("LRW3E1EA8RF000000", {"driver_assist": "TeslaAP4"})
        assert info.has_mcu3
        assert info.has_hw4

    def test_m3_platform(self):
        assert detect_platform("5YJ3E1EA8JF000000").is_m3_platform
        assert detect_platform("5YJYGDEE9LF000000").is_m3_platform
        assert not detect_platform("5YJSB6E19JF000000").is_m3_platform


class TestEdgeCases:
    """Test edge cases."""

    def test_missing_vin(self):
        info = detect_platform(None)
        assert info.model_type == "unknown"
        assert info.model_year == 0
        assert info.mcu_version == "unknown"

    def test_empty_config(self):
        info = detect_platform("5YJ3E1EA8JF000000", {})
        assert info.model_type == "model3"
