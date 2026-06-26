"""
Tesla AI Copilot

Combines Fleet API data, CAN bus state, and a user-provided LLM API to
provide an intelligent vehicle companion. The copilot can:

- Explain vehicle status in natural language
- Suggest charging, climate, and driving optimizations
- Invoke safe Fleet API commands via function calling
- Provide voice/text interaction for in-car AI upgrades

Safety design:
- Default read-only; commands require explicit tool execution
- CAN TX is never triggered by the copilot directly
- All vehicle commands go through Tesla Fleet API (authenticated, logged)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from packages.llm_adapters.base import BaseLLMAdapter, ToolDefinition

from .can_bus import BaseCANInterface, MockCANInterface
from .can_frames import TeslaCANParser, VehicleCANState
from .exceptions import CommandFailedError

if TYPE_CHECKING:
    from .vehicle import Vehicle


@dataclass
class CopilotResponse:
    """Structured response from the AI copilot."""

    content: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    executed_commands: List[Dict[str, Any]] = field(default_factory=list)
    vehicle_state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "tool_calls": self.tool_calls,
            "executed_commands": self.executed_commands,
            "vehicle_state": self.vehicle_state,
            "error": self.error,
        }


class TeslaAICopilot:
    """
    AI copilot for Tesla vehicles.

    Usage:
        from packages.llm_adapters import LLMFactory
        from packages.tesla_client import TeslaFleetClient, TeslaAICopilot

        client = TeslaFleetClient(...)
        llm = LLMFactory.create_from_env()
        copilot = TeslaAICopilot(vehicle=vehicle, llm_adapter=llm)

        # Ask a question
        response = await copilot.ask("我应该现在充电吗？")

        # Get driving advice
        advice = await copilot.get_driving_advice()
    """

    def __init__(
        self,
        vehicle: Optional["Vehicle"] = None,
        llm_adapter: Optional[BaseLLMAdapter] = None,
        can_interface: Optional[BaseCANInterface] = None,
        system_prompt: Optional[str] = None,
        auto_execute_tools: bool = False,
    ):
        """
        Initialize AI copilot.

        Args:
            vehicle: Tesla Fleet API vehicle instance (optional).
            llm_adapter: LLM adapter for generating responses.
            can_interface: CAN bus interface for live vehicle state (optional).
            system_prompt: Custom system prompt for the LLM.
            auto_execute_tools: If True, automatically execute safe Fleet API
                tool calls. If False, only return tool_calls for approval.
        """
        self.vehicle = vehicle
        self.llm_adapter = llm_adapter
        self.can_interface = can_interface or MockCANInterface(listen_only=True)
        self.can_parser = TeslaCANParser()
        self.auto_execute_tools = auto_execute_tools

        # Register CAN frame handler if using a live interface
        if self.can_interface:
            self.can_interface.on_frame(self._on_can_frame)

        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        return (
            "你是 xClaw，一位专业的 Tesla 车辆 AI 助手。你通过 Tesla Fleet API "
            "和车载 CAN 总线了解车辆状态。你的回答应该简洁、专业、安全。"
            "\n\n原则："
            "\n1. 默认只读取车辆状态，不主动控制车辆。"
            "\n2. 只有用户明确要求或授权后，才执行车辆命令。"
            "\n3. 驾驶安全优先；任何建议必须考虑当前车速、电量和路况。"
            "\n4. 不要承诺可以解锁 Tesla 官方未授权的功能。"
        )

    def _on_can_frame(self, frame) -> None:
        """Internal handler: parse incoming CAN frames."""
        try:
            self.can_parser.parse_frame(
                can_id=frame.can_id,
                data=frame.data,
                timestamp=frame.timestamp,
            )
        except Exception:
            pass

    async def _get_vehicle_snapshot(self) -> Dict[str, Any]:
        """Build a unified snapshot from Fleet API and CAN bus."""
        snapshot: Dict[str, Any] = {
            "source": [],
            "platform": None,
            "fleet_api": None,
            "can_bus": None,
        }

        if self.vehicle:
            snapshot["source"].append("fleet_api")
            snapshot["platform"] = self.vehicle.platform_info.to_dict()

            try:
                data = await self.vehicle.get_vehicle_data()
                snapshot["fleet_api"] = {
                    "vin": data.vin,
                    "display_name": data.display_name,
                    "state": data.state,
                    "battery_level": data.charge_state.battery_level,
                    "battery_range_miles": data.charge_state.battery_range,
                    "charging_state": data.charge_state.charging_state.value,
                    "speed": data.drive_state.speed,
                    "shift_state": (
                        data.drive_state.shift_state.value
                        if data.drive_state.shift_state
                        else None
                    ),
                    "inside_temp": data.climate_state.inside_temp,
                    "outside_temp": data.climate_state.outside_temp,
                    "is_climate_on": data.climate_state.is_climate_on,
                    "locked": data.vehicle_state.locked,
                    "odometer": data.vehicle_state.odometer,
                    "car_version": data.vehicle_state.car_version,
                }
            except Exception as exc:
                snapshot["fleet_api_error"] = str(exc)

        if self.can_interface and not isinstance(self.can_interface, MockCANInterface):
            snapshot["source"].append("can_bus")
            snapshot["can_bus"] = self.can_parser.get_state().to_dict()

        return snapshot

    def _build_tools(self) -> List[ToolDefinition]:
        """Build tool definitions for LLM function calling."""
        return [
            ToolDefinition(
                name="lock_doors",
                description="Lock the vehicle doors.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            ToolDefinition(
                name="unlock_doors",
                description="Unlock the vehicle doors.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            ToolDefinition(
                name="flash_lights",
                description="Flash the vehicle lights to locate it.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            ToolDefinition(
                name="honk_horn",
                description="Honk the vehicle horn.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            ToolDefinition(
                name="start_climate",
                description="Start the vehicle climate control (HVAC).",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            ToolDefinition(
                name="stop_climate",
                description="Stop the vehicle climate control (HVAC).",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            ToolDefinition(
                name="set_charge_limit",
                description="Set the vehicle charge limit percentage.",
                parameters={
                    "type": "object",
                    "properties": {
                        "percent": {
                            "type": "integer",
                            "description": "Charge limit percentage (50-100)",
                            "minimum": 50,
                            "maximum": 100,
                        }
                    },
                    "required": ["percent"],
                },
            ),
            ToolDefinition(
                name="set_climate_temperature",
                description="Set the vehicle climate temperature.",
                parameters={
                    "type": "object",
                    "properties": {
                        "driver_temp": {
                            "type": "number",
                            "description": "Driver side temperature in Celsius",
                        },
                        "passenger_temp": {
                            "type": "number",
                            "description": "Passenger side temperature in Celsius (optional)",
                        },
                    },
                    "required": ["driver_temp"],
                },
            ),
            ToolDefinition(
                name="navigation_request",
                description="Send a destination to the in-vehicle navigation.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Address or place name",
                        },
                        "locale": {
                            "type": "string",
                            "description": "Locale for the query (default zh-CN)",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single tool call against the vehicle.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            Dict with result or error.
        """
        if not self.vehicle:
            return {"tool": name, "error": "No vehicle instance available"}

        try:
            result = False
            if name == "lock_doors":
                result = await self.vehicle.lock_doors()
            elif name == "unlock_doors":
                result = await self.vehicle.unlock_doors()
            elif name == "flash_lights":
                result = await self.vehicle.flash_lights()
            elif name == "honk_horn":
                result = await self.vehicle.honk_horn()
            elif name == "start_climate":
                result = await self.vehicle.auto_conditioning_start()
            elif name == "stop_climate":
                result = await self.vehicle.auto_conditioning_stop()
            elif name == "set_charge_limit":
                percent = arguments.get("percent", 80)
                result = await self.vehicle.set_charge_limit(percent)
            elif name == "set_climate_temperature":
                driver_temp = arguments.get("driver_temp", 22.0)
                passenger_temp = arguments.get("passenger_temp")
                result = await self.vehicle.set_climate_temperature(
                    driver_temp, passenger_temp
                )
            elif name == "navigation_request":
                query = arguments.get("query", "")
                locale = arguments.get("locale", "zh-CN")
                result = await self.vehicle.navigation_request(query, locale)
            else:
                return {"tool": name, "error": f"Unknown tool: {name}"}

            return {"tool": name, "arguments": arguments, "result": result}

        except CommandFailedError as exc:
            return {"tool": name, "arguments": arguments, "error": str(exc)}
        except Exception as exc:
            return {"tool": name, "arguments": arguments, "error": f"{type(exc).__name__}: {exc}"}

    async def _execute_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Execute all tool calls and collect results."""
        results = []
        for tc in tool_calls:
            try:
                args = tc.arguments if hasattr(tc, "arguments") else tc.get("arguments", {})
                name = tc.name if hasattr(tc, "name") else tc.get("name", "")
                result = await self.execute_tool(name, args)
                results.append(result)
            except Exception as exc:
                results.append({"error": str(exc)})
        return results

    async def ask(
        self,
        question: str,
        enable_tools: bool = True,
    ) -> CopilotResponse:
        """
        Ask the copilot a question about the vehicle.

        Args:
            question: User question in natural language.
            enable_tools: Whether to allow LLM function calling.

        Returns:
            CopilotResponse with answer and any executed commands.
        """
        if not self.llm_adapter:
            return CopilotResponse(error="No LLM adapter configured")

        snapshot = await self._get_vehicle_snapshot()
        tools = self._build_tools() if enable_tools else None

        vehicle_state_text = json.dumps(snapshot, ensure_ascii=False, indent=2, default=str)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"当前车辆状态：\n{vehicle_state_text}\n\n"
                    f"用户问题：{question}"
                ),
            },
        ]

        try:
            llm_response = await self.llm_adapter.chat_completion(
                messages=messages,
                tools=tools,
                tool_choice="auto" if enable_tools else "none",
            )
        except Exception as exc:
            return CopilotResponse(
                error=f"LLM request failed: {self.llm_adapter.handle_error(exc)}"
            )

        response = CopilotResponse(
            content=llm_response.content,
            tool_calls=[
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                }
                for tc in llm_response.tool_calls
            ],
            vehicle_state=snapshot,
        )

        if llm_response.has_tool_calls and self.auto_execute_tools:
            response.executed_commands = await self._execute_tool_calls(
                llm_response.tool_calls
            )

        return response

    async def get_driving_advice(self) -> CopilotResponse:
        """Get AI-generated driving/charging advice based on current state."""
        prompt = (
            "根据当前车辆状态，给出 1-3 条简洁的驾驶或用车建议。"
            "例如：是否需要充电、空调设置、胎压/能耗提醒等。"
            "如果车辆正在行驶，请强调安全，不要分散驾驶员注意力。"
        )
        return await self.ask(prompt, enable_tools=False)

    async def summarize_trip(self) -> CopilotResponse:
        """Generate a natural language summary of current trip/vehicle status."""
        prompt = (
            "用一句话总结车辆当前状态，包括电量、车速、空调、门锁等关键信息。"
            "语气像一位贴心的随车助手。"
        )
        return await self.ask(prompt, enable_tools=False)

    async def diagnose(self) -> CopilotResponse:
        """Provide a diagnostic-style overview from CAN bus data."""
        prompt = (
            "基于 CAN 总线数据，分析车辆高压系统、电池温度、Autopilot 状态。"
            "如发现异常请指出；否则报告一切正常。"
        )
        return await self.ask(prompt, enable_tools=False)
