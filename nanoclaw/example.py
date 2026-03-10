#!/usr/bin/env python3
"""
NanoClaw + Genesis 集成示例

展示如何使用 NanoClaw Agent 控制 genesis-cloud-sim 仿真环境
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO)

from nanoclaw import NanoClaw, GenesisIntegration, SimConfig


def example_basic():
    """示例1: 基础用法 - 创建 Agent 并调用仿真"""
    print("=" * 60)
    print("示例1: 基础用法")
    print("=" * 60)
    
    # 创建 Agent
    agent = NanoClaw("basic_agent")
    
    # 创建 Genesis 集成
    integration = GenesisIntegration(agent)
    integration.setup(SimConfig(
        task_id="pick_object",
        seed=42,
        headless=True,
        record=True
    ))
    
    try:
        # 1. 重置环境
        print("\n1. 重置环境...")
        result = agent.call("sim.reset", task_id="pick_object", seed=42)
        print(f"   结果: {result}")
        
        # 2. 获取观测
        print("\n2. 获取观测...")
        result = agent.call("sim.get_obs")
        print(f"   成功: {result['success']}")
        
        # 3. 执行几步
        print("\n3. 执行随机动作...")
        for i in range(3):
            import random
            action = {'joint_positions': [random.uniform(-0.1, 0.1) for _ in range(7)]}
            result = agent.call("sim.step", action=action)
            print(f"   Step {i+1}: reward={result.get('result', {}).get('reward', 0):.3f}")
        
        # 4. 运行完整 episode
        print("\n4. 运行完整 episode...")
        result = agent.call("sim.run_episode", max_steps=50)
        if result['success']:
            print(f"   Episode 完成: {result['result']['steps']} steps, "
                  f"reward={result['result']['total_reward']:.2f}")
        
    finally:
        # 关闭
        agent.call("sim.close")
        integration.close()
    
    print("\n✓ 示例1完成")


def example_custom_skills():
    """示例2: 自定义技能与仿真结合"""
    print("\n" + "=" * 60)
    print("示例2: 自定义技能")
    print("=" * 60)
    
    agent = NanoClaw("custom_agent")
    integration = GenesisIntegration(agent)
    integration.setup(SimConfig(headless=True))
    
    # 注册自定义感知技能
    @agent.skill("perceive.objects", description="检测场景中的物体")
    def perceive_objects(context, **kwargs):
        """模拟物体检测"""
        # 实际应调用视觉模型
        objects = [
            {'id': 'cup', 'position': [0.3, 0.2, 0.1], 'confidence': 0.95},
            {'id': 'plate', 'position': [0.5, -0.1, 0.1], 'confidence': 0.87}
        ]
        context.set('detected_objects', objects)
        return objects
    
    # 注册自定义规划技能
    @agent.skill("plan.grasp", description="规划抓取动作")
    def plan_grasp(context, object_id: str = None, **kwargs):
        """规划抓取"""
        objects = context.get('detected_objects', [])
        target = next((o for o in objects if o['id'] == object_id), None)
        
        if target is None:
            return {'success': False, 'error': f'Object {object_id} not found'}
        
        # 生成抓取轨迹
        plan = {
            'approach': [target['position'][0], target['position'][1], target['position'][2] + 0.1],
            'grasp': target['position'],
            'lift': [target['position'][0], target['position'][1], target['position'][2] + 0.2]
        }
        context.set('grasp_plan', plan)
        return plan
    
    # 注册执行技能
    @agent.skill("execute.grasp", description="执行抓取")
    def execute_grasp(context, **kwargs):
        """执行抓取动作序列"""
        plan = context.get('grasp_plan')
        if not plan:
            return {'success': False, 'error': 'No grasp plan'}
        
        results = []
        
        # 接近
        result = agent.call("sim.step", action={'joint_positions': plan['approach']})
        results.append(('approach', result['success']))
        
        # 抓取
        result = agent.call("sim.step", action={'joint_positions': plan['grasp']})
        results.append(('grasp', result['success']))
        
        # 抬起
        result = agent.call("sim.step", action={'joint_positions': plan['lift']})
        results.append(('lift', result['success']))
        
        return {'success': True, 'steps': results}
    
    try:
        # 重置
        agent.call("sim.reset", task_id="pick_object", seed=0)
        
        # 执行完整任务链
        print("\n执行任务链: 感知 -> 规划 -> 执行")
        
        # 感知
        result = agent.call("perceive.objects")
        print(f"   检测到 {len(result['result'])} 个物体")
        
        # 规划
        result = agent.call("plan.grasp", object_id="cup")
        print(f"   规划完成: {result['result']}")
        
        # 执行
        result = agent.call("execute.grasp")
        print(f"   执行结果: {result}")
        
    finally:
        integration.close()
    
    print("\n✓ 示例2完成")


def example_agent_thinking():
    """示例3: Agent 思考与状态管理"""
    print("\n" + "=" * 60)
    print("示例3: Agent 思考与状态管理")
    print("=" * 60)
    
    agent = NanoClaw("thinking_agent")
    
    # Agent 思考过程
    agent.think("我需要完成抓取任务，首先应该检测环境中的物体")
    
    # 记忆信息
    agent.remember('task_goal', 'pick_up_cup')
    agent.remember('safety_constraints', ['max_force', 'collision_avoidance'])
    
    # 回忆信息
    goal = agent.recall('task_goal')
    print(f"\n当前任务目标: {goal}")
    
    # 思考下一步
    agent.think("我已经知道目标是 pick_up_cup，现在需要规划抓取路径")
    
    # 查看上下文
    print("\nAgent 上下文状态:")
    print(f"   Session ID: {agent.context.session_id}")
    print(f"   记忆条目: {list(agent.context.state.keys())}")
    print(f"   历史记录: {len(agent.context.history)} 条")
    
    print("\n✓ 示例3完成")


def example_task_chain():
    """示例4: 复杂任务链"""
    print("\n" + "=" * 60)
    print("示例4: 复杂任务链")
    print("=" * 60)
    
    agent = NanoClaw("chain_agent")
    
    # 定义一个多步骤任务
    @agent.skill("task.prepare_meal", description="准备简单餐食")
    def prepare_meal(context, **kwargs):
        """多步骤任务示例"""
        steps = [
            {'skill': 'perceive.objects', 'args': {}},
            {'skill': 'plan.grasp', 'args': {'object_id': 'ingredient'}},
            {'skill': 'execute.grasp', 'args': {}},
            # ... 更多步骤
        ]
        
        results = []
        for i, step in enumerate(steps):
            agent.think(f"执行步骤 {i+1}: {step['skill']}")
            result = agent.call(step['skill'], **step['args'])
            results.append(result)
            
            if not result['success']:
                agent.think(f"步骤 {i+1} 失败，尝试恢复策略")
                # 错误恢复逻辑
        
        return {'success': True, 'steps_completed': len(results)}
    
    # 使用 chain 方法执行
    print("\n执行技能链:")
    results = agent.chain(
        {'skill': 'perceive.objects', 'args': {}},
        {'skill': 'plan.grasp', 'args': {'object_id': 'cup'}},
        {'skill': 'task.prepare_meal', 'args': {}}
    )
    
    print(f"   链执行完成，共 {len(results)} 个结果")
    
    print("\n✓ 示例4完成")


def example_event_driven():
    """示例5: 事件驱动"""
    print("\n" + "=" * 60)
    print("示例5: 事件驱动")
    print("=" * 60)
    
    agent = NanoClaw("event_agent")
    
    # 订阅事件
    from nanoclaw import EventType
    
    event_log = []
    
    def on_skill_called(event):
        event_log.append(f"[CALLED] {event.data['skill']}")
    
    def on_skill_completed(event):
        event_log.append(f"[COMPLETED] {event.data['skill']}")
    
    agent.on(EventType.SKILL_CALLED, on_skill_called)
    agent.on(EventType.SKILL_COMPLETED, on_skill_completed)
    
    # 注册测试技能
    @agent.skill("test.skill1")
    def test_skill1(context, **kwargs):
        return "skill1_result"
    
    @agent.skill("test.skill2")
    def test_skill2(context, **kwargs):
        return "skill2_result"
    
    # 调用技能
    print("\n调用技能 (带事件记录):")
    agent.call("test.skill1")
    agent.call("test.skill2")
    
    print("\n事件日志:")
    for log in event_log:
        print(f"   {log}")
    
    print("\n✓ 示例5完成")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("NanoClaw + Genesis 集成示例")
    print("=" * 60)
    
    try:
        # 运行示例
        example_basic()
        example_custom_skills()
        example_agent_thinking()
        example_task_chain()
        example_event_driven()
        
        print("\n" + "=" * 60)
        print("所有示例完成!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
