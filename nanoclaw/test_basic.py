#!/usr/bin/env python3
"""
NanoClaw 基础功能测试

无需 Genesis 即可运行
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nanoclaw import NanoClaw
from nanoclaw.core import EventType


def test_basic_skill():
    """测试基础技能"""
    print("测试1: 基础技能...")
    
    agent = NanoClaw("test_agent")
    
    @agent.skill("add", description="加法")
    def add(context, a: int, b: int):
        return a + b
    
    result = agent.call("add", a=1, b=2)
    assert result['success'] == True
    assert result['result'] == 3
    
    print("   [PASS] 基础技能通过")


def test_context():
    """测试上下文管理"""
    print("测试2: 上下文管理...")
    
    agent = NanoClaw("test_agent")
    
    # 记忆
    agent.remember('key1', 'value1')
    
    # 回忆
    value = agent.recall('key1')
    assert value == 'value1'
    
    # 默认值
    value = agent.recall('nonexistent', 'default')
    assert value == 'default'
    
    print("   [PASS] 上下文管理通过")


def test_skill_chain():
    """测试技能链"""
    print("测试3: 技能链...")
    
    agent = NanoClaw("test_agent")
    
    @agent.skill("step1")
    def step1(context, **kwargs):
        context.set('step1_done', True)
        return 'step1_result'
    
    @agent.skill("step2")
    def step2(context, **kwargs):
        if context.get('step1_done'):
            return 'step2_result'
        return 'step2_failed'
    
    results = agent.chain(
        {'skill': 'step1'},
        {'skill': 'step2'}
    )
    
    assert len(results) == 2
    assert results[0]['result'] == 'step1_result'
    assert results[1]['result'] == 'step2_result'
    
    print("   [PASS] 技能链通过")


def test_events():
    """测试事件系统"""
    print("测试4: 事件系统...")
    
    agent = NanoClaw("test_agent")
    
    events_received = []
    
    def handler(event):
        events_received.append(event.type.value)
    
    agent.on(EventType.SKILL_CALLED, handler)
    agent.on(EventType.SKILL_COMPLETED, handler)
    
    @agent.skill("test")
    def test(context, **kwargs):
        return "ok"
    
    agent.call("test")
    
    assert 'skill_called' in events_received
    assert 'skill_completed' in events_received
    
    print("   [PASS] 事件系统通过")


def test_thinking():
    """测试思考记录"""
    print("测试5: 思考记录...")
    
    agent = NanoClaw("test_agent")
    
    agent.think("I need to plan the task")
    agent.think("First, I should detect objects")
    
    thoughts = agent.context.get('_thoughts', [])
    assert len(thoughts) == 2
    
    print("   [PASS] 思考记录通过")


def test_error_handling():
    """测试错误处理"""
    print("测试6: 错误处理...")
    
    agent = NanoClaw("test_agent")
    
    @agent.skill("fail")
    def fail(context, **kwargs):
        raise ValueError("Intentional error")
    
    result = agent.call("fail")
    
    assert result['success'] == False
    assert 'error' in result
    
    print("   [PASS] 错误处理通过")


def test_skill_info():
    """测试技能信息"""
    print("测试7: 技能信息...")
    
    agent = NanoClaw("test_agent")
    
    @agent.skill("test_skill", description="A test skill")
    def test_skill(context, **kwargs):
        return "result"
    
    # 调用几次
    agent.call("test_skill")
    agent.call("test_skill")
    
    info = agent.info()
    
    assert 'test_skill' in info['skills']
    assert info['skills']['test_skill']['call_count'] == 2
    
    print("   [PASS] 技能信息通过")


def main():
    print("=" * 60)
    print("NanoClaw 基础功能测试")
    print("=" * 60)
    
    try:
        test_basic_skill()
        test_context()
        test_skill_chain()
        test_events()
        test_thinking()
        test_error_handling()
        test_skill_info()
        
        print("\n" + "=" * 60)
        print("所有测试通过! [PASS]")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
