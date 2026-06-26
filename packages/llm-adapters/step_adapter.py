"""
StepFun Adapter

Adapter for StepFun (阶跃星辰) API.
"""

import json
from typing import Dict, List, Any, Optional
import httpx

from .base import BaseLLMAdapter, LLMResponse, ToolCall, ToolDefinition, LLMProvider


class StepAdapter(BaseLLMAdapter):
    """
    Adapter for StepFun (阶跃星辰).

    Docs: https://platform.stepfun.com/

    Required env:
    - STEP_API_KEY (从阶跃星辰开放平台获取)
    """

    provider = LLMProvider.STEP
    DEFAULT_API_BASE = "https://api.stepfun.com/v1"

    # Model names
    MODELS = {
        "step-1-8k": "step-1-8k",
        "step-1-32k": "step-1-32k",
        "step-1-128k": "step-1-128k",
        "step-1-256k": "step-1-256k",
        "step-1v": "step-1v",
        "step-2": "step-2",
        "step-2-mini": "step-2-mini",
    }

    def get_default_model(self) -> str:
        return "step-2"

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
        """Send chat completion request to StepFun."""
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
                raise Exception(f"StepFun error: {data['error']}")

            return self._parse_response(data)

        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", error_text)
            except Exception:
                error_msg = error_text
            raise Exception(f"StepFun API error: {error_msg}")
        except Exception as e:
            raise Exception(f"StepFun request failed: {str(e)}")

    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse StepFun response."""
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
        """Format tools for StepFun (OpenAI compatible)."""
        return [tool.to_openai_format() for tool in tools]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
