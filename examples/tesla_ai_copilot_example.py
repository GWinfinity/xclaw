"""
Tesla AI Copilot Example

Demonstrates how to combine:
- Tesla Fleet API (vehicle state + commands)
- CAN bus interface (M5StickS3 / ESP32 bridge)
- User's LLM API (via packages.llm_adapters)

Hardware:
- Option A: Fleet API only (no extra hardware)
- Option B: M5StickS3 + external CAN transceiver plugged into car OBD-II/X179

Safety:
- CAN bus defaults to listen-only mode.
- Call enable_tx() only after you understand the risks and legal implications.
"""

import asyncio

from packages.llm_adapters import LLMFactory
from packages.tesla_client import (
    TeslaFleetClient,
    TeslaAICopilot,
    M5StickS3Interface,
    MockCANInterface,
)


async def main():
    # 1. Create Fleet API client
    client = TeslaFleetClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        region="cn",
        # Or load from env: TESLA_CLIENT_ID / TESLA_CLIENT_SECRET
    )

    # 2. Pick a vehicle
    vehicles = await client.get_vehicles()
    if not vehicles:
        print("No vehicles found")
        return

    vehicle = vehicles[0]
    print(f"Connected to: {vehicle.display_name} ({vehicle.vin})")

    # 3. Create CAN interface
    # For real hardware:
    # can = M5StickS3Interface(port="COM3", listen_only=True)
    # For desktop testing:
    can = MockCANInterface(listen_only=True)
    await can.start_rx_loop()

    # 4. Create LLM adapter from environment (LLM_PROVIDER, OPENAI_API_KEY, etc.)
    llm = LLMFactory.create_from_env()

    # 5. Create AI copilot
    copilot = TeslaAICopilot(
        vehicle=vehicle,
        llm_adapter=llm,
        can_interface=can,
        auto_execute_tools=False,  # Require manual approval for commands
    )

    # 6. Ask questions
    response = await copilot.ask("我应该现在充电吗？")
    print("AI:", response.content)

    response = await copilot.get_driving_advice()
    print("Advice:", response.content)

    # 7. If LLM suggests a tool call, you can review and execute manually:
    if response.tool_calls:
        print("Suggested commands:", response.tool_calls)
        # await copilot.execute_tool("flash_lights", {})

    # 8. Cleanup
    await can.stop_rx_loop()
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
