"""
XClaw AI Agent

Main AI agent that processes natural language and controls Tesla vehicles.
Supports multiple LLM providers through adapters.

Enhanced with Hermes Agent-inspired features:
- Persistent memory with FTS5 search
- Multi-step planning
- Skill auto-learning
- Context compression
- Safety guardrails
- Structured logging
"""

import os
import json
import time
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
from .persistent_memory import PersistentMemory
from .logging import AgentLogger, setup_logging
from .safety import SafetyGuard
from .scheduler import TaskScheduler
from .context_compressor import ContextCompressor
from .planner import Planner
from .skill_learner import SkillLearner


@dataclass
class AgentResponse:
    """Response from the AI agent."""
    message: str
    tool_calls: List[ToolResult]
    context: Optional[Dict[str, Any]] = None
    plan_summary: Optional[str] = None


class XClawAgent:
    """
    xClaw AI Agent for Tesla vehicle control.
    
    Enhanced with Hermes Agent-inspired capabilities:
    - Persistent memory across sessions
    - Multi-step planning for complex requests
    - Automatic skill learning from successful interactions
    - Context compression for long conversations
    - Safety guardrails with rate limiting and audit logging
    - Structured logging for observability
    
    Usage:
        # Auto-detect from environment
        agent = XClawAgent(vehicle)
        
        # Specific provider
        agent = XClawAgent(vehicle, llm_provider="qwen")
        
        # With persistent memory
        agent = XClawAgent(vehicle, enable_persistent_memory=True)
        
        response = await agent.process("帮我锁车")
        print(response.message)
    """
    
    SYSTEM_PROMPT = """你是一个智能特斯拉车辆助手，名为 xClaw 🦞。

你可以帮助用户控制他们的特斯拉车辆，包括：
- 车门控制：锁定/解锁、控制车窗、开启前/后备箱
- 空调控制：开启/关闭空调、设置温度、座椅加热、座椅通风、方向盘加热
- 充电管理：开始/停止充电、设置充电限制、设置充电电流
- 位置服务：获取车辆位置
- 哨兵模式：开启/关闭哨兵模式
- 车辆召唤：鸣笛、闪灯
- 限速模式：设置/取消限速
- 代客模式：开启/关闭代客模式
- 软件更新：调度/取消软件更新
- Homelink：触发车库门开关

车辆平台信息（如可用）将附加在后续 system 消息中，告知你当前车辆的 MCU、HW 及支持的功能。如果某项功能在当前车辆上不可用，请拒绝执行并友好解释。

重要规则：
1. 始终用中文回复用户
2. 回复要简洁友好，使用 emoji 让回复更生动
3. 执行命令前确认车辆状态
4. 如果操作失败，解释可能的原因并提供建议
5. 对于敏感操作（如解锁车辆），提醒用户注意安全
6. 当用户说"车里太热了"或"车里太冷了"时，自动调整空调
7. 充电相关的距离单位使用"公里"
8. 对于复杂的多步骤请求，先制定计划再执行
9. 记住用户的偏好和习惯，提供个性化服务

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
        user_id: str = "default",
        enable_persistent_memory: bool = True,
        enable_safety: bool = True,
        enable_planner: bool = True,
        enable_skill_learning: bool = True,
        db_path: Optional[str] = None,
    ):
        """
        Initialize xClaw AI Agent.
        
        Args:
            vehicle_context: Vehicle context with Tesla client
            llm_adapter: Pre-configured LLM adapter (optional)
            llm_provider: Provider name if creating adapter (openai, qwen, etc.)
            temperature: Model temperature
            user_id: User identifier for memory and safety
            enable_persistent_memory: Enable SQLite persistent memory
            enable_safety: Enable safety guardrails
            enable_planner: Enable multi-step planning
            enable_skill_learning: Enable automatic skill learning
            db_path: Path to SQLite database for persistent memory
        """
        self.vehicle_context = vehicle_context
        self.temperature = temperature
        self.user_id = user_id
        
        # Initialize LLM adapter
        if llm_adapter:
            self.llm = llm_adapter
        else:
            try:
                if llm_provider:
                    self.llm = LLMFactory.create(llm_provider)
                else:
                    self.llm = LLMFactory.create_from_env()
            except Exception as e:
                print(f"⚠️ Failed to create LLM adapter: {e}")
                print("📝 Make sure to set LLM_PROVIDER and corresponding API key environment variables")
                raise
        
        # Core components
        self.tools = TeslaToolSet(vehicle_context)
        self.memory = ConversationMemory()
        
        # Hermes Agent-inspired components
        self.persistent_memory = PersistentMemory(db_path) if enable_persistent_memory else None
        self.logger = AgentLogger()
        self.safety = SafetyGuard(self.persistent_memory) if enable_safety else None
        self.scheduler = TaskScheduler(self.persistent_memory)
        self.compressor = ContextCompressor()
        self.planner = Planner() if enable_planner else None
        self.skill_learner = SkillLearner(self.persistent_memory) if enable_skill_learning else None
        
        # Build tool definitions
        self._tool_definitions = self._build_tool_definitions()
        
        # Session tracking
        self._session_id = f"session_{int(time.time())}"
    
    def _build_tool_definitions(self) -> List[ToolDefinition]:
        """Build tool definitions from TeslaToolSet."""
        tools = []
        openai_functions = self.tools.get_openai_functions()
        
        for func in openai_functions:
            func_data = func.get("function", func)
            tools.append(ToolDefinition(
                name=func_data.get("name", ""),
                description=func_data.get("description", ""),
                parameters=func_data.get("parameters", {}),
            ))
        
        return tools
    
    async def process(
        self,
        user_message: str,
        user_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Process a user message and execute actions.
        
        Enhanced with:
        - Skill matching for known patterns
        - Multi-step planning for complex requests
        - Safety validation for each tool call
        - Persistent memory for context
        - Skill learning from successful interactions
        
        Args:
            user_message: Natural language message from user
            user_id: Optional user identifier (overrides default)
            
        Returns:
            AgentResponse with message and tool call results
        """
        uid = user_id or self.user_id
        start_time = time.time()
        
        self.logger.process_start(uid, user_message)
        
        # Check for matching skills first
        matched_skill = None
        if self.skill_learner:
            matched_skill = self.skill_learner.find_matching_skill(user_message)
        
        # Check if this is a multi-step request
        plan = None
        if self.planner:
            plan = self.planner.analyze_request(user_message)
        
        # Add message to memory
        self.memory.add_user_message(user_message, uid)
        if self.persistent_memory:
            self.persistent_memory.add_message(
                self._session_id, uid, "user", user_message
            )
        
        # Build messages for LLM
        messages = await self._build_messages(uid)
        
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
                    # Safety check
                    if self.safety:
                        allowed, reason, risk = self.safety.validate_command(
                            uid, tool_call.name, tool_call.arguments
                        )
                        if not allowed:
                            tool_results.append(ToolResult(
                                tool_call_id=tool_call.id,
                                success=False,
                                error=f"安全限制: {reason}",
                            ))
                            continue
                    
                    result = await self._execute_tool(
                        tool_call.id, tool_call.name, tool_call.arguments
                    )
                    tool_results.append(result)
                    
                    # Log tool execution
                    self.logger.tool_executed(
                        tool_call.name, result.success, 0
                    )
                
                # Build tool call messages for final response
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
                        "content": json.dumps(result.data, ensure_ascii=False) if result.success else result.error,
                    })
                
                final_response = await self.llm.chat_completion(
                    messages=messages,
                    tools=None,
                )
                
                reply = final_response.content or "操作完成"
            else:
                reply = response.content or ""
            
            # Add assistant response to memory
            self.memory.add_assistant_message(reply, uid)
            if self.persistent_memory:
                self.persistent_memory.add_message(
                    self._session_id, uid, "assistant", reply
                )
            
            # Learn from successful interactions
            if self.skill_learner and tool_results:
                all_success = all(r.success for r in tool_results)
                self.skill_learner.observe_interaction(
                    uid, user_message,
                    [{"name": tc.name, "arguments": tc.arguments} for tc in response.tool_calls],
                    all_success,
                )
            
            # Save vehicle state snapshot
            if self.persistent_memory and tool_results:
                try:
                    data = await self.vehicle_context.get_vehicle_data()
                    self.persistent_memory.save_vehicle_state(
                        data.vin,
                        {
                            "battery_level": data.charge_state.battery_level,
                            "charging_state": data.charge_state.charging_state.value,
                            "inside_temp": data.climate_state.inside_temp,
                            "locked": data.vehicle_state.locked,
                            "sentry_mode": data.vehicle_state.sentry_mode,
                        }
                    )
                except Exception:
                    pass
            
            # Build plan summary if applicable
            plan_summary = None
            if plan:
                self.planner.mark_step_completed(plan, 0, {"reply": reply})
                plan_summary = self.planner.get_plan_summary(plan)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.process_end(uid, duration_ms, len(tool_results))
            
            return AgentResponse(
                message=reply,
                tool_calls=tool_results,
                context={"user_id": uid, "session_id": self._session_id},
                plan_summary=plan_summary,
            )
            
        except Exception as e:
            self.logger.error("process", e)
            error_msg = f"❌ AI 处理出错: {str(e)}"
            return AgentResponse(
                message=error_msg,
                tool_calls=[],
                context={"error": str(e)}
            )
    
    async def _get_platform_context(self) -> str:
        """Get vehicle platform summary for system prompt."""
        try:
            vehicle = await self.vehicle_context.get_vehicle()
            info = await self.tools.execute("get_vehicle_info", {})
            if info.success and info.data:
                data = info.data
                features = data.get("features", {})
                supported = [k for k, v in features.items() if v]
                unsupported = [k for k, v in features.items() if not v]
                context = (
                    f"当前车辆: {data.get('model', '未知')} {data.get('generation', '')}\n"
                    f"MCU: {data.get('mcu', '未知')}, HW: {data.get('hw', '未知')}\n"
                    f"支持的功能: {', '.join(supported)}"
                )
                if unsupported:
                    context += f"\n不支持的功能: {', '.join(unsupported)}"
                return context
        except Exception:
            pass
        return ""

    async def _build_messages(self, user_id: str) -> List[Dict[str, str]]:
        """Build messages for LLM with persistent memory context."""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Add vehicle platform context
        platform_context = await self._get_platform_context()
        if platform_context:
            messages.append({"role": "system", "content": platform_context})
        
        # Add user preferences from persistent memory
        if self.persistent_memory:
            prefs = self.persistent_memory.get_preferences(user_id)
            if prefs:
                pref_text = "用户偏好:\n"
                for key, value in prefs.items():
                    pref_text += f"- {key}: {value}\n"
                messages.append({"role": "system", "content": pref_text})
            
            # Search for relevant memories
            recent_msgs = self.memory.get_messages(user_id, limit=3)
            if recent_msgs:
                search_query = " ".join([m.get("content", "") for m in recent_msgs[-2:]])
                if search_query:
                    memories = self.persistent_memory.search_memories(
                        search_query, user_id, limit=3
                    )
                    if memories:
                        memory_text = "相关记忆:\n"
                        for mem in memories:
                            memory_text += f"- {mem['content']}\n"
                        messages.append({"role": "system", "content": memory_text})
        
        # Add conversation history with compression
        conv_messages = self.memory.get_messages(user_id, limit=20)
        if self.compressor.needs_compression(conv_messages):
            conv_messages = self.compressor.compress(conv_messages)
        
        messages.extend(conv_messages)
        
        return messages
    
    async def _execute_tool(
        self, tool_call_id: str, function_name: str, arguments: Dict
    ) -> ToolResult:
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
    
    async def start_scheduler(self):
        """Start the task scheduler."""
        await self.scheduler.start()
    
    async def stop_scheduler(self):
        """Stop the task scheduler."""
        await self.scheduler.stop()
    
    def get_audit_summary(self, hours: int = 24) -> Dict:
        """Get safety audit summary."""
        if self.safety:
            return self.safety.get_audit_summary(self.user_id, hours)
        return {"error": "Safety guard not enabled"}
    
    def get_memory_stats(self) -> Dict:
        """Get memory statistics."""
        if self.persistent_memory:
            return self.persistent_memory.get_stats()
        return {"error": "Persistent memory not enabled"}
    
    async def close(self):
        """Close agent and cleanup resources."""
        await self.stop_scheduler()
        if self.llm and hasattr(self.llm, 'close'):
            await self.llm.close()
        if self.persistent_memory:
            self.persistent_memory.close()
