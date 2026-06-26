"""
Tests for Tesla AI Copilot.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from packages.llm_adapters.base import LLMResponse, ToolCall

from .ai_copilot import TeslaAICopilot, CopilotResponse


class MockLLMAdapter:
    """Simple mock LLM adapter for testing."""

    def __init__(self, response: LLMResponse):
        self.response = response

    async def chat_completion(self, messages, tools=None, tool_choice="auto"):
        return self.response

    def handle_error(self, error):
        return str(error)


class TestTeslaAICopilot:
    """Test AI copilot behavior."""

    @pytest.mark.asyncio
    async def test_ask_without_llm_returns_error(self):
        copilot = TeslaAICopilot()
        result = await copilot.ask("hello")
        assert result.error is not None
        assert "No LLM adapter" in result.error

    @pytest.mark.asyncio
    async def test_ask_with_llm_no_tools(self):
        llm = MockLLMAdapter(LLMResponse(content="电量充足，无需充电。"))
        copilot = TeslaAICopilot(llm_adapter=llm)
        result = await copilot.ask("我应该现在充电吗？", enable_tools=False)

        assert isinstance(result, CopilotResponse)
        assert result.content == "电量充足，无需充电。"
        assert result.error is None
        assert result.vehicle_state is not None

    @pytest.mark.asyncio
    async def test_ask_with_tool_call_auto_execute(self):
        tool_call = ToolCall(
            id="call_1",
            name="flash_lights",
            arguments={},
        )
        llm = MockLLMAdapter(
            LLMResponse(
                content="正在闪灯帮您找车。",
                tool_calls=[tool_call],
            )
        )

        vehicle = MagicMock()
        vehicle.flash_lights = AsyncMock(return_value=True)
        vehicle.platform_info.to_dict.return_value = {"model_type": "model3"}
        vehicle.get_vehicle_data = AsyncMock(
            side_effect=Exception("offline for test")
        )

        copilot = TeslaAICopilot(
            vehicle=vehicle,
            llm_adapter=llm,
            auto_execute_tools=True,
        )
        result = await copilot.ask("我在哪？")

        assert result.content == "正在闪灯帮您找车。"
        assert len(result.tool_calls) == 1
        assert len(result.executed_commands) == 1
        assert result.executed_commands[0]["result"] is True
        vehicle.flash_lights.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ask_with_tool_call_no_auto_execute(self):
        tool_call = ToolCall(
            id="call_1",
            name="lock_doors",
            arguments={},
        )
        llm = MockLLMAdapter(
            LLMResponse(
                content="建议锁车。",
                tool_calls=[tool_call],
            )
        )

        vehicle = MagicMock()
        vehicle.lock_doors = AsyncMock(return_value=True)
        vehicle.platform_info.to_dict.return_value = {"model_type": "model3"}
        vehicle.get_vehicle_data = AsyncMock(
            side_effect=Exception("offline for test")
        )

        copilot = TeslaAICopilot(
            vehicle=vehicle,
            llm_adapter=llm,
            auto_execute_tools=False,
        )
        result = await copilot.ask("锁车")

        assert len(result.tool_calls) == 1
        assert len(result.executed_commands) == 0
        vehicle.lock_doors.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_tool_unknown_tool(self):
        vehicle = MagicMock()
        vehicle.platform_info.to_dict.return_value = {"model_type": "model3"}
        copilot = TeslaAICopilot(vehicle=vehicle)

        result = await copilot.execute_tool("unknown_tool", {})
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_driving_advice(self):
        llm = MockLLMAdapter(LLMResponse(content="建议保持当前速度。"))
        copilot = TeslaAICopilot(llm_adapter=llm)
        result = await copilot.get_driving_advice()

        assert result.content == "建议保持当前速度。"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_can_frame_handler_updates_state(self):
        from .can_bus import CANFrame, MockCANInterface

        can = MockCANInterface(listen_only=True)
        copilot = TeslaAICopilot(can_interface=can)

        can.inject_frame(CANFrame(can_id=0x398, data=bytes.fromhex("8000000000000000")))
        await can.start_rx_loop()
        import asyncio

        await asyncio.sleep(0.05)
        await can.stop_rx_loop()

        assert copilot.can_parser.state.hw_version.value == "hw3"
