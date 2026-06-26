"""
阿里通义千问 Adapter

Adapter for Alibaba Qwen (通义千问) API.
"""

import json
from typing import Dict, List, Any, Optional
import httpx

from .base import BaseLLMAdapter, LLMResponse, ToolCall, ToolDefinition, LLMProvider


class QwenAdapter(BaseLLMAdapter):
    """
    Adapter for Alibaba Qwen (通义千问).
    
    Docs: https://help.aliyun.com/document_detail/611472.html
    
    Required env:
    - QWEN_API_KEY (从阿里云 DashScope 获取)
    """
    
    provider = LLMProvider.QWEN
    DEFAULT_API_BASE = "https://dashscope.aliyuncs.com/api/v1"
    
    # Model names
    MODELS = {
        "qwen-max": "qwen-max",              # 通义千问-Max
        "qwen-plus": "qwen-plus",            # 通义千问-Plus
        "qwen-turbo": "qwen-turbo",          # 通义千问-Turbo
        "qwen-72b": "qwen-72b-chat",         # Qwen-72B
        "qwen-14b": "qwen-14b-chat",         # Qwen-14B
        "qwen-7b": "qwen-7b-chat",           # Qwen-7B
    }
    
    def get_default_model(self) -> str:
        return "qwen-max"
    
    def __init__(self, api_key: str, api_base: Optional[str] = None, **kwargs):
        super().__init__(api_key, api_base, **kwargs)
        self.api_base = api_base or self.DEFAULT_API_BASE
        
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
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
        """Send chat completion request to Qwen."""
        # Map model name
        model = self.MODELS.get(self.model, self.model)
        
        payload = {
            "model": model,
            "input": {
                "messages": messages,
            },
            "parameters": {
                "temperature": self.temperature,
                "result_format": "message",
            }
        }
        
        if self.max_tokens:
            payload["parameters"]["max_tokens"] = self.max_tokens
        
        # Tools support (Qwen supports function calling)
        if tools:
            payload["tools"] = self.format_tools(tools)
            if tool_choice == "auto":
                payload["tool_choice"] = "auto"
            elif tool_choice != "none":
                payload["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}
        
        try:
            response = await self.client.post("/services/aigc/text-generation/generation", json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code"):
                raise Exception(f"Qwen error {data['code']}: {data.get('message')}")
            
            return self._parse_response(data)
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", error_text)
            except:
                error_msg = error_text
            raise Exception(f"Qwen API error: {error_msg}")
        except Exception as e:
            raise Exception(f"Qwen request failed: {str(e)}")
    
    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse Qwen response."""
        output = data.get("output", {})
        choice = output.get("choices", [{}])[0]
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
                    id=tc.get("id", f"call_{func.get('name', 'unknown')}"),
                    name=func.get("name", ""),
                    arguments=arguments,
                ))
        
        # Handle function call format (older API version)
        function_call = message.get("function_call")
        if function_call and not tool_calls:
            try:
                arguments = json.loads(function_call.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {"raw": function_call.get("arguments", "{}")}
            
            tool_calls.append(ToolCall(
                id=f"call_{function_call.get('name', 'unknown')}",
                name=function_call.get("name", ""),
                arguments=arguments,
            ))
        
        # Usage info
        usage_data = data.get("usage", {})
        usage = {
            "prompt_tokens": usage_data.get("input_tokens", 0),
            "completion_tokens": usage_data.get("output_tokens", 0),
            "total_tokens": usage_data.get("total_tokens", 0),
        }
        
        return LLMResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            usage=usage,
            model=self.model,
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def format_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Format tools for Qwen."""
        return [tool.to_qwen_format() for tool in tools]
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
