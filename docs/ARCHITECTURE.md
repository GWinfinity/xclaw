# xClaw 架构文档

## 概述

xClaw 是一个对标 [rosclaw](https://github.com/PlaiPin/rosclaw) 的项目，将 Tesla 车辆作为"机器人"通过自然语言进行控制。

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Discord  │  │ Telegram │  │  Slack   │  ...               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
└───────┼─────────────┼─────────────┼────────────────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
              ┌───────▼────────┐
              │  xClaw Gateway │
              │  (AI Agent)    │
              └───────┬────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼─────┐ ┌────▼────┐ ┌──────▼──────┐
│   Tesla     │ │ Memory  │ │   Tools     │
│ Fleet API   │ │ (Redis) │ │  (Function  │
│   Client    │ │         │ │   Calling)  │
└─────────────┘ └─────────┘ └─────────────┘
                      │
              ┌───────▼────────┐
              │ Tesla Vehicle  │
              │   (Robot 🦞)   │
              └────────────────┘
```

## 核心组件

### 1. Tesla Fleet API Client (`packages/tesla-client/`)

与 Tesla Fleet API 通信的 Python 客户端。

**主要功能:**
- OAuth2 认证流程
- 车辆数据获取
- 车辆控制命令
- 错误处理和重试

**关键类:**
- `TeslaFleetClient`: 主客户端类
- `Vehicle`: 车辆实例，提供控制方法
- 数据模型: `VehicleData`, `ChargeState`, `ClimateState`, etc.

### 2. AI Agent Core (`packages/xclaw-core/`)

AI 代理核心，处理自然语言并执行操作。

**主要功能:**
- 自然语言理解 (OpenAI GPT-4)
- Function Calling 工具调用
- 对话记忆管理
- 上下文管理

**关键类:**
- `XClawAgent`: 主代理类
- `TeslaToolSet`: Tesla 工具集
- `ConversationMemory`: 对话记忆
- `VehicleContext`: 车辆上下文

### 3. 消息网关 (`extensions/`)

与消息平台的集成。

**Discord Bot:**
- 命令处理 (`!lock`, `!unlock`, `!climate`, etc.)
- 自然语言处理
- 安全确认机制

**Telegram Bot:**
- 命令处理 (`/lock`, `/unlock`, `/climate`, etc.)
- 内联键盘确认
- 用户白名单

### 4. 工具集 (`tools/`)

额外的实用工具。

- `VehicleMonitor`: 车辆状态监控
- `NotificationHandler`: 事件通知处理

## 数据流

### 命令执行流程

```
1. 用户发送消息
   ↓
2. Bot 接收消息
   ↓
3. AI Agent 解析意图
   - 调用 OpenAI API
   - Function Calling 选择工具
   ↓
4. 执行 Tesla API 调用
   - 获取车辆实例
   - 发送控制命令
   ↓
5. 返回结果给用户
   - 格式化响应
   - 发送消息
```

### 车辆数据获取流程

```
1. 请求车辆数据
   ↓
2. 检查车辆状态
   - 如果 asleep，发送 wake_up
   ↓
3. 调用 /vehicle_data API
   ↓
4. 解析响应数据
   - 转换为 Pydantic 模型
   ↓
5. 返回结构化数据
```

## 安全设计

### 1. 认证安全
- OAuth2 流程，支持 token 刷新
- 环境变量存储敏感信息
- 用户白名单机制

### 2. 操作安全
- 敏感操作二次确认 (解锁、远程启动)
- 命令超时机制
- 操作日志记录

### 3. API 安全
- 速率限制处理
- 错误重试机制
- Token 过期自动刷新

## 扩展性设计

### 添加新的消息平台

1. 在 `extensions/` 创建新的 bot 目录
2. 实现消息接收和发送
3. 集成 `XClawAgent` 处理消息
4. 添加配置文件

### 添加新的 Tesla 工具

1. 在 `TeslaToolSet` 中添加工具方法
2. 定义 OpenAI function schema
3. 实现工具执行逻辑

### 添加 Fleet Telemetry

1. 配置 Tesla Fleet Telemetry
2. 实现 WebSocket 客户端
3. 集成到 `VehicleMonitor`

## 部署架构

### Docker Compose 部署

```yaml
services:
  xclaw-discord:    # Discord Bot
  xclaw-telegram:   # Telegram Bot
  redis:            # 缓存和会话存储
  xclaw-monitor:    # 车辆监控 (可选)
```

### 环境要求

- Python 3.9+
- Redis (可选，用于多实例部署)
- Tesla Developer Account
- OpenAI API Key
- Discord/Telegram Bot Token

## 配置文件

### 环境变量 (.env)

```env
# Tesla API
TESLA_CLIENT_ID=xxx
TESLA_CLIENT_SECRET=xxx
TESLA_REGION=cn

# OpenAI
OPENAI_API_KEY=xxx
OPENAI_MODEL=gpt-4o

# Discord
DISCORD_BOT_TOKEN=xxx

# Telegram
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_ALLOWED_USERS=user1,user2
```

### 日志配置 (config/logging.yaml)

支持 JSON 格式日志，便于日志收集和分析。

## 技术栈

- **Python 3.11**: 主语言
- **OpenAI GPT-4**: 自然语言处理
- **Tesla Fleet API**: 车辆控制
- **Discord.py**: Discord 集成
- **python-telegram-bot**: Telegram 集成
- **Pydantic**: 数据验证
- **HTTPX**: 异步 HTTP 客户端

## 参考

- [Tesla Fleet API 文档](https://developer.tesla.cn/docs/fleet-api/announcements)
- [rosclaw 项目](https://github.com/PlaiPin/rosclaw)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
