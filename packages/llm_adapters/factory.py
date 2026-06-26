"""
LLM Factory

Factory for creating LLM adapters based on configuration.
"""

import os
from typing import Optional, Dict, Any

from .base import BaseLLMAdapter, LLMProvider
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


class LLMFactory:
    """
    Factory for creating LLM adapters.
    
    Usage:
        # From environment variables
        adapter = LLMFactory.create_from_env()
        
        # Explicit creation
        adapter = LLMFactory.create(
            provider="qwen",
            api_key="your_key",
            model="qwen-max"
        )
    """
    
    # Provider to adapter mapping
    ADAPTERS = {
        LLMProvider.OPENAI: OpenAIAdapter,
        LLMProvider.WENXIN: WenxinAdapter,
        LLMProvider.QWEN: QwenAdapter,
        LLMProvider.ZHIPU: ZhipuAdapter,
        LLMProvider.KIMI: KimiAdapter,
        LLMProvider.SPARK: SparkAdapter,
        LLMProvider.DEEPSEEK: DeepseekAdapter,
        LLMProvider.STEP: StepAdapter,
        LLMProvider.OPENROUTER: OpenRouterAdapter,
        LLMProvider.XAI: XAIAdapter,
    }
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        LLMProvider.OPENAI: {
            "api_key": "OPENAI_API_KEY",
            "model": "OPENAI_MODEL",
            "api_base": "OPENAI_API_BASE",
        },
        LLMProvider.WENXIN: {
            "api_key": "WENXIN_API_KEY",
            "api_secret": "WENXIN_SECRET_KEY",
            "model": "WENXIN_MODEL",
        },
        LLMProvider.QWEN: {
            "api_key": "QWEN_API_KEY",
            "model": "QWEN_MODEL",
            "api_base": "QWEN_API_BASE",
        },
        LLMProvider.ZHIPU: {
            "api_key": "ZHIPU_API_KEY",
            "model": "ZHIPU_MODEL",
            "api_base": "ZHIPU_API_BASE",
        },
        LLMProvider.KIMI: {
            "api_key": "KIMI_API_KEY",
            "model": "KIMI_MODEL",
            "api_base": "KIMI_API_BASE",
        },
        LLMProvider.SPARK: {
            "api_key": "SPARK_API_KEY",
            "api_secret": "SPARK_API_SECRET",
            "app_id": "SPARK_APP_ID",
            "model": "SPARK_MODEL",
        },
        LLMProvider.DEEPSEEK: {
            "api_key": "DEEPSEEK_API_KEY",
            "model": "DEEPSEEK_MODEL",
            "api_base": "DEEPSEEK_API_BASE",
        },
        LLMProvider.STEP: {
            "api_key": "STEP_API_KEY",
            "model": "STEP_MODEL",
            "api_base": "STEP_API_BASE",
        },
        LLMProvider.OPENROUTER: {
            "api_key": "OPENROUTER_API_KEY",
            "model": "OPENROUTER_MODEL",
            "site_url": "OPENROUTER_SITE_URL",
            "site_name": "OPENROUTER_SITE_NAME",
        },
        LLMProvider.XAI: {
            "api_key": "XAI_API_KEY",
            "model": "XAI_MODEL",
            "api_base": "XAI_API_BASE",
        },
    }
    
    @classmethod
    def create(
        cls,
        provider: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseLLMAdapter:
        """
        Create an adapter by provider name.
        
        Args:
            provider: Provider name (openai, qwen, wenxin, etc.)
            api_key: API key (or from env)
            **kwargs: Additional adapter-specific arguments
            
        Returns:
            Configured adapter instance
        """
        # Normalize provider name
        provider_enum = cls._normalize_provider(provider)
        
        if provider_enum not in cls.ADAPTERS:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported: {[p.value for p in cls.ADAPTERS.keys()]}"
            )
        
        adapter_class = cls.ADAPTERS[provider_enum]
        
        # Get API key from env if not provided
        if api_key is None:
            api_key = cls._get_from_env(provider_enum, "api_key")
        
        if not api_key:
            env_var = cls.ENV_MAPPINGS[provider_enum].get("api_key", f"{provider.upper()}_API_KEY")
            raise ValueError(f"API key required. Set {env_var} or pass api_key parameter.")
        
        # Get other config from kwargs or env
        config = cls._get_config_from_env(provider_enum)
        config.update(kwargs)
        
        return adapter_class(api_key=api_key, **config)
    
    @classmethod
    def create_from_env(cls) -> BaseLLMAdapter:
        """
        Create adapter from environment variables.
        
        Uses LLM_PROVIDER env var to determine which adapter to create.
        Defaults to OpenAI if not specified.
        
        Returns:
            Configured adapter instance
        """
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        return cls.create(provider)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return [p.value for p in cls.ADAPTERS.keys()]
    
    @classmethod
    def get_provider_info(cls, provider: str) -> Dict[str, Any]:
        """Get information about a provider."""
        provider_enum = cls._normalize_provider(provider)
        
        if provider_enum not in cls.ADAPTERS:
            raise ValueError(f"Unknown provider: {provider}")
        
        adapter_class = cls.ADAPTERS[provider_enum]
        
        # Get default model
        default_model = adapter_class(None).get_default_model() if hasattr(adapter_class, "MODELS") else "unknown"
        
        return {
            "name": provider_enum.value,
            "env_vars": cls.ENV_MAPPINGS.get(provider_enum, {}),
            "default_model": default_model,
            "supports_tools": True,  # All current adapters support tools
        }
    
    @classmethod
    def _normalize_provider(cls, provider: str) -> LLMProvider:
        """Normalize provider string to enum."""
        provider = provider.lower().strip()
        
        # Aliases
        aliases = {
            "openai": LLMProvider.OPENAI,
            "gpt": LLMProvider.OPENAI,
            "gpt-4": LLMProvider.OPENAI,
            "wenxin": LLMProvider.WENXIN,
            "baidu": LLMProvider.WENXIN,
            "文心一言": LLMProvider.WENXIN,
            "ernie": LLMProvider.WENXIN,
            "qwen": LLMProvider.QWEN,
            "alibaba": LLMProvider.QWEN,
            "dashscope": LLMProvider.QWEN,
            "通义千问": LLMProvider.QWEN,
            "zhipu": LLMProvider.ZHIPU,
            "智谱": LLMProvider.ZHIPU,
            "chatglm": LLMProvider.ZHIPU,
            "glm": LLMProvider.ZHIPU,
            "kimi": LLMProvider.KIMI,
            "moonshot": LLMProvider.KIMI,
            "月之暗面": LLMProvider.KIMI,
            "spark": LLMProvider.SPARK,
            "iflytek": LLMProvider.SPARK,
            "讯飞": LLMProvider.SPARK,
            "星火": LLMProvider.SPARK,
            "deepseek": LLMProvider.DEEPSEEK,
            "深度求索": LLMProvider.DEEPSEEK,
            "step": LLMProvider.STEP,
            "stepfun": LLMProvider.STEP,
            "阶跃": LLMProvider.STEP,
            "阶跃星辰": LLMProvider.STEP,
            "openrouter": LLMProvider.OPENROUTER,
            "xai": LLMProvider.XAI,
            "grok": LLMProvider.XAI,
            "elon": LLMProvider.XAI,
        }
        
        if provider in aliases:
            return aliases[provider]
        
        # Try to match enum value
        try:
            return LLMProvider(provider)
        except ValueError:
            raise ValueError(f"Unknown provider: {provider}")
    
    @classmethod
    def _get_from_env(cls, provider: LLMProvider, key: str) -> Optional[str]:
        """Get a config value from environment."""
        mappings = cls.ENV_MAPPINGS.get(provider, {})
        env_var = mappings.get(key)
        if env_var:
            return os.getenv(env_var)
        return None
    
    @classmethod
    def _get_config_from_env(cls, provider: LLMProvider) -> Dict[str, Any]:
        """Get all config from environment for a provider."""
        config = {}
        mappings = cls.ENV_MAPPINGS.get(provider, {})
        
        for key, env_var in mappings.items():
            if key == "api_key":
                continue  # Handled separately
            value = os.getenv(env_var)
            if value:
                config[key] = value
        
        return config


def create_llm_adapter(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseLLMAdapter:
    """
    Convenience function to create LLM adapter.
    
    Args:
        provider: Provider name (or from LLM_PROVIDER env)
        api_key: API key (or from provider-specific env)
        **kwargs: Additional arguments
        
    Returns:
        LLM adapter instance
        
    Examples:
        # From environment
        adapter = create_llm_adapter()
        
        # Explicit
        adapter = create_llm_adapter("qwen", api_key="your_key")
        
        # With options
        adapter = create_llm_adapter("openai", model="gpt-4", temperature=0.5)
    """
    if provider is None and api_key is None:
        return LLMFactory.create_from_env()
    
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai")
    
    return LLMFactory.create(provider, api_key, **kwargs)
