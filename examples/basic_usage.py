"""
xClaw Basic Usage Example

Demonstrates basic Tesla vehicle control using xClaw.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from packages.tesla_client import TeslaFleetClient
from packages.xclaw_core import XClawAgent, VehicleContext


async def basic_vehicle_control():
    """Basic vehicle control example."""
    print("🦞 xClaw Basic Usage Example\n")
    
    # Create Tesla client
    client = TeslaFleetClient(
        client_id=os.getenv("TESLA_CLIENT_ID"),
        client_secret=os.getenv("TESLA_CLIENT_SECRET"),
        region=os.getenv("TESLA_REGION", "cn"),
    )
    
    try:
        # List vehicles
        print("📋 获取车辆列表...")
        vehicles = await client.get_vehicles()
        
        if not vehicles:
            print("❌ 没有找到车辆")
            return
        
        print(f"✅ 找到 {len(vehicles)} 辆车:\n")
        
        for v in vehicles:
            print(f"  • {v.display_name} ({v.vin})")
            print(f"    状态: {v.state}")
        
        # Use first vehicle
        vehicle = vehicles[0]
        print(f"\n🚗 使用车辆: {vehicle.display_name}\n")
        
        # Create vehicle context
        context = VehicleContext(vin=vehicle.vin, client=client)
        
        # Create AI agent
        agent = XClawAgent(
            vehicle_context=context,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        # Get vehicle status
        print("📊 获取车辆状态...\n")
        summary = await agent.get_vehicle_summary()
        print(summary)
        print()
        
        # Example: Natural language control
        commands = [
            "查看车辆状态",
            "还剩多少电",
            "车里温度多少",
        ]
        
        for cmd in commands:
            print(f"👤 用户: {cmd}")
            response = await agent.process(cmd)
            print(f"🤖 AI: {response.message}\n")
            await asyncio.sleep(1)
        
        print("✅ 示例完成!")
        
    finally:
        await client.close()


async def direct_api_example():
    """Direct API usage example."""
    print("\n🦞 Direct API Example\n")
    
    client = TeslaFleetClient(
        client_id=os.getenv("TESLA_CLIENT_ID"),
        client_secret=os.getenv("TESLA_CLIENT_SECRET"),
        region=os.getenv("TESLA_REGION", "cn"),
    )
    
    try:
        # Get vehicles
        vehicles = await client.get_vehicles()
        if not vehicles:
            print("❌ 没有找到车辆")
            return
        
        vehicle = vehicles[0]
        
        # Wake up vehicle
        print("⏰ 唤醒车辆...")
        is_awake = await vehicle.wake_up()
        print(f"  车辆已唤醒: {is_awake}\n")
        
        # Get detailed data
        print("📊 获取车辆数据...")
        data = await vehicle.get_vehicle_data()
        
        print(f"\n  车辆: {data.display_name}")
        print(f"  VIN: {data.vin}")
        print(f"\n  🔋 电池:")
        print(f"    电量: {data.charge_state.battery_level}%")
        print(f"    续航: {int(data.charge_state.battery_range * 1.60934)} km")
        print(f"    充电状态: {data.charge_state.charging_state.value}")
        
        print(f"\n  🌡️ 空调:")
        print(f"    状态: {'开启' if data.climate_state.is_climate_on else '关闭'}")
        print(f"    设定温度: {data.climate_state.driver_temp_setting}°C")
        if data.climate_state.inside_temp:
            print(f"    车内温度: {data.climate_state.inside_temp:.1f}°C")
        
        print(f"\n  🔒 状态:")
        print(f"    锁定: {'是' if data.vehicle_state.locked else '否'}")
        print(f"    哨兵模式: {'开启' if data.vehicle_state.sentry_mode else '关闭'}")
        
        if data.drive_state.latitude and data.drive_state.longitude:
            print(f"\n  📍 位置:")
            print(f"    纬度: {data.drive_state.latitude}")
            print(f"    经度: {data.drive_state.longitude}")
        
    finally:
        await client.close()


async def advanced_control_example():
    """Advanced control example."""
    print("\n🦞 Advanced Control Example\n")
    
    client = TeslaFleetClient(
        client_id=os.getenv("TESLA_CLIENT_ID"),
        client_secret=os.getenv("TESLA_CLIENT_SECRET"),
        region=os.getenv("TESLA_REGION", "cn"),
    )
    
    try:
        vehicles = await client.get_vehicles()
        if not vehicles:
            print("❌ 没有找到车辆")
            return
        
        vehicle = vehicles[0]
        
        # Ensure vehicle is awake
        print("⏰ 唤醒车辆...")
        await vehicle.wake_up()
        
        # Examples of various controls
        # NOTE: Uncomment to actually execute
        
        # print("🔒 锁定车辆...")
        # result = await vehicle.lock_doors()
        # print(f"  结果: {result}")
        
        # print("\n❄️ 开启空调并设置温度...")
        # await vehicle.auto_conditioning_start()
        # await vehicle.set_climate_temperature(22.0)
        
        # print("\n🔋 设置充电限制...")
        # await vehicle.set_charge_limit(80)
        
        print("\n📢 鸣笛并闪灯...")
        await vehicle.honk_horn()
        await asyncio.sleep(0.5)
        await vehicle.flash_lights()
        print("  完成!")
        
    finally:
        await client.close()


async def interactive_mode():
    """Interactive mode example."""
    print("\n🦞 xClaw Interactive Mode\n")
    print("输入自然语言命令控制你的特斯拉")
    print("输入 'quit' 或 'exit' 退出\n")
    
    client = TeslaFleetClient(
        client_id=os.getenv("TESLA_CLIENT_ID"),
        client_secret=os.getenv("TESLA_CLIENT_SECRET"),
        region=os.getenv("TESLA_REGION", "cn"),
    )
    
    try:
        context = VehicleContext(client=client)
        agent = XClawAgent(
            vehicle_context=context,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        while True:
            try:
                user_input = input("👤 > ").strip()
                
                if user_input.lower() in ["quit", "exit", "退出"]:
                    print("👋 再见!")
                    break
                
                if not user_input:
                    continue
                
                print()
                response = await agent.process(user_input)
                print(f"🤖 {response.message}\n")
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}\n")
    
    finally:
        await client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "direct":
            asyncio.run(direct_api_example())
        elif mode == "advanced":
            asyncio.run(advanced_control_example())
        elif mode == "interactive":
            asyncio.run(interactive_mode())
        else:
            asyncio.run(basic_vehicle_control())
    else:
        asyncio.run(basic_vehicle_control())
