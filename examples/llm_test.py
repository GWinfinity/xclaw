"""
LLM Adapter Test

Test different LLM providers with xClaw.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from packages.llm_adapters import LLMFactory, create_llm_adapter


async def test_provider(provider: str):
    """Test a specific LLM provider."""
    print(f"\n{'='*60}")
    print(f"🧪 测试 {provider.upper()} 提供商")
    print('='*60)
    
    try:
        # Create adapter
        adapter = LLMFactory.create(provider)
        print(f"✅ 成功创建适配器")
        print(f"   模型: {adapter.model}")
        
        # Test simple completion
        messages = [
            {"role": "system", "content": "你是一个助手，用中文简短回答。"},
            {"role": "user", "content": "你好，请介绍一下自己"}
        ]
        
        print("\n📝 发送测试消息...")
        response = await adapter.chat_completion(messages)
        
        print(f"✅ 收到响应:")
        print(f"   内容: {response.content[:100]}...")
        print(f"   用量: {response.usage}")
        
        # Test with tools
        from packages.llm_adapters import ToolDefinition
        
        tools = [
            ToolDefinition(
                name="get_vehicle_data",
                description="获取特斯拉车辆数据",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
            )
        ]
        
        print("\n🔧 测试工具调用...")
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": "查看我的车辆状态"})
        
        response2 = await adapter.chat_completion(messages, tools=tools)
        
        if response2.has_tool_calls:
            print(f"✅ 工具调用成功:")
            for tc in response2.tool_calls:
                print(f"   工具: {tc.name}")
                print(f"   参数: {tc.arguments}")
        else:
            print(f"ℹ️  模型选择直接回答:")
            print(f"   {response2.content[:100]}...")
        
        await adapter.close()
        print(f"\n✅ {provider} 测试通过!")
        
    except Exception as e:
        print(f"\n❌ {provider} 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_all_providers():
    """Test all configured providers."""
    print("🦞 xClaw LLM 适配器测试")
    
    # Get provider from env or test all configured
    provider = os.getenv("LLM_PROVIDER")
    
    if provider:
        await test_provider(provider)
    else:
        # Test all providers that have API keys configured
        providers_to_test = []
        
        if os.getenv("OPENAI_API_KEY"):
            providers_to_test.append("openai")
        if os.getenv("QWEN_API_KEY"):
            providers_to_test.append("qwen")
        if os.getenv("ZHIPU_API_KEY"):
            providers_to_test.append("zhipu")
        if os.getenv("KIMI_API_KEY"):
            providers_to_test.append("kimi")
        if os.getenv("WENXIN_API_KEY"):
            providers_to_test.append("wenxin")
        if os.getenv("DEEPSEEK_API_KEY"):
            providers_to_test.append("deepseek")
        if os.getenv("STEP_API_KEY"):
            providers_to_test.append("step")
        if os.getenv("OPENROUTER_API_KEY"):
            providers_to_test.append("openrouter")
        if os.getenv("SPARK_API_KEY"):
            providers_to_test.append("spark")
        
        if not providers_to_test:
            print("❌ 没有找到配置好的 LLM 提供商")
            print("请设置以下环境变量之一:")
            print("  - OPENAI_API_KEY")
            print("  - QWEN_API_KEY")
            print("  - ZHIPU_API_KEY")
            print("  - KIMI_API_KEY")
            print("  - WENXIN_API_KEY")
            print("  - DEEPSEEK_API_KEY")
            print("  - STEP_API_KEY")
            print("  - SPARK_API_KEY")
            print("  - OPENROUTER_API_KEY")
            return
        
        print(f"\n找到 {len(providers_to_test)} 个配置好的提供商:")
        for p in providers_to_test:
            print(f"  - {p}")
        
        for provider in providers_to_test:
            await test_provider(provider)
    
    print("\n" + "="*60)
    print("🎉 测试完成!")


def list_providers():
    """List all available providers."""
    print("🦞 xClaw 支持的 LLM 提供商:\n")
    
    providers = LLMFactory.get_available_providers()
    
    for provider in providers:
        try:
            info = LLMFactory.get_provider_info(provider)
            print(f"📌 {provider}")
            print(f"   默认模型: {info['default_model']}")
            print(f"   环境变量:")
            for key, env_var in info['env_vars'].items():
                print(f"     - {env_var}")
            print()
        except Exception as e:
            print(f"❌ {provider}: {e}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LLM adapters")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有支持的提供商")
    parser.add_argument("--provider", "-p", type=str, help="测试特定提供商")
    
    args = parser.parse_args()
    
    if args.list:
        list_providers()
    elif args.provider:
        asyncio.run(test_provider(args.provider))
    else:
        asyncio.run(test_all_providers())
