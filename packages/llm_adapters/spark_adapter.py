"""
讯飞星火 Adapter

Adapter for iFlytek Spark (讯飞星火) API.
"""

import json
import base64
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, AsyncGenerator
import httpx
import websockets
import asyncio

from .base import BaseLLMAdapter, LLMResponse, ToolCall, ToolDefinition, LLMProvider


class SparkAdapter(BaseLLMAdapter):
    """
    Adapter for iFlytek Spark (讯飞星火).
    
    Docs: https://www.xfyun.cn/doc/spark/Web.html
    
    Required env:
    - SPARK_APP_ID
    - SPARK_API_KEY
    - SPARK_API_SECRET
    """
    
    provider = LLMProvider.SPARK
    
    # WebSocket URLs for different versions
    SPARK_URLS = {
        "4.0": "wss://spark-api.xf-yun.com/v4.0/chat",
        "3.5": "wss://spark-api.xf-yun.com/v3.5/chat",
        "3.1": "wss://spark-api.xf-yun.com/v3.1/chat",
        "3.0": "wss://spark-api.xf-yun.com/v3.0/chat",
        "2.0": "wss://spark-api.xf-yun.com/v2.0/chat",
        "1.5": "wss://spark-api.xf-yun.com/v1.1/chat",
    }
    
    MODEL_MAPPING = {
        "spark-4": "4.0",
        "spark-3.5": "3.5",
        "spark-3.1": "3.1",
        "spark-3": "3.0",
        "spark-2": "2.0",
        "spark-1.5": "1.5",
    }
    
    def get_default_model(self) -> str:
        return "spark-4"
    
    def __init__(
        self,
        api_key: str,
        api_secret: Optional[str] = None,
        app_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Spark adapter.
        
        Args:
            api_key: API Key
            api_secret: API Secret
            app_id: App ID
        """
        super().__init__(api_key, None, **kwargs)
        self.api_secret = api_secret or kwargs.get("api_secret")
        self.app_id = app_id or kwargs.get("app_id")
        
        if not self.api_secret or not self.app_id:
            raise ValueError("SPARK_API_SECRET and SPARK_APP_ID are required")
    
    def _generate_auth_url(self, version: str) -> str:
        """Generate authenticated WebSocket URL."""
        base_url = self.SPARK_URLS.get(version, self.SPARK_URLS["4.0"])
        
        # Parse URL
        url_parts = base_url.replace("wss://", "").split("/")
        host = url_parts[0]
        path = "/" + "/".join(url_parts[1:])
        
        # Generate timestamp
        now = datetime.now(timezone.utc)
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # Generate signature
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode()
        
        # Build authorization
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode()).decode()
        
        # Build final URL
        auth_url = f"{base_url}?authorization={authorization}&date={date.replace(' ', '%20').replace(',', '%2C')}&host={host}"
        
        return auth_url
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: str = "auto",
    ) -> LLMResponse:
        """Send chat completion request via WebSocket."""
        version = self.MODEL_MAPPING.get(self.model, "4.0")
        auth_url = self._generate_auth_url(version)
        
        # Build request payload
        payload = {
            "header": {
                "app_id": self.app_id,
            },
            "parameter": {
                "chat": {
                    "domain": f"generalv{version.replace('.', '')}",
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens or 4096,
                }
            },
            "payload": {
                "message": {
                    "text": messages
                }
            }
        }
        
        # Add tools if provided (Spark 4.0+)
        if tools and version >= "4.0":
            payload["payload"]["functions"] = {
                "text": self.format_tools(tools)
            }
        
        try:
            full_content = ""
            tool_calls = []
            usage = {}
            
            async with websockets.connect(auth_url) as ws:
                await ws.send(json.dumps(payload))
                
                while True:
                    response = await ws.recv()
                    data = json.loads(response)
                    
                    header = data.get("header", {})
                    payload_data = data.get("payload", {})
                    
                    # Check for errors
                    code = header.get("code")
                    if code != 0:
                        raise Exception(f"Spark error {code}: {header.get('message')}")
                    
                    # Extract content
                    choices = payload_data.get("choices", {})
                    text_list = choices.get("text", [])
                    
                    for text_item in text_list:
                        content = text_item.get("content", "")
                        if content:
                            full_content += content
                        
                        # Check for function call
                        function_call = text_item.get("function_call")
                        if function_call:
                            try:
                                arguments = json.loads(function_call.get("arguments", "{}"))
                            except json.JSONDecodeError:
                                arguments = {"raw": function_call.get("arguments", "{}")}
                            
                            tool_calls.append(ToolCall(
                                id=f"call_{function_call.get('name', 'unknown')}",
                                name=function_call.get("name", ""),
                                arguments=arguments,
                            ))
                    
                    # Extract usage
                    usage_data = payload_data.get("usage", {})
                    if usage_data:
                        usage = {
                            "prompt_tokens": usage_data.get("prompt_tokens", 0),
                            "completion_tokens": usage_data.get("completion_tokens", 0),
                            "total_tokens": usage_data.get("total_tokens", 0),
                        }
                    
                    # Check if finished
                    status = header.get("status")
                    if status in [2, 3]:  # Finished or error
                        break
            
            return LLMResponse(
                content=full_content if not tool_calls else None,
                tool_calls=tool_calls,
                usage=usage,
                model=self.model,
                finish_reason="stop" if not tool_calls else "function_call",
            )
            
        except Exception as e:
            raise Exception(f"Spark request failed: {str(e)}")
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion via WebSocket."""
        version = self.MODEL_MAPPING.get(self.model, "4.0")
        auth_url = self._generate_auth_url(version)
        
        payload = {
            "header": {
                "app_id": self.app_id,
            },
            "parameter": {
                "chat": {
                    "domain": f"generalv{version.replace('.', '')}",
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens or 4096,
                }
            },
            "payload": {
                "message": {
                    "text": messages
                }
            }
        }
        
        async with websockets.connect(auth_url) as ws:
            await ws.send(json.dumps(payload))
            
            while True:
                response = await ws.recv()
                data = json.loads(response)
                
                header = data.get("header", {})
                
                if header.get("code") != 0:
                    raise Exception(f"Spark error: {header.get('message')}")
                
                payload_data = data.get("payload", {})
                choices = payload_data.get("choices", {})
                text_list = choices.get("text", [])
                
                for text_item in text_list:
                    content = text_item.get("content", "")
                    if content:
                        yield content
                
                if header.get("status") in [2, 3]:
                    break
    
    def format_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Format tools for Spark."""
        # Spark uses similar format to OpenAI
        formatted = []
        for tool in tools:
            formatted.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            })
        return formatted
