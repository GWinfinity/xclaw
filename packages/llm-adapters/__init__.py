"""
xClaw LLM Adapters

Universal adapter for multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5, GPT-4o)
- Baidu ERNIE-Bot
- Alibaba Qwen
- Zhipu AI (ChatGLM/GLM-4)
- Moonshot Kimi
- iFlytek Spark
- DeepSeek
- StepFun (阶跃星辰)
- OpenRouter
- xAI (Grok)

Usage:
    # Create adapter from environment
    from packages.llm_adapters import LLMFactory
    adapter = LLMFactory.create_from_env()
    
    # Create specific adapter
    adapter = LLMFactory.create("qwen", api_key="your_key")
    
    # Use in agent
    from packages.xclaw_core import XClawAgent
    agent = XClawAgent(vehicle, llm_adapter=adapter)
"""

from .base import BaseLLMAdapter, LLMResponse, ToolCall, ToolDefinition, LLMProvider
from .factory import LLMFactory, create_llm_adapter
from .openai_adapter import OpenAIAdapter
from .wenxin_adapter import WenxinAdapter
from .qwen_adapter import QwenAdapter
from .zhipu_adapter import ZhipuAdapter
from .kimi_adapter import KimiAdapter
from .spark_adapter import SparkAdapter
from .deepseek_adapter import DeepseekAdapter
from .step_adapter import StepAdapter
from .openrouter_adapter import OpenRouterAdapter
from .xai_adapter import XAIAdapter

__version__ = "0.1.0"
__all__ = [
    # Base classes
    "BaseLLMAdapter",
    "LLMResponse", 
    "ToolCall",
    "ToolDefinition",
    "LLMProvider",
    # Factory
    "LLMFactory",
    "create_llm_adapter",
    # Adapters
    "OpenAIAdapter",
    "WenxinAdapter",
    "QwenAdapter",
    "ZhipuAdapter",
    "KimiAdapter",
    "SparkAdapter",
    "DeepseekAdapter",
    "StepAdapter",
    "OpenRouterAdapter",
    "XAIAdapter",
]
