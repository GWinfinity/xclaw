"""
XClaw AI Agent

Main AI agent that processes natural language and controls Tesla vehicles.
Supports multiple LLM providers through adapters.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from packages.llm_adapters import (
    BaseLLMAdapter,
    LLMFactory,
    ToolDefinition,
    LLMResponse,
)

from .tools import TeslaToolSet, ToolResult
from .memory import ConversationMemory
from .context import VehicleContext


@dataclass
class AgentResponse:
    """Response from the AI agent."""
    message: str
    tool_calls: List[ToolResult]
    context: Optional[Dict[str, Any]] = None


class XClawAgent:
    """
    xClaw AI Agent for Tesla vehicle control.
    
    Supports multiple LLM providers (OpenAI, Qwen, Wenxin, Zhipu, Kimi, Spark, DeepSeek, etc.)
    
    Usage:
        # Auto-detect from environment
        agent = XClawAgent(vehicle)
        
        # Specific provider
        agent = XClawAgent(vehicle, llm_provider="qwen")
        
        # With custom adapter
        from packages.llm_adapters import QwenAdapter
        adapter = QwenAdapter(api_key="...")
        agent = XClawAgent(vehicle, llm_adapter=adapter)
        
        response = await agent.process("帮我锁车")
        print(response.message)
    """
    
    SYSTEM_PROMPT = """你是一个智能特斯拉车辆助手，名为 xClaw 🦞。

你可以帮助用户控制他们的特斯拉车辆，包括：
- 车门控制：锁定/解锁、控制车窗、开启前/后备箱
- 空调控制：开启/关闭空调、设置温度、座椅加热
- 充电管理：开始/停止充电、设置充电限制、查看充电状态
- 位置服务：获取车辆位置
- 哨兵模式：开启/关闭哨兵模式
- 车辆召唤：鸣笛、闪灯

重要规则：
1. 始终用中文回复用户
2. 回复要简洁友好，使用 emoji 让回复更生动
3. 执行命令前确认车辆状态
4. 如果操作失败，解释可能的原因并提供建议
5. 对于敏感操作（如解锁车辆），提醒用户注意安全
6. 当用户说"车里太热了"或"车里太冷了"时，自动调整空调
7. 充电相关的距离单位使用"公里"

车辆数据解释：
- 电池电量：百分比，78% 表示还有78%的电量
- 续航里程：车辆还能行驶的公里数
- 充电状态：正在充电、未充电、充电完成等
- 车内温度：摄氏度

时间格式使用 24 小时制。"""

    def __init__(
        self,
        vehicle_context: VehicleContext,
        llm_adapter: Optional[BaseLLMAdapter] = None,
        llm_provider: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """
        Initialize xClaw AI Agent.
        
        Args:
            vehicle_context: Vehicle context with Tesla client
            llm_adapter: Pre-configured LLM adapter (optional)
            llm_provider: Provider name if creating adapter (openai, qwen, etc.)
            temperature: Model temperature
        """
        self.vehicle_context = vehicle_context
        self.temperature = temperature
        
        # Initialize LLM adapter
        if llm_adapter:
            self.llm = llm_adapter
        else:
            # Create from environment or provider
            try:
                if llm_provider:
                    self.llm = LLMFactory.create(llm_provider)
                else:
                    self.llm = LLMFactory.create_from_env()
            except Exception as e:
                print(f"⚠️ Failed to create LLM adapter: {e}")
                print("📝 Make sure to set LLM_PROVIDER and corresponding API key environment variables")
                raise
        
        self.tools = TeslaToolSet(vehicle_context)
        self.memory = ConversationMemory()
        
        # Build tool definitions
        self._tool_definitions = self._build_tool_definitions()
    
    def _build_tool_definitions(self) -> List[ToolDefinition]:
        """Build tool definitions from TeslaToolSet."""
        tools = []
        openai_functions = self.tools.get_openai_functions()
        
        for func in openai_functions:
            func_data = func.get("function", func)  # Handle both formats
            tools.append(ToolDefinition(
                name=func_data.get("name", ""),
                description=func_data.get("description", ""),
                parameters=func_data.get("parameters", {}),
            ))
        
        return tools
    
    async def process(
        self,
        user_message: str,
        user_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Process a user message and execute actions.
        
        Args:
            user_message: Natural language message from user
            user_id: Optional user identifier for memory
            
        Returns:
            AgentResponse with message and tool call results
        """
        # Add message to memory
        self.memory.add_user_message(user_message, user_id)
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.memory.get_messages(user_id, limit=10),
        ]
        
        try:
            # Get completion with function calling
            response = await self.llm.chat_completion(
                messages=messages,
                tools=self._tool_definitions,
                tool_choice="auto",
            )
            
            tool_results = []
            
            # Handle tool calls
            if response.has_tool_calls:
                for tool_call in response.tool_calls:
                    result = await self._execute_tool(tool_call.id, tool_call.name, tool_call.arguments)
                    tool_results.append(result)
                
                # Get final response after tool execution
                messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                            }
                        }
                        for tc in response.tool_calls
                    ]
                })
                
                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result.tool_call_id,
                        "content": json.dumps(result.data, ensure_ascii=False),
                    })
                
                final_response = await self.llm.chat_completion(
                    messages=messages,
                    tools=None,
                )
                
                reply = final_response.content or "操作完成"
            else:
                reply = response.content or ""
            
            # Add assistant response to memory
            self.memory.add_assistant_message(reply, user_id)
            
            return AgentResponse(
                message=reply,
                tool_calls=tool_results,
                context={"user_id": user_id}
            )
            
        except Exception as e:
            error_msg = f"❌ AI 处理出错: {str(e)}"
            return AgentResponse(
                message=error_msg,
                tool_calls=[],
                context={"error": str(e)}
            )
    
    async def _execute_tool(self, tool_call_id: str, function_name: str, arguments: Dict) -> ToolResult:
        """Execute a tool call."""
        result = await self.tools.execute(function_name, arguments)
        result.tool_call_id = tool_call_id
        return result
    
    async def get_vehicle_summary(self) -> str:
        """Get a summary of current vehicle status."""
        try:
            data = await self.vehicle_context.get_vehicle_data()
            
            vs = data.vehicle_state
            cs = data.charge_state
            cls = data.climate_state
            ds = data.drive_state
            
            summary = f"""📊 **{data.display_name}** 车辆状态

🔋 **电池**
• 电量: {cs.battery_level}%
• 续航: {int(cs.battery_range * 1.60934)} km
• 充电状态: {"⚡ 充电中" if cs.charging_state.value == "Charging" else "🔋 " + cs.charging_state.value}

🌡️ **空调**
• 状态: {"❄️ 开启" if cls.is_climate_on else "⭕ 关闭"}
• 温度: {cls.driver_temp_setting}°C
• 车内: {f"{cls.inside_temp:.1f}°C" if cls.inside_temp else "N/A"}

🔒 **安全**
• 车门: {"🔒 已锁定" if vs.locked else "🔓 未锁定"}
• 哨兵: {"👁️ 开启" if vs.sentry_mode else "⭕ 关闭"}

📍 **位置**
• 状态: {data.state}
• 档位: {ds.shift_state.value if ds.shift_state else "P"}
"""
            return summary
            
        except Exception as e:
            return f"❌ 获取车辆状态失败: {str(e)}"
    
    def clear_memory(self, user_id: Optional[str] = None):
        """Clear conversation memory."""
        self.memory.clear(user_id)
    
    async def close(self):
        """Close LLM adapter connection."""
        if hasattr(self.llm, 'close'):
            await self.llm.close()
