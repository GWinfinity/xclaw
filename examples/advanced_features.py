"""
xClaw Advanced Features Example

Demonstrates all Hermes Agent-inspired features:
- Persistent memory with FTS5 search
- Multi-step planning
- Skill auto-learning
- Context compression
- Safety guardrails
- Scheduled tasks
- Structured logging
"""

import asyncio
from packages.xclaw_core import (
    XClawAgent,
    VehicleContext,
    PersistentMemory,
    setup_logging,
    SafetyGuard,
    TaskScheduler,
    Planner,
    SkillLearner,
)


async def demo_persistent_memory():
    """Demo: Persistent memory across sessions."""
    print("\n🧠 === 持久化记忆演示 ===\n")
    
    context = VehicleContext()
    agent = XClawAgent(
        context,
        user_id="demo_user",
        enable_persistent_memory=True,
    )
    
    # Session 1: Learn user preferences
    response = await agent.process("我习惯车内温度22度，充电一般冲到80%")
    print(f"Session 1: {response.message}")
    
    # Simulate session end
    await agent.close()
    
    # Session 2: Agent remembers preferences
    agent2 = XClawAgent(
        context,
        user_id="demo_user",
        enable_persistent_memory=True,
    )
    
    response = await agent2.process("车里太热了")
    print(f"Session 2: {response.message}")
    # Agent will set to 22°C based on learned preference
    
    # Search memories
    if agent2.persistent_memory:
        memories = agent2.persistent_memory.search_memories("温度", "demo_user")
        print(f"\n搜索到 {len(memories)} 条相关记忆")
    
    await agent2.close()


async def demo_multi_step_planning():
    """Demo: Multi-step planning for complex requests."""
    print("\n📋 === 多步规划演示 ===\n")
    
    context = VehicleContext()
    agent = XClawAgent(
        context,
        enable_planner=True,
    )
    
    # Complex multi-step request
    response = await agent.process(
        "明天早上8点出门前，把车预热到24度，充到80%，然后锁车开哨兵"
    )
    print(f"计划: {response.plan_summary}")
    print(f"回复: {response.message}")
    
    await agent.close()


async def demo_safety_guardrails():
    """Demo: Safety guardrails with rate limiting."""
    print("\n🔒 === 安全护栏演示 ===\n")
    
    context = VehicleContext()
    agent = XClawAgent(
        context,
        user_id="demo_user",
        enable_safety=True,
    )
    
    # Normal command
    response = await agent.process("锁车")
    print(f"锁车: {response.message}")
    
    # Get audit summary
    summary = agent.get_audit_summary(hours=1)
    print(f"\n审计摘要: {summary}")
    
    await agent.close()


async def demo_scheduled_tasks():
    """Demo: Scheduled task management."""
    print("\n⏰ === 定时任务演示 ===\n")
    
    context = VehicleContext()
    agent = XClawAgent(
        context,
        user_id="demo_user",
        enable_persistent_memory=True,
    )
    
    # Schedule climate control
    task_id = agent.scheduler.schedule_climate(
        user_id="demo_user",
        time_str="2024-01-15T07:45:00",
        temperature=24.0,
        name="早起预热"
    )
    print(f"创建定时任务: {task_id}")
    
    # Schedule charging
    task_id = agent.scheduler.schedule_charging(
        user_id="demo_user",
        target_time="2024-01-15T07:00:00",
        target_percent=80,
        name="上班前充电"
    )
    print(f"创建充电任务: {task_id}")
    
    # Schedule recurring check
    task_id = agent.scheduler.schedule_recurring_check(
        user_id="demo_user",
        interval_hours=6,
        name="定期检查"
    )
    print(f"创建定期检查: {task_id}")
    
    # Get user tasks
    tasks = agent.persistent_memory.get_user_tasks("demo_user")
    print(f"\n用户任务数: {len(tasks)}")
    for task in tasks:
        print(f"  - {task['name']}: {task['description']}")
    
    await agent.close()


async def demo_skill_learning():
    """Demo: Automatic skill learning."""
    print("\n🎯 === 技能学习演示 ===\n")
    
    context = VehicleContext()
    agent = XClawAgent(
        context,
        user_id="demo_user",
        enable_skill_learning=True,
    )
    
    # Simulate repeated patterns
    for i in range(3):
        response = await agent.process("帮我锁车然后开哨兵模式")
        print(f"第 {i+1} 次: {response.message}")
    
    # Check learned skills
    if agent.skill_learner:
        skill = agent.skill_learner.find_matching_skill("锁车开哨兵")
        if skill:
            print(f"\n学习到技能: {skill['name']}")
            print(f"描述: {skill['description']}")
            print(f"成功次数: {skill['success_count']}")
    
    await agent.close()


async def demo_context_compression():
    """Demo: Context compression for long conversations."""
    print("\n🗜️ === 上下文压缩演示 ===\n")
    
    context = VehicleContext()
    agent = XClawAgent(context)
    
    # Simulate long conversation
    messages = [
        "今天天气怎么样？",
        "帮我检查一下电池",
        "开启空调",
        "设置温度到22度",
        "锁车",
        "查看充电状态",
        "开始充电",
        "设置充电限制到80%",
        "关闭空调",
        "解锁车门",
        "打开后备箱",
        "关闭后备箱",
        "开启哨兵模式",
        "查看车辆位置",
        "鸣笛一下",
    ]
    
    for msg in messages:
        await agent.process(msg)
    
    # Check if compression happened
    conv = agent.memory.get_messages("default", limit=50)
    print(f"对话消息数: {len(conv)}")
    
    if agent.compressor.needs_compression(conv):
        compressed = agent.compressor.compress(conv)
        print(f"压缩后消息数: {len(compressed)}")
    
    await agent.close()


async def demo_structured_logging():
    """Demo: Structured logging."""
    print("\n📊 === 结构化日志演示 ===\n")
    
    # Setup structured logging
    setup_logging(level="INFO", format="text", service_name="xclaw-demo")
    
    context = VehicleContext()
    agent = XClawAgent(context)
    
    # Process a command (will generate structured logs)
    response = await agent.process("检查电池状态")
    print(f"回复: {response.message}")
    
    await agent.close()


async def demo_full_workflow():
    """Demo: Complete workflow with all features."""
    print("\n🚗 === 完整工作流演示 ===\n")
    
    # Setup logging
    setup_logging(level="INFO", format="text")
    
    context = VehicleContext()
    
    # Create agent with all features
    agent = XClawAgent(
        context,
        user_id="power_user",
        enable_persistent_memory=True,
        enable_safety=True,
        enable_planner=True,
        enable_skill_learning=True,
    )
    
    # Start scheduler
    await agent.start_scheduler()
    
    print("1. 学习用户偏好...")
    await agent.process("我习惯温度22度，充电到80%")
    
    print("\n2. 复杂命令规划...")
    response = await agent.process("明天早上出门前准备好车")
    print(f"   {response.message}")
    
    print("\n3. 定时任务...")
    agent.scheduler.schedule_climate(
        "power_user", "2024-01-15T07:45:00", 22.0
    )
    
    print("\n4. 车辆控制...")
    await agent.process("锁车开哨兵")
    
    print("\n5. 状态查询...")
    summary = await agent.get_vehicle_summary()
    print(summary)
    
    print("\n6. 审计报告...")
    audit = agent.get_audit_summary()
    print(f"   命令数: {audit.get('total_commands', 0)}")
    
    print("\n7. 记忆统计...")
    stats = agent.get_memory_stats()
    print(f"   {stats}")
    
    await agent.close()
    print("\n✅ 演示完成!")


async def main():
    """Run all demos."""
    print("🦞 xClaw 高级功能演示")
    print("=" * 50)
    
    # Run individual demos
    await demo_persistent_memory()
    await demo_multi_step_planning()
    await demo_safety_guardrails()
    await demo_scheduled_tasks()
    await demo_skill_learning()
    await demo_context_compression()
    await demo_structured_logging()
    
    # Or run the full workflow
    # await demo_full_workflow()


if __name__ == "__main__":
    asyncio.run(main())
