"""
百度文心一言 Adapter

Adapter for Baidu ERNIE-Bot API.
"""

import json
from typing import Dict, List, Any, Optional
import httpx

from .base import BaseLLMAdapter, LLMResponse, ToolCall, ToolDefinition, LLMProvider


class WenxinAdapter(BaseLLMAdapter):
    """
    Adapter for Baidu Wenxin Yiyan (文心一言).
    
    Docs: https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html
    
    Required env:
    - WENXIN_API_KEY (从百度智能云获取)
    - WENXIN_SECRET_KEY
    """
    
    provider = LLMProvider.WENXIN
    DEFAULT_API_BASE = "https://aip.baidubce.com"
    
    # Model mappings
    MODELS = {
        "ernie-bot-4": "completions_pro",      # ERNIE-Bot 4.0
        "ernie-bot": "completions",             # ERNIE-Bot
        "ernie-bot-turbo": "eb-instant",        # ERNIE-Bot-Turbo
        "ernie-speed": "ernie_speed",           # ERNIE-Speed
        "ernie-lite": "eb-instant",             # ERNIE-Lite
    }
    
    def get_default_model(self) -> str:
        return "ernie-bot-4"
    
    def __init__(
        self,
        api_key: str,
        secret_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ):
        super().__init__(api_key, api_base, **kwargs)
        self.api_base = api_base or self.DEFAULT_API_BASE
        self.secret_key = secret_key or kwargs.get("secret_key")
        self._access_token: Optional[str] = None
        
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            timeout=self.timeout,
        )
    
    async def _get_access_token(self) -> str:
        """Get Baidu access token."""
        if self._access_token:
            return self._access_token
        
        url = f"/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        
        response = await self.client.post(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        self._access_token = data.get("access_token")
        if not self._access_token:
            raise Exception(f"Failed to get access token: {data}")
        
        return self._access_token
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: str = "auto",
    ) -> LLMResponse:
        """Send chat completion request to Wenxin."""
        access_token = await self._get_access_token()
        
        # Map model name to endpoint
        endpoint = self.MODELS.get(self.model, "completions_pro")
        url = f"/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{endpoint}?access_token={access_token}"
        
        # Format messages (Wenxin uses standard OpenAI format)
        payload = {
            "messages": messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            payload["max_output_tokens"] = self.max_tokens
        
        # Tools support (ERNIE-Bot 4.0+)
        if tools:
            payload["functions"] = self.format_tools(tools)
            if tool_choice != "auto":
                payload["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("error_code"):
                raise Exception(f"Wenxin error {data['error_code']}: {data.get('error_msg')}")
            
            return self._parse_response(data)
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"Wenxin HTTP error: {e.response.text}")
        except Exception as e:
            raise Exception(f"Wenxin request failed: {str(e)}")
    
    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse Wenxin response."""
        # Parse function call if present
        tool_calls = []
        function_call = data.get("function_call")
        if function_call:
            try:
                arguments = json.loads(function_call.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {"raw": function_call.get("arguments", "{}")}
            
            tool_calls.append(ToolCall(
                id="call_" + function_call.get("name", "unknown"),
                name=function_call.get("name", ""),
                arguments=arguments,
            ))
        
        # Calculate usage (Wenxin may not provide this)
        usage = data.get("usage", {})
        if not usage:
            content = data.get("result", "")
            usage = {
                "prompt_tokens": len(str(data.get("messages", []))) // 4,
                "completion_tokens": len(content) // 4,
                "total_tokens": (len(str(data.get("messages", []))) + len(content)) // 4,
            }
        
        return LLMResponse(
            content=data.get("result"),
            tool_calls=tool_calls,
            usage=usage,
            model=self.model,
            finish_reason="stop" if not tool_calls else "function_call",
            raw_response=data,
        )
    
    def format_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Format tools for Wenxin."""
        return [tool.to_wenxin_format() for tool in tools]
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
