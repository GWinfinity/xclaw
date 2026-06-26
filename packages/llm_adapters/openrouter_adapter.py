"""
OpenRouter Adapter

Adapter for OpenRouter API - Unified access to many models.
"""

import json
from typing import Dict, List, Any, Optional
import httpx

from .base import BaseLLMAdapter, LLMResponse, ToolCall, ToolDefinition, LLMProvider


class OpenRouterAdapter(BaseLLMAdapter):
    """
    Adapter for OpenRouter.
    
    Provides access to many models including:
    - OpenAI GPT-4/GPT-3.5
    - Anthropic Claude
    - Google Gemini
    - Meta Llama
    - And many more
    
    Docs: https://openrouter.ai/docs
    
    Required env:
    - OPENROUTER_API_KEY (从 OpenRouter 获取)
    """
    
    provider = LLMProvider.OPENROUTER
    DEFAULT_API_BASE = "https://openrouter.ai/api/v1"
    
    # Popular models on OpenRouter
    MODELS = {
        # OpenAI
        "gpt-4o": "openai/gpt-4o",
        "gpt-4": "openai/gpt-4",
        "gpt-4-turbo": "openai/gpt-4-turbo",
        "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
        # Anthropic
        "claude-3-opus": "anthropic/claude-3-opus",
        "claude-3-sonnet": "anthropic/claude-3-sonnet",
        "claude-3-haiku": "anthropic/claude-3-haiku",
        # Google
        "gemini-pro": "google/gemini-pro",
        "gemini-flash": "google/gemini-flash",
        # Meta
        "llama-3-70b": "meta-llama/llama-3-70b-instruct",
        "llama-3-8b": "meta-llama/llama-3-8b-instruct",
        # Mistral
        "mixtral-8x22b": "mistralai/mixtral-8x22b-instruct",
        # Chinese models
        "qwen-72b": "qwen/qwen-72b-chat",
        "deepseek-chat": "deepseek/deepseek-chat",
        "deepseek-coder": "deepseek/deepseek-coder",
    }
    
    def get_default_model(self) -> str:
        return "gpt-4o"
    
    def __init__(self, api_key: str, api_base: Optional[str] = None, **kwargs):
        super().__init__(api_key, api_base, **kwargs)
        self.api_base = api_base or self.DEFAULT_API_BASE
        self.site_url = kwargs.get("site_url", "https://github.com/yourusername/xClaw")
        self.site_name = kwargs.get("site_name", "xClaw")
        
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name,
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: str = "auto",
    ) -> LLMResponse:
        """Send chat completion request to OpenRouter."""
        # Map or use model directly
        model = self.MODELS.get(self.model, self.model)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens
        
        # Tools support
        if tools:
            payload["tools"] = self.format_tools(tools)
            payload["tool_choice"] = tool_choice
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("error"):
                raise Exception(f"OpenRouter error: {data['error']}")
            
            return self._parse_response(data)
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", error_text)
            except:
                error_msg = error_text
            raise Exception(f"OpenRouter API error: {error_msg}")
        except Exception as e:
            raise Exception(f"OpenRouter request failed: {str(e)}")
    
    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse OpenRouter response (OpenAI compatible)."""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        # Parse tool calls
        tool_calls = []
        raw_tool_calls = message.get("tool_calls", [])
        for tc in raw_tool_calls:
            if tc.get("type") == "function":
                func = tc.get("function", {})
                try:
                    arguments = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    arguments = {"raw": func.get("arguments", "{}")}
                
                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=arguments,
                ))
        
        return LLMResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            usage=data.get("usage", {}),
            model=data.get("model", self.model),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def format_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Format tools for OpenRouter (OpenAI compatible)."""
        return [tool.to_openai_format() for tool in tools]
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter."""
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            raise Exception(f"Failed to get models: {str(e)}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
