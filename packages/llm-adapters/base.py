"""
Base LLM Adapter

Abstract base class for all LLM adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    WENXIN = "wenxin"           # 百度文心一言
    QWEN = "qwen"               # 阿里通义千问
    ZHIPU = "zhipu"             # 智谱清言
    KIMI = "kimi"               # Moonshot Kimi
    SPARK = "spark"             # 讯飞星火
    DEEPSEEK = "deepseek"       # DeepSeek
    OPENROUTER = "openrouter"   # OpenRouter


@dataclass
class ToolCall:
    """Represents a tool call from LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Create from provider-specific dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            arguments=data.get("arguments", {}),
        )


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None
    
    @property
    def has_tool_calls(self) -> bool:
        """Check if response has tool calls."""
        return len(self.tool_calls) > 0


@dataclass
class ToolDefinition:
    """Tool definition for function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }
    
    def to_qwen_format(self) -> Dict[str, Any]:
        """Convert to Qwen format (similar to OpenAI)."""
        return self.to_openai_format()
    
    def to_zhipu_format(self) -> Dict[str, Any]:
        """Convert to Zhipu format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
    
    def to_wenxin_format(self) -> Dict[str, Any]:
        """Convert to Wenxin format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters.get("properties", {}),
                "required": self.parameters.get("required", []),
            }
        }


class BaseLLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.
    
    All adapters must implement:
    - chat_completion: Non-streaming chat
    - chat_completion_stream: Streaming chat (optional)
    - format_tools: Format tools for provider
    """
    
    provider: LLMProvider
    
    def __init__(
        self,
        api_key: str,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 60.0,
        **kwargs
    ):
        """
        Initialize adapter.
        
        Args:
            api_key: API key for the provider
            api_base: Custom API base URL (optional)
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model or self.get_default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra_kwargs = kwargs
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get default model name for this provider."""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: str = "auto",
    ) -> LLMResponse:
        """
        Send chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions
            tool_choice: Tool choice strategy
            
        Returns:
            Standardized LLMResponse
        """
        pass
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion.
        
        Args:
            messages: List of message dicts
            tools: Optional list of tool definitions
            
        Yields:
            Content chunks as strings
        """
        # Default implementation: non-streaming
        response = await self.chat_completion(messages, tools)
        if response.content:
            yield response.content
    
    @abstractmethod
    def format_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Format tools for this provider's API."""
        pass
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Format messages for this provider.
        
        Override if provider requires special formatting.
        """
        return messages
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count.
        
        Default implementation: ~4 characters per token.
        Override for more accurate counting.
        """
        return len(text) // 4
    
    def handle_error(self, error: Exception) -> str:
        """Convert exception to user-friendly error message."""
        error_type = type(error).__name__
        return f"LLM API Error ({error_type}): {str(error)}"
