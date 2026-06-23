# xClaw 🦞

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Tesla](https://img.shields.io/badge/Tesla-Fleet%20API-red)](https://developer.tesla.com/)

**Natural Language Control for Tesla Vehicles**

xClaw is a lightweight, extensible AI framework that lets you control your Tesla using natural language. Built on the Tesla Fleet API with multi-platform integrations and support for 9+ LLM providers.

[Features](#features) • [Quick Start](#quick-start) • [Installation](#installation) • [Documentation](#documentation) • [Examples](#examples)

---

## Features

- **🗣️ Natural Language Control** — Talk to your Tesla like a human. No command memorization needed.
- **🧠 Multi-LLM Support** — OpenAI, xAI (Grok), Anthropic, DeepSeek, Qwen, Kimi, and more
- **💬 Multi-Platform** — Discord, Telegram, WeChat, Slack integrations
- **🔧 Function Calling** — AI agents that actually *do* things, not just chat (28+ vehicle tools)
- **🧠 Persistent Memory** — SQLite + FTS5 full-text search, remembers across sessions
- **📋 Multi-Step Planning** — Decomposes complex requests into ordered execution plans
- **🎯 Skill Auto-Learning** — Learns reusable skills from successful interactions
- **🗜️ Context Compression** — Summarizes old conversations to stay within token limits
- **🔒 Safety Guardrails** — Rate limiting, command validation, audit logging
- **⏰ Scheduled Tasks** — Pre-heat climate, schedule charging, periodic checks
- **📊 Structured Logging** — Full observability with structlog
- **⚡ Async Architecture** — Built with `asyncio` for high performance

## Supported Tesla Vehicles

xClaw supports all Tesla Model 3 and Model Y vehicles, including the latest refreshed versions:

| 车型 | 年款 | 代号 | MCU | 自动驾驶硬件 | VIN 前缀 |
|------|------|------|-----|-------------|----------|
| Model 3 旧款 | 2017-2023 | - | MCU2 (Intel Atom) | HW3.0/HW2.5 | `5YJ3E` |
| **Model 3 焕新版** | 2023 Q4+ | **Highland** | **MCU3 (AMD Ryzen)** | **HW4.0** | `LRW3E` |
| Model Y 旧款 | 2020-2024 | - | MCU2 (Intel Atom) | HW3.0 | `5YJY` |
| **Model Y 焕新版** | 2025 Q1+ | **Juniper** | **MCU3 (AMD Ryzen)** | **HW4.0** | `LRWY` |

### 功能兼容性

| 功能 | 旧款 (MCU2) | 焕新版 (MCU3) |
|------|------------|--------------|
| 基础控制 (锁车/解锁/鸣笛/闪灯) | ✅ | ✅ |
| 空调控制 | ✅ | ✅ |
| 充电控制 | ✅ | ✅ |
| 座椅加热 | ✅ | ✅ |
| **座椅通风** | ❌ | ✅ |
| 方向盘加热 | ✅ | ✅ |
| **生物武器防御模式** | ❌ | ✅ |
| 宠物/露营模式 | ✅ | ✅ |
| 新调度命令 | 需固件 2024.26+ | ✅ |
| 导航命令 | ✅ | ✅ |
| 媒体控制 | ✅ | ✅ |

### 硬件检测

xClaw 会自动检测车辆硬件版本，并根据车型启用/禁用特定功能：

```python
# 获取车辆硬件信息
info = await agent.process("查看我的车辆硬件信息")
# 输出:
# 🚗 Model 3 焕新版 (Highland)
# 🔧 硬件: MCU3 (AMD Ryzen) / HW4.0
# ✅ 支持: 座椅通风、生物武器防御模式、新调度命令

# 自动兼容性检查
await agent.process("开启座椅通风")
# MCU3: ✅ 执行成功
# MCU2: ❌ "座椅通风仅支持焕新版车型"
```

## Quick Start

### Basic Usage

```python
import asyncio
from packages.xclaw_core import XClawAgent, VehicleContext

async def main():
    # Initialize context and agent
    context = VehicleContext()
    agent = XClawAgent(context)
    
    # Control with natural language
    response = await agent.process("Lock my car and check battery")
    print(response.message)
    # 🔒 Vehicle locked
    # 📍 Location: San Francisco, CA
    # 🔋 Battery: 78%

    # Complex commands
    response = await agent.process("It's hot inside, set AC to 72°F")
    print(response.message)
    # ❄️ Climate control activated
    # 🌡️ Temperature set to 72°F

    # Multi-step planning
    response = await agent.process("明天早上8点出门前，把车预热到24度，充到80%")
    print(response.message)
    # 📋 已创建执行计划:
    # ⏳ 定时空调: 7:45 AM, 24°C
    # ⏳ 定时充电: 充至80%

    # Close agent (cleans up resources)
    await agent.close()

asyncio.run(main())
```

### Advanced Usage with Persistent Memory

```python
import asyncio
from packages.xclaw_core import XClawAgent, VehicleContext

async def main():
    context = VehicleContext()
    
    # Agent with all features enabled
    agent = XClawAgent(
        context,
        user_id="user_123",
        enable_persistent_memory=True,  # SQLite + FTS5
        enable_safety=True,             # Rate limiting + audit
        enable_planner=True,            # Multi-step planning
        enable_skill_learning=True,     # Auto-learn skills
    )
    
    # Start scheduled task scheduler
    await agent.start_scheduler()
    
    # Schedule a task
    agent.scheduler.schedule_climate(
        user_id="user_123",
        time_str="2024-01-15T07:45:00",
        temperature=24.0,
        name="早起预热"
    )
    
    # Process requests (memory persists across sessions)
    response = await agent.process("我习惯车内温度22度")
    # Agent learns this preference for future interactions
    
    response = await agent.process("车里太热了")
    # Agent remembers preference and sets to 22°C
    
    # Get audit summary
    summary = agent.get_audit_summary(hours=24)
    print(f"过去24小时执行了 {summary['total_commands']} 个命令")
    
    # Get memory stats
    stats = agent.get_memory_stats()
    print(f"记忆: {stats}")
    
    await agent.close()

asyncio.run(main())
```

### Switch LLM Providers

```python
# OpenAI (default)
agent = XClawAgent(context, llm_provider="openai")

# xAI Grok
agent = XClawAgent(context, llm_provider="xai")

# DeepSeek (cost-effective)
agent = XClawAgent(context, llm_provider="deepseek")

# Local via OpenRouter
agent = XClawAgent(context, llm_provider="openrouter")
```

### Discord Bot

```bash
export DISCORD_BOT_TOKEN="your_token"
python run.py discord
```

### Telegram Bot

```bash
export TELEGRAM_BOT_TOKEN="your_token"
python run.py telegram
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/xClaw.git
cd xClaw

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Minimum Configuration

```bash
# Required: LLM provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Required: Tesla API
TESLA_CLIENT_ID=...
TESLA_CLIENT_SECRET=...
TESLA_REGION=na  # na, eu, or cn

# Optional: Messaging platform
DISCORD_BOT_TOKEN=...
TELEGRAM_BOT_TOKEN=...
```

## Supported LLM Providers

| Provider | ID | Recommended Model | Notes |
|----------|-----|-------------------|-------|
| **OpenAI** | `openai` | `gpt-4o` | Best overall capabilities |
| **xAI** | `xai` | `grok-3` | Fast reasoning, real-time data |
| **DeepSeek** | `deepseek` | `deepseek-chat` | Cost-effective, strong reasoning |
| **Anthropic** | `anthropic` | `claude-3-opus` | Excellent for complex tasks |
| **Moonshot Kimi** | `kimi` | `kimi-latest` | Long context window |
| **Alibaba Qwen** | `qwen` | `qwen-max` | Strong multilingual support |
| **Zhipu AI** | `zhipu` | `glm-4` | Open source friendly |
| **OpenRouter** | `openrouter` | Various | Access 100+ models |

## Supported Platforms

| Platform | ID | Best For |
|----------|-----|----------|
| **Discord** | `discord` | Communities, team coordination |
| **Telegram** | `telegram` | Privacy-focused users |
| **WeChat** | `wechat` | Chinese market |
| **Slack** | `slack` | Enterprise teams |

## Architecture

```
xClaw
├── Core Layer
│   ├── XClawAgent              # AI agent with function calling
│   ├── TeslaToolSet            # 28+ vehicle control tools
│   ├── ConversationMemory      # In-memory context
│   ├── PersistentMemory        # SQLite + FTS5 persistent memory
│   ├── VehicleContext          # State management
│   ├── Planner                 # Multi-step planning engine
│   ├── SkillLearner            # Auto-learn from interactions
│   ├── ContextCompressor       # Token-aware compression
│   ├── TaskScheduler           # Cron-like scheduled tasks
│   ├── SafetyGuard             # Rate limiting & audit
│   └── StructuredLogger        # Observability with structlog
│
├── Adapter Layer
│   ├── llm-adapters/           # 9+ LLM provider adapters
│   │   ├── OpenAI
│   │   ├── xAI (Grok)
│   │   ├── DeepSeek
│   │   └── ...
│   └── platform-clients/       # Messaging platform clients
│       ├── Discord
│       ├── Telegram
│       └── WeChat
│
└── Tesla Fleet API
    ├── Vehicle Control
    ├── Climate Control
    ├── Charging Control
    └── Telemetry
```

## API Reference

### XClawAgent

```python
from packages.xclaw_core import XClawAgent

agent = XClawAgent(
    vehicle_context,
    llm_provider="openai",
    temperature=0.7,
)

# Process natural language command
response = await agent.process("Start charging to 80%")
print(response.message)
print(response.tool_calls)  # Tools that were invoked

# Get vehicle summary
summary = await agent.get_vehicle_summary()

# Clear conversation memory
agent.clear_memory()
```

### VehicleContext

```python
from packages.xclaw_core import VehicleContext

context = VehicleContext(vin="YOUR_VIN")

# Get vehicle instance
vehicle = await context.get_vehicle()

# Fetch current data
data = await context.get_vehicle_data()
print(data.charge_state.battery_level)
print(data.climate_state.inside_temp)
```

### TeslaToolSet

| Tool | Description |
|------|-------------|
| `get_vehicle_data` | Retrieve complete vehicle state |
| `get_location` | Get vehicle GPS location |
| `lock_doors` / `unlock_doors` | Door control |
| `start_climate` / `stop_climate` | Climate control |
| `set_temperature` | Set target temperature |
| `set_seat_heater` | Set seat heating level (0-3) |
| `set_steering_wheel_heater` | Toggle steering wheel heater |
| `start_charging` / `stop_charging` | Charging control |
| `set_charge_limit` | Set charge limit (%) |
| `set_charging_amps` | Set charging amperage |
| `honk_horn` / `flash_lights` | Locate vehicle |
| `set_sentry_mode` | Toggle Sentry Mode |
| `open_frunk` / `open_trunk` | Front/rear trunk |
| `vent_windows` / `close_windows` | Window control |
| `set_speed_limit` | Set vehicle speed limit |
| `set_valet_mode` | Toggle valet mode |
| `trigger_homelink` | Trigger garage door opener |
| `schedule_software_update` | Schedule OTA update |
| `cancel_software_update` | Cancel scheduled update |

## Examples

### Vehicle Control

```python
# Status check
await agent.process("What's my battery level?")

# Climate control
await agent.process("Turn on climate")
await agent.process("Set temperature to 68°F")
await agent.process("Turn off AC")

# Charging
await agent.process("Start charging")
await agent.process("Set charge limit to 80%")
await agent.process("How long until fully charged?")

# Security
await agent.process("Lock the car")
await agent.process("Enable Sentry Mode")

# Locate
await agent.process("Honk the horn")
await agent.process("Flash the lights")
```

### Multi-Turn Conversations

```python
# Context is preserved across calls
await agent.process("Turn on the heater")      # AC activated
await agent.process("Make it warmer")           # Temperature increased
await agent.process("Turn it off")              # AC deactivated
```

## Running Examples

```bash
# Interactive mode
python run.py interactive

# Vehicle monitoring daemon
python run.py monitor

# Platform bots
python run.py discord
python run.py telegram
python run.py wechat
```

## Configuration Reference

### Environment Variables

```bash
# LLM Configuration
LLM_PROVIDER=openai              # Provider identifier
OPENAI_API_KEY=sk-...            # API key
OPENAI_MODEL=gpt-4o              # Model name

# xAI Configuration
XAI_API_KEY=xai-...              # xAI API key
XAI_MODEL=grok-3                 # grok-3, grok-3-fast, grok-3-mini

# Tesla Configuration
TESLA_CLIENT_ID=...              # From developer.tesla.com
TESLA_CLIENT_SECRET=...          # From developer.tesla.com
TESLA_REGION=na                  # na, eu, or cn
TESLA_VIN=...                    # Optional: default vehicle

# Discord Configuration
DISCORD_BOT_TOKEN=...            # From discord.com/developers
DISCORD_GUILD_ID=...             # Optional: for debugging
DISCORD_CHANNEL_ID=...           # Optional: restrict channel

# Telegram Configuration
TELEGRAM_BOT_TOKEN=...           # From @BotFather
TELEGRAM_ALLOWED_USERS=...       # Comma-separated user IDs

# Security Settings
COMMAND_CONFIRMATION_TIMEOUT=30  # Seconds to confirm sensitive ops
ENABLE_CONFIRMATION_FOR_UNLOCK=true
ENABLE_CONFIRMATION_FOR_REMOTE_START=true
```

## Comparison with rosclaw

xClaw draws inspiration from [rosclaw](https://github.com/PlaiPin/rosclaw), applying similar patterns to Tesla vehicles:

| Project | Target | Protocol | Use Case |
|---------|--------|----------|----------|
| **rosclaw** | ROS2 Robots | rosbridge/WebSocket | Robotics research |
| **xClaw** | Tesla Vehicles | Tesla Fleet API | Consumer/prosumer vehicle automation |

xClaw can operate as:
1. **Standalone Assistant** — Direct natural language control
2. **Multi-Platform Bot** — Integrate with Discord, Telegram, etc.
3. **Home Automation Component** — Works with Home Assistant, Node-RED

## Requirements

- Python >= 3.9
- httpx >= 0.28.0
- pydantic >= 2.13.0
- openai >= 2.40.0 (optional)
- discord.py >= 2.7.0 (for Discord)
- python-telegram-bot >= 22.0 (for Telegram)

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [LLM Provider Setup](docs/LLM_PROVIDERS.md)
- [Platform Integration](docs/PLATFORM_INTEGRATION.md)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/yourusername/xClaw.git
cd xClaw
pip install -r requirements-dev.txt
pre-commit install
```

## License

Apache 2.0 — See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with 🦞 by the xClaw team. Not affiliated with Tesla, Inc.</sub>
</p>
