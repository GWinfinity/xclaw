# xClaw 🦞

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
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
- **🔧 Function Calling** — AI agents that actually *do* things, not just chat
- **🧠 Context Memory** — Remembers preferences and conversation context
- **🔒 Safety First** — Confirmation prompts for sensitive operations, full audit logging
- **⚡ Async Architecture** — Built with `asyncio` for high performance

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
│   ├── XClawAgent          # AI agent with function calling
│   ├── TeslaToolSet        # Vehicle control primitives
│   ├── ConversationMemory  # Context persistence
│   └── VehicleContext      # State management
│
├── Adapter Layer
│   ├── llm-adapters/       # 9+ LLM provider adapters
│   │   ├── OpenAI
│   │   ├── xAI (Grok)
│   │   ├── DeepSeek
│   │   └── ...
│   └── platform-clients/   # Messaging platform clients
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
| `lock_doors` / `unlock_doors` | Door control |
| `start_climate` / `stop_climate` | Climate control |
| `set_temperature` | Set target temperature |
| `start_charging` / `stop_charging` | Charging control |
| `set_charge_limit` | Set charge limit (%) |
| `honk_horn` / `flash_lights` | Locate vehicle |
| `set_sentry_mode` | Toggle Sentry Mode |
| `open_frunk` / `open_trunk` | Front/rear trunk |

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
- httpx >= 0.24.0
- pydantic >= 2.0.0
- openai >= 1.0.0 (optional)
- discord.py >= 2.3.0 (for Discord)
- python-telegram-bot >= 20.0 (for Telegram)

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
