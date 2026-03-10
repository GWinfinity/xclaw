# xClaw 🦞 - 特斯拉智能助手

一个极简的特斯拉车辆 AI 控制框架，支持自然语言交互和多平台接入。

## 特性

- **自然语言控制** - 用中文与特斯拉对话，无需记忆命令
- **多 LLM 支持** - OpenAI、通义千问、智谱清言、Kimi、DeepSeek 等
- **多平台接入** - 微信、Discord、Telegram 一键接入
- **Tesla Fleet API** - 完整的车辆控制能力
- **AI Agent** - 基于 Function Calling 的智能代理
- **对话记忆** - 记住用户偏好和上下文
- **安全可靠** - 敏感操作二次确认，日志记录

## 快速开始

### 基础用法

```python
from packages.xclaw_core import XClawAgent, VehicleContext

# 创建 Agent
context = VehicleContext()
agent = XClawAgent(context)

# 自然语言控制车辆
response = await agent.process("帮我锁车")
print(response.message)
# 🔒 车辆已锁定
# 📍 当前位置: 北京市朝阳区
# 🔋 电量: 78%

# 复杂指令
response = await agent.process("车里太热了，开启空调到23度")
print(response.message)
# ❄️ 空调已开启
# 🌡️ 温度设置为 23°C
```

### 切换 LLM 提供商

```python
# 使用阿里通义千问
agent = XClawAgent(context, llm_provider="qwen")

# 使用智谱清言 (免费)
agent = XClawAgent(context, llm_provider="zhipu")

# 使用 Kimi
agent = XClawAgent(context, llm_provider="kimi")
```

### 微信接入

```python
from extensions.wechat_bot import WeChatBot

# 创建微信公众号机器人
bot = WeChatBot.create_mp_bot(
    app_id="wx_xxxxxxxx",
    app_secret="xxxxxxxx",
    token="your_token",
)

# 启动服务
await bot.start()
# 📍 Webhook: http://localhost:8080/wechat/callback
```

### Discord 接入

```python
# 设置环境变量
# DISCORD_BOT_TOKEN=your_token

# 运行
python run.py discord
```

### Telegram 接入

```python
# 设置环境变量
# TELEGRAM_BOT_TOKEN=your_token

# 运行
python run.py telegram
```

## 使用示例

### 车辆控制

```python
# 查看状态
await agent.process("查看车辆状态")

# 控制空调
await agent.process("开启空调")
await agent.process("设置温度到22度")
await agent.process("关闭空调")

# 充电管理
await agent.process("开始充电")
await agent.process("设置充电限制到80%")
await agent.process("还剩多少电")

# 安全控制
await agent.process("锁定车辆")
await agent.process("开启哨兵模式")

# 寻车
await agent.process("鸣笛")
await agent.process("闪灯")
```

### 多轮对话

```python
# Agent 会记住上下文
await agent.process("开启空调")  # 空调已开启
await agent.process("温度调高一点")  # 理解为升高温度
await agent.process("关了它")  # 理解为关闭空调
```

## 支持的 LLM 提供商

| 提供商 | 标识 | 推荐模型 | 特点 |
|--------|------|----------|------|
| OpenAI | `openai` | gpt-4o | 功能最强 |
| 阿里通义千问 | `qwen` | qwen-max | 中文能力强 |
| 智谱清言 | `zhipu` | glm-4-flash | **免费** |
| Moonshot Kimi | `kimi` | kimi-latest | 长文本支持 |
| 讯飞星火 | `spark` | spark-4 | 语音优势 |
| DeepSeek | `deepseek` | deepseek-chat | 性价比高 |

## 支持的消息平台

| 平台 | 标识 | 特点 |
|------|------|------|
| 微信公众号 | `mp` | 国内用户首选 |
| 企业微信 | `wework` | 企业用户推荐 |
| Discord | `discord` | 国际社区 |
| Telegram | `telegram` | 隐私安全 |

## 架构

```
xClaw
├── Core (核心层)
│   ├── XClawAgent (AI Agent)
│   ├── TeslaToolSet (Tesla 工具集)
│   ├── ConversationMemory (对话记忆)
│   └── VehicleContext (车辆上下文)
│
├── Adapters (适配器层)
│   ├── llm-adapters (LLM 适配器)
│   │   ├── OpenAI
│   │   ├── Qwen (阿里)
│   │   ├── Zhipu (智谱)
│   │   ├── Kimi
│   │   └── ...
│   └── wechat-client (微信客户端)
│       ├── WeChatMP (公众号)
│       ├── WeWork (企业微信)
│       └── Wechaty (个人微信)
│
├── Extensions (扩展层)
│   ├── discord-bot
│   ├── telegram-bot
│   └── wechat-bot
│
└── Tesla Fleet API (底层)
    ├── Vehicle Control
    ├── Climate Control
    ├── Charging Control
    └── Data Retrieval
```

## API 参考

### XClawAgent

```python
agent = XClawAgent(
    vehicle_context,
    llm_provider="openai",  # 或 qwen/zhipu/kimi 等
    temperature=0.7,
)

# 处理消息
response = await agent.process("帮我锁车")
print(response.message)      # AI 回复
print(response.tool_calls)   # 执行的工具调用

# 获取车辆摘要
summary = await agent.get_vehicle_summary()

# 清理记忆
agent.clear_memory()
```

### VehicleContext

```python
context = VehicleContext(vin="your_vin")

# 获取车辆
vehicle = await context.get_vehicle()

# 获取数据
data = await context.get_vehicle_data()
print(data.charge_state.battery_level)
print(data.climate_state.is_climate_on)
```

### TeslaToolSet

| 工具 | 描述 |
|------|------|
| `get_vehicle_data` | 获取车辆完整数据 |
| `lock_doors` | 锁定车门 |
| `unlock_doors` | 解锁车门 |
| `start_climate` | 开启空调 |
| `stop_climate` | 关闭空调 |
| `set_temperature` | 设置温度 |
| `start_charging` | 开始充电 |
| `stop_charging` | 停止充电 |
| `set_charge_limit` | 设置充电限制 |
| `honk_horn` | 鸣笛 |
| `flash_lights` | 闪灯 |
| `set_sentry_mode` | 设置哨兵模式 |

## 运行示例

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行 Discord Bot
python run.py discord

# 运行 Telegram Bot
python run.py telegram

# 运行微信 Bot
python run.py wechat

# 运行交互模式
python run.py interactive

# 运行车辆监控
python run.py monitor
```

## 配置

### 最小配置

```env
# LLM (必填)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Tesla (必填)
TESLA_CLIENT_ID=...
TESLA_CLIENT_SECRET=...
TESLA_REGION=cn

# 消息平台 (至少选一个)
DISCORD_BOT_TOKEN=...  # Discord
TELEGRAM_BOT_TOKEN=... # Telegram
WECHAT_MP_APP_ID=...   # 微信
```

### 多 LLM 配置示例

```env
# 使用阿里通义千问
LLM_PROVIDER=qwen
QWEN_API_KEY=sk-...
QWEN_MODEL=qwen-max

# 使用智谱清言 (免费)
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=...
ZHIPU_MODEL=glm-4-flash
```

### 微信配置示例

```env
WECHAT_MODE=mp
WECHAT_MP_APP_ID=wx_...
WECHAT_MP_APP_SECRET=...
WECHAT_MP_TOKEN=...
```

## 与 rosclaw 的关系

xClaw 对标 [rosclaw](https://github.com/PlaiPin/rosclaw)，将特斯拉车辆视为"机器人"进行控制：

| 项目 | 控制目标 | 通信协议 | 特点 |
|------|----------|----------|------|
| **rosclaw** | ROS2 机器人 | rosbridge/WebSocket | 机器人控制 |
| **xClaw** | Tesla 车辆 | Tesla Fleet API | 车辆智能控制 |

xClaw 可以作为：
1. **独立车辆助手** - 直接通过自然语言控制特斯拉
2. **多平台机器人** - 接入微信、Discord 等社交平台
3. **智能家居组件** - 与 Home Assistant 等系统集成

## 依赖

- Python >= 3.9
- httpx >= 0.24.0
- pydantic >= 2.0.0
- openai >= 1.0.0 (可选)
- fastapi >= 0.104.0 (微信接入)
- pycryptodome >= 3.19.0 (微信加密)
- discord.py >= 2.3.0 (Discord)
- python-telegram-bot >= 20.0 (Telegram)

## 文档

- [快速入门](docs/QUICKSTART.md)
- [架构文档](docs/ARCHITECTURE.md)
- [LLM 提供商配置](docs/LLM_PROVIDERS.md)
- [微信接入指南](docs/WECHAT_INTEGRATION.md)

## 许可证

Apache 2.0
