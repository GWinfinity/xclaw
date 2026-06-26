"""
Tests for Tesla CAN bus interface layer.
"""

import asyncio
import pytest

from .can_bus import (
    CANFrame,
    MockCANInterface,
    create_can_interface,
)


class TestCANFrame:
    """Test CAN frame dataclass."""

    def test_hex_id_standard(self):
        frame = CANFrame(can_id=0x3FD, data=b"\x00" * 8)
        assert frame.hex_id == "0x3FD"
        assert frame.dlc == 8

    def test_hex_data(self):
        frame = CANFrame(can_id=0x398, data=bytes.fromhex("0102030405060708"))
        assert frame.hex_data == "0102030405060708"

    def test_to_from_dict(self):
        frame = CANFrame(can_id=0x132, data=b"\xAB\xCD" * 4, interface="mock")
        restored = CANFrame.from_dict(frame.to_dict())
        assert restored.can_id == frame.can_id
        assert restored.data == frame.data
        assert restored.interface == frame.interface


class TestMockCANInterface:
    """Test mock CAN interface."""

    @pytest.mark.asyncio
    async def test_listen_only_blocks_tx(self):
        iface = MockCANInterface(listen_only=True)
        await iface.start()
        frame = CANFrame(can_id=0x3FD, data=b"\x00" * 8)

        with pytest.raises(RuntimeError):
            await iface.send_frame(frame)

        await iface.stop()

    @pytest.mark.asyncio
    async def test_tx_enabled_allows_tx(self):
        iface = MockCANInterface(listen_only=False)
        await iface.start()
        frame = CANFrame(can_id=0x3FD, data=b"\x00" * 8)

        ok = await iface.send_frame(frame)
        assert ok is True
        assert len(iface.transmitted_frames) == 1
        await iface.stop()

    @pytest.mark.asyncio
    async def test_safe_send_frame_requires_enable_tx(self):
        iface = MockCANInterface(listen_only=True)
        await iface.start()
        frame = CANFrame(can_id=0x3FD, data=b"\x00" * 8)

        with pytest.raises(RuntimeError):
            await iface.safe_send_frame(frame)

        iface.enable_tx()
        ok = await iface.safe_send_frame(frame)
        assert ok is True
        await iface.stop()

    @pytest.mark.asyncio
    async def test_replay_frames(self):
        frames = [
            CANFrame(can_id=0x398, data=bytes.fromhex("8000000000000000")),
            CANFrame(can_id=0x132, data=bytes.fromhex("1234567890ABCDEF")),
        ]
        iface = MockCANInterface(replay_frames=frames, loop=False)
        await iface.start()

        received = []
        for _ in range(3):
            frame = await iface.read_frame()
            if frame:
                received.append(frame)

        assert len(received) == 2
        assert received[0].can_id == 0x398
        assert received[1].can_id == 0x132
        await iface.stop()

    @pytest.mark.asyncio
    async def test_frame_handler_dispatch(self):
        iface = MockCANInterface(listen_only=True)
        await iface.start_rx_loop()

        received = []

        @iface.on_frame
        def handler(frame):
            received.append(frame)

        iface.inject_frame(CANFrame(can_id=0x39B, data=b"\x02\x00\x00\x00\x00\x00\x00\x00"))
        await asyncio.sleep(0.05)

        await iface.stop_rx_loop()
        assert len(received) == 1
        assert received[0].can_id == 0x39B


class TestCreateCANInterface:
    """Test factory function."""

    def test_create_mock(self):
        iface = create_can_interface("mock")
        assert isinstance(iface, MockCANInterface)

    def test_unknown_interface_raises(self):
        with pytest.raises(ValueError):
            create_can_interface("unknown")
