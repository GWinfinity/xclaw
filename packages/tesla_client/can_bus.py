"""
Tesla CAN Bus Interface

Multi-platform CAN bus abstraction for xClaw. Supports:
- Mock CAN (testing / simulation)
- SocketCAN (Linux desktop / Raspberry Pi with CAN hat)
- ESP32/M5StickS3 serial bridge
- ESP32/M5StickS3 TCP/UDP bridge over WiFi

Design goal: provide a single async interface that works both in the cloud
(Fleet API companion) and on-device (ESP32/M5StickS3 plugged into the car).
"""

from __future__ import annotations

import abc
import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class CANFrameType(str, Enum):
    """CAN frame type."""

    STANDARD = "standard"
    EXTENDED = "extended"


@dataclass
class CANFrame:
    """A single CAN frame."""

    can_id: int
    data: bytes
    extended: bool = False
    timestamp: float = field(default_factory=time.time)
    interface: str = "unknown"

    @property
    def hex_id(self) -> str:
        """Return CAN ID as hex string."""
        return f"0x{self.can_id:03X}"

    @property
    def hex_data(self) -> str:
        """Return data as hex string."""
        return self.data.hex()

    @property
    def dlc(self) -> int:
        """Data length code."""
        return len(self.data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "can_id": self.can_id,
            "hex_id": self.hex_id,
            "data": self.hex_data,
            "dlc": self.dlc,
            "extended": self.extended,
            "timestamp": self.timestamp,
            "interface": self.interface,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CANFrame":
        return cls(
            can_id=data["can_id"],
            data=bytes.fromhex(data["data"]),
            extended=data.get("extended", False),
            timestamp=data.get("timestamp", time.time()),
            interface=data.get("interface", "unknown"),
        )


class BaseCANInterface(abc.ABC):
    """Abstract async CAN interface."""

    name: str = "base"

    def __init__(self, listen_only: bool = True):
        """
        Initialize CAN interface.

        Args:
            listen_only: When True, the interface will not transmit frames.
                         This is the fail-safe default for first tests.
        """
        self.listen_only = listen_only
        self._running = False
        self._rx_task: Optional[asyncio.Task] = None
        self._frame_handlers: List[Callable[[CANFrame], None]] = []
        self._tx_enabled = not listen_only

    @abc.abstractmethod
    async def start(self) -> None:
        """Start receiving frames."""
        raise NotImplementedError

    @abc.abstractmethod
    async def stop(self) -> None:
        """Stop receiving frames and release resources."""
        raise NotImplementedError

    @abc.abstractmethod
    async def read_frame(self) -> Optional[CANFrame]:
        """Read one CAN frame (blocking). Returns None on timeout/close."""
        raise NotImplementedError

    @abc.abstractmethod
    async def send_frame(self, frame: CANFrame) -> bool:
        """
        Transmit one CAN frame.

        Returns True on success, False on failure.
        Raises RuntimeError if listen_only=True.
        """
        raise NotImplementedError

    def on_frame(self, handler: Callable[[CANFrame], None]) -> Callable[[CANFrame], None]:
        """Register a frame handler. Can be used as decorator."""
        self._frame_handlers.append(handler)
        return handler

    def remove_handler(self, handler: Callable[[CANFrame], None]) -> None:
        """Remove a frame handler."""
        if handler in self._frame_handlers:
            self._frame_handlers.remove(handler)

    def _dispatch_frame(self, frame: CANFrame) -> None:
        """Dispatch frame to all registered handlers."""
        for handler in self._frame_handlers:
            try:
                handler(frame)
            except Exception:
                # Handlers must not crash the bus loop
                pass

    async def _rx_loop(self) -> None:
        """Background receive loop."""
        while self._running:
            try:
                frame = await self.read_frame()
                if frame:
                    self._dispatch_frame(frame)
            except asyncio.CancelledError:
                break
            except Exception:
                # Avoid tight crash loops; let hardware recover
                await asyncio.sleep(0.01)

    async def start_rx_loop(self) -> None:
        """Start background frame receiving."""
        if self._running:
            return
        self._running = True
        await self.start()
        self._rx_task = asyncio.create_task(self._rx_loop())

    async def stop_rx_loop(self) -> None:
        """Stop background frame receiving."""
        self._running = False
        if self._rx_task and not self._rx_task.done():
            self._rx_task.cancel()
            try:
                await self._rx_task
            except asyncio.CancelledError:
                pass
        await self.stop()

    def enable_tx(self) -> None:
        """Enable frame transmission after safety checks."""
        self._tx_enabled = True
        self.listen_only = False

    def disable_tx(self) -> None:
        """Disable frame transmission (listen-only mode)."""
        self._tx_enabled = False
        self.listen_only = True

    async def safe_send_frame(self, frame: CANFrame) -> bool:
        """
        Send frame only if TX is enabled.

        This is the recommended public method for all transmit paths.
        """
        if not self._tx_enabled or self.listen_only:
            raise RuntimeError(
                "CAN TX is disabled. Call enable_tx() only after verifying "
                "hardware, wiring, and legal/safety conditions."
            )
        return await self.send_frame(frame)


class MockCANInterface(BaseCANInterface):
    """
    In-memory CAN interface for unit tests and simulation.

    Can replay a list of frames and record transmitted frames.
    """

    name = "mock"

    def __init__(
        self,
        listen_only: bool = True,
        replay_frames: Optional[List[CANFrame]] = None,
        loop: bool = False,
    ):
        super().__init__(listen_only=listen_only)
        self._replay_frames = list(replay_frames or [])
        self._loop = loop
        self._index = 0
        self._tx_log: List[CANFrame] = []
        self._rx_queue: asyncio.Queue[CANFrame] = asyncio.Queue()
        self._closed = True

    async def start(self) -> None:
        self._closed = False

    async def stop(self) -> None:
        self._closed = True

    async def read_frame(self) -> Optional[CANFrame]:
        if self._closed:
            return None

        # Replay queue first
        if not self._rx_queue.empty():
            return await self._rx_queue.get()

        # Then replay pre-recorded frames
        if self._replay_frames:
            if self._index >= len(self._replay_frames):
                if self._loop:
                    self._index = 0
                else:
                    await asyncio.sleep(0.05)
                    return None

            frame = self._replay_frames[self._index]
            self._index += 1
            await asyncio.sleep(0.001)
            return frame

        # Nothing to replay: block briefly
        await asyncio.sleep(0.05)
        return None

    async def send_frame(self, frame: CANFrame) -> bool:
        if self.listen_only:
            raise RuntimeError("Mock CAN is in listen-only mode")
        self._tx_log.append(frame)
        return True

    def inject_frame(self, frame: CANFrame) -> None:
        """Inject a frame into the RX path for testing."""
        self._rx_queue.put_nowait(frame)

    @property
    def transmitted_frames(self) -> List[CANFrame]:
        return list(self._tx_log)


class SocketCANInterface(BaseCANInterface):
    """
    Linux SocketCAN interface (e.g., can0, vcan0).

    Requires `python-can`:
        pip install python-can

    Also requires a CAN interface on the host:
        sudo ip link add dev vcan0 type vcan
        sudo ip link set up vcan0
    """

    name = "socketcan"

    def __init__(
        self,
        channel: str = "vcan0",
        bitrate: int = 500_000,
        listen_only: bool = True,
    ):
        super().__init__(listen_only=listen_only)
        self.channel = channel
        self.bitrate = bitrate
        self._bus: Optional[Any] = None

    async def start(self) -> None:
        try:
            import can  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "python-can is required for SocketCAN. Install: pip install python-can"
            ) from exc

        self._bus = can.interface.Bus(
            channel=self.channel,
            bustype="socketcan",
            bitrate=self.bitrate,
        )

    async def stop(self) -> None:
        if self._bus:
            self._bus.shutdown()
            self._bus = None

    async def read_frame(self) -> Optional[CANFrame]:
        if not self._bus:
            return None

        # python-can recv blocks; run in thread pool
        loop = asyncio.get_event_loop()
        msg = await loop.run_in_executor(None, self._bus.recv, 0.1)
        if msg is None:
            return None

        return CANFrame(
            can_id=msg.arbitration_id,
            data=msg.data,
            extended=msg.is_extended_id,
            timestamp=msg.timestamp,
            interface=self.name,
        )

    async def send_frame(self, frame: CANFrame) -> bool:
        if not self._bus:
            raise RuntimeError("SocketCAN not started")

        try:
            import can  # type: ignore
        except ImportError as exc:
            raise RuntimeError("python-can not installed") from exc

        msg = can.Message(
            arbitration_id=frame.can_id,
            data=frame.data,
            is_extended_id=frame.extended,
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._bus.send, msg)
        return True


class ESP32SerialBridgeInterface(BaseCANInterface):
    """
    Bridge to an ESP32 running a simple serial-CAN forwarder.

    The ESP32 firmware is expected to send/receive newline-delimited JSON:
        {"id":1021,"data":"0000000000000000","ext":false}

    Wiring (example for M5StickS3 + external TJA1051/MCP2515):
        M5StickS3 GPIO -> CAN transceiver -> vehicle CAN-H/L
        M5StickS3 USB/UART -> host USB

    For M5StickS3 specifically, use this class with the USB-COM port.
    The board has no built-in CAN transceiver, so you still need an
    external transceiver module.
    """

    name = "esp32_serial"

    def __init__(
        self,
        port: str,
        baudrate: int = 921600,
        listen_only: bool = True,
    ):
        super().__init__(listen_only=listen_only)
        self.port = port
        self.baudrate = baudrate
        self._serial: Optional[Any] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def start(self) -> None:
        try:
            import serial_asyncio  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "pyserial-asyncio is required. Install: pip install pyserial-asyncio"
            ) from exc

        self._reader, self._writer = await serial_asyncio.open_serial_connection(
            url=self.port,
            baudrate=self.baudrate,
        )

    async def stop(self) -> None:
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def read_frame(self) -> Optional[CANFrame]:
        if not self._reader:
            return None

        try:
            line = await asyncio.wait_for(self._reader.readline(), timeout=0.2)
        except asyncio.TimeoutError:
            return None

        if not line:
            return None

        try:
            payload = json.loads(line.decode("utf-8").strip())
            return CANFrame(
                can_id=int(payload["id"]),
                data=bytes.fromhex(payload["data"]),
                extended=bool(payload.get("ext", False)),
                timestamp=time.time(),
                interface=self.name,
            )
        except Exception:
            return None

    async def send_frame(self, frame: CANFrame) -> bool:
        if not self._writer:
            raise RuntimeError("ESP32 serial bridge not started")

        payload = json.dumps(
            {
                "id": frame.can_id,
                "data": frame.hex_data,
                "ext": frame.extended,
            }
        )
        self._writer.write((payload + "\n").encode("utf-8"))
        await self._writer.drain()
        return True


class ESP32TCPBridgeInterface(BaseCANInterface):
    """
    Bridge to an ESP32 CAN forwarder over TCP/UDP.

    Useful when the ESP32/M5StickS3 is connected to the car and exposes
    a WiFi AP or joins the same network as the host.
    """

    name = "esp32_tcp"

    def __init__(
        self,
        host: str,
        port: int = 3333,
        listen_only: bool = True,
    ):
        super().__init__(listen_only=listen_only)
        self.host = host
        self.port = port
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def start(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(
            self.host, self.port
        )

    async def stop(self) -> None:
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def read_frame(self) -> Optional[CANFrame]:
        if not self._reader:
            return None

        try:
            line = await asyncio.wait_for(self._reader.readline(), timeout=0.2)
        except asyncio.TimeoutError:
            return None

        if not line:
            return None

        try:
            payload = json.loads(line.decode("utf-8").strip())
            return CANFrame(
                can_id=int(payload["id"]),
                data=bytes.fromhex(payload["data"]),
                extended=bool(payload.get("ext", False)),
                timestamp=time.time(),
                interface=self.name,
            )
        except Exception:
            return None

    async def send_frame(self, frame: CANFrame) -> bool:
        if not self._writer:
            raise RuntimeError("ESP32 TCP bridge not started")

        payload = json.dumps(
            {
                "id": frame.can_id,
                "data": frame.hex_data,
                "ext": frame.extended,
            }
        )
        self._writer.write((payload + "\n").encode("utf-8"))
        await self._writer.drain()
        return True


class M5StickS3Interface(ESP32SerialBridgeInterface):
    """
    Convenience alias for M5StickS3 + external CAN transceiver over USB serial.

    M5StickS3 is an ESP32-S3 board. It has WiFi/BLE and a small screen, but
    NO built-in CAN transceiver. You must attach an external module such as:
      - TJA1051 / SN65HVD230 transceiver (for ESP32 TWAI)
      - MCP2515 SPI module

    The recommended firmware on the StickS3 is a serial-to-CAN bridge that
    prints one JSON line per CAN frame. This class talks to that bridge.
    """

    name = "m5sticks3"

    def __init__(
        self,
        port: str,
        baudrate: int = 921600,
        listen_only: bool = True,
    ):
        super().__init__(
            port=port,
            baudrate=baudrate,
            listen_only=listen_only,
        )


def create_can_interface(
    interface_type: str,
    **kwargs: Any,
) -> BaseCANInterface:
    """
    Factory for CAN interfaces.

    Args:
        interface_type: One of "mock", "socketcan", "esp32_serial",
                        "esp32_tcp", "m5sticks3".
        **kwargs: Passed to the concrete interface constructor.

    Returns:
        Configured CAN interface instance.
    """
    mapping: Dict[str, type] = {
        "mock": MockCANInterface,
        "socketcan": SocketCANInterface,
        "esp32_serial": ESP32SerialBridgeInterface,
        "esp32_tcp": ESP32TCPBridgeInterface,
        "m5sticks3": M5StickS3Interface,
    }

    cls = mapping.get(interface_type)
    if not cls:
        raise ValueError(
            f"Unknown CAN interface type: {interface_type}. "
            f"Supported: {list(mapping.keys())}"
        )

    return cls(**kwargs)
