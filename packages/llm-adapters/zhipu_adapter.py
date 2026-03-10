"""
智谱清言 Adapter

Adapter for Zhipu AI (智谱清言/ChatGLM) API.
"""

import json
from typing import Dict, List, Any, Optional
import httpx

from .base import BaseLLMAdapter, LLMResponse, ToolCall, ToolDefinition, LLMProvider


class ZhipuAdapter(BaseLLMAdapter):
    """
    Adapter for Zhipu AI (智谱清言).
    
    Docs: https://open.bigmodel.cn/dev/api
    
    Required env:
    - ZHIPU_API_KEY (从智谱 AI 开放平台获取)
    """
    
    provider = LLMProvider.ZHIPU
    DEFAULT_API_BASE = "https://open.bigmodel.cn/api/paas/v4"
    
    # Model names
    MODELS = {
        "glm-4": "glm-4",                    # GLM-4 (旗舰版)
        "glm-4-air": "glm-4-air",            # GLM-4-Air
        "glm-4-flash": "glm-4-flash",        # GLM-4-Flash (免费)
        "glm-3-turbo": "glm-3-turbo",        # GLM-3-Turbo
    }
    
    def get_default_model(self) -> str:
        return "glm-4"
    
    def __init__(self, api_key: str, api_base: Optional[str] = None, **kwargs):
        super().__init__(api_key, api_base, **kwargs)
        self.api_base = api_base or self.DEFAULT_API_BASE
        
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": self.api_key,
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
        """Send chat completion request to Zhipu."""
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
            if tool_choice == "auto":
                payload["tool_choice"] = "auto"
            elif tool_choice == "none":
                payload["tool_choice"] = "none"
            else:
                payload["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("error"):
                raise Exception(f"Zhipu error: {data['error']}")
            
            return self._parse_response(data)
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", error_text)
            except:
                error_msg = error_text
            raise Exception(f"Zhipu API error: {error_msg}")
        except Exception as e:
            raise Exception(f"Zhipu request failed: {str(e)}")
    
    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse Zhipu response."""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        # Parse tool calls
        tool_calls = []
        raw_tool_calls = message.get("tool_calls", [])
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            try:
                arguments = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {"raw": func.get("arguments", "{}")}
            
            tool_calls.append(ToolCall(
                id=tc.get("id", f"call_{func.get('name', 'unknown')}"),
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
        """Format tools for Zhipu."""
        return [tool.to_zhipu_format() for tool in tools]
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
