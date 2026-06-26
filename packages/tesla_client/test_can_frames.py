"""
Tests for Tesla CAN frame parser and builders.
"""

import pytest

from .can_frames import (
    CAN_ID_GTW_CAR_CONFIG,
    CAN_ID_DAS_STATUS,
    CAN_ID_BMS_HV_BUS,
    TeslaCANParser,
    TeslaHWVersion,
    AutopilotState,
    get_can_id_name,
    build_fsd_unlock_frame,
    build_tlssc_restore_frame,
)


class TestTeslaCANParser:
    """Test CAN parser state updates."""

    def test_hw_detection_hw3(self):
        parser = TeslaCANParser()
        # byte0 bits 6-7 = 10 (binary) -> HW3
        parser.parse_frame(CAN_ID_GTW_CAR_CONFIG, bytes.fromhex("8000000000000000"))
        assert parser.state.hw_version == TeslaHWVersion.HW3
        assert parser.state.das_hw == 2

    def test_hw_detection_hw4(self):
        parser = TeslaCANParser()
        # byte0 bits 6-7 = 11 -> HW4
        parser.parse_frame(CAN_ID_GTW_CAR_CONFIG, bytes.fromhex("C000000000000000"))
        assert parser.state.hw_version == TeslaHWVersion.HW4
        assert parser.state.das_hw == 3

    def test_das_status_engaged(self):
        parser = TeslaCANParser()
        parser.parse_frame(CAN_ID_DAS_STATUS, bytes.fromhex("0200000000000000"))
        assert parser.state.autopilot_state == AutopilotState.ENGAGED

    def test_bms_hv_bus(self):
        parser = TeslaCANParser()
        # voltage = 0x0123 * 0.1 = 29.1 V; current = 0x0001 * 0.1 = 0.1 A
        parser.parse_frame(CAN_ID_BMS_HV_BUS, bytes.fromhex("2301010000000000"))
        assert parser.state.battery_voltage == pytest.approx(29.1, 0.1)
        assert parser.state.battery_current == pytest.approx(0.1, 0.01)

    def test_get_can_id_name(self):
        assert get_can_id_name(0x3FD) == "UI_autopilotControl"
        assert get_can_id_name(0x999) == "UNKNOWN_0x999"


class TestFrameBuilders:
    """Test TX frame builders."""

    def test_build_fsd_unlock_hw3(self):
        base = bytes.fromhex("0000000000000000")
        result = build_fsd_unlock_frame(base, TeslaHWVersion.HW3, enable=True)
        assert result[5] & 0x40

        cleared = build_fsd_unlock_frame(result, TeslaHWVersion.HW3, enable=False)
        assert not (cleared[5] & 0x40)

    def test_build_fsd_unlock_hw4(self):
        base = bytes.fromhex("0000000000000000")
        result = build_fsd_unlock_frame(base, TeslaHWVersion.HW4, enable=True)
        assert result[5] & 0x40
        assert result[7] & 0x10

    def test_build_fsd_unlock_wrong_length(self):
        with pytest.raises(ValueError):
            build_fsd_unlock_frame(b"\x00" * 7, TeslaHWVersion.HW3)

    def test_build_tlssc_restore(self):
        base = bytes.fromhex("0100000000000000")
        result = build_tlssc_restore_frame(base, enable=True)
        assert result[0] & 0x03 == 0x03

        restored = build_tlssc_restore_frame(result, enable=False)
        assert restored[0] & 0x03 == 0x01
