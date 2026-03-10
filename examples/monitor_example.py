"""
Vehicle Monitor Example

Example of monitoring vehicle state changes.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from packages.tesla_client import TeslaFleetClient
from packages.xclaw_core import VehicleContext
from tools.monitor import VehicleMonitor, VehicleEvent


async def on_battery_change(event: VehicleEvent):
    """Handle battery level changes."""
    data = event.data
    old = data.get("old")
    new = data.get("new")
    delta = new - old
    
    print(f"\n🔋 电池变化: {old}% → {new}% ({'+' if delta > 0 else ''}{delta}%)")
    
    if new <= 20:
        print("⚠️ 警告: 电量低于 20%!")


async def on_charging_change(event: VehicleEvent):
    """Handle charging state changes."""
    data = event.data
    new_state = data.get("new")
    
    messages = {
        "Charging": "🔌 开始充电",
        "Complete": "✅ 充电完成",
        "Stopped": "⏹️ 充电停止",
        "Disconnected": "🔌 充电器断开",
    }
    
    print(f"\n{messages.get(new_state, f'充电状态: {new_state}')}")


async def on_lock_change(event: VehicleEvent):
    """Handle lock state changes."""
    locked = event.data.get("locked")
    print(f"\n{'🔒' if locked else '🔓'} 车辆已{'锁定' if locked else '解锁'}")


async def on_climate_change(event: VehicleEvent):
    """Handle climate changes."""
    is_on = event.data.get("is_on")
    print(f"\n{'❄️' if is_on else '⭕'} 空调已{'开启' if is_on else '关闭'}")


async def on_location_change(event: VehicleEvent):
    """Handle location changes."""
    distance = event.data.get("distance_km")
    speed = event.data.get("speed")
    
    speed_str = f" 速度: {speed} km/h" if speed else ""
    print(f"\n🚗 车辆移动: {distance} km{speed_str}")


async def main():
    """Main monitoring loop."""
    print("🦞 xClaw Vehicle Monitor\n")
    
    client = TeslaFleetClient(
        client_id=os.getenv("TESLA_CLIENT_ID"),
        client_secret=os.getenv("TESLA_CLIENT_SECRET"),
        region=os.getenv("TESLA_REGION", "cn"),
    )
    
    try:
        # Create vehicle context
        context = VehicleContext(client=client)
        
        # Create monitor
        monitor = VehicleMonitor(context)
        
        # Register event handlers
        monitor.on_event(on_battery_change)
        monitor.on_event(on_charging_change)
        monitor.on_event(on_lock_change)
        monitor.on_event(on_climate_change)
        monitor.on_event(on_location_change)
        
        print("🔍 开始监控车辆...")
        print("按 Ctrl+C 停止\n")
        
        try:
            await monitor.start(interval=30)
        except KeyboardInterrupt:
            print("\n\n🛑 停止监控...")
            monitor.stop()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
