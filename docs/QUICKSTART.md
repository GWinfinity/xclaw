# xClaw 快速入门

## 环境准备

### 1. 获取 Tesla Fleet API 访问权限

1. 访问 [Tesla Developer Portal](https://developer.tesla.com)
2. 注册开发者账号
3. 创建应用，获取 `CLIENT_ID` 和 `CLIENT_SECRET`
4. 配置回调地址 (Redirect URI)
5. 申请所需的 API 权限范围:
   - `vehicle_device_data`: 车辆数据读取
   - `vehicle_cmds`: 车辆控制命令
   - `vehicle_charging_cmds`: 充电控制

### 2. 获取 OpenAI API Key

1. 访问 [OpenAI Platform](https://platform.openai.com)
2. 创建 API Key
3. 确保账户有余额

### 3. 创建 Bot

**Discord Bot:**
1. 访问 [Discord Developer Portal](https://discord.com/developers/applications)
2. 创建新应用
3. 添加 Bot，获取 Bot Token
4. 启用 MESSAGE CONTENT INTENT
5. 生成邀请链接，添加 Bot 到服务器

**Telegram Bot:**
1. 在 Telegram 中搜索 @BotFather
2. 发送 `/newbot` 创建新 Bot
3. 获取 Bot Token
4. (可选) 设置用户名头像

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/xClaw.git
cd xClaw

# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### Docker 安装

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f xclaw-discord
docker-compose logs -f xclaw-telegram
```

## 配置

创建 `.env` 文件:

```bash
cp .env.example .env
```

编辑 `.env`:

```env
# Tesla API
TESLA_CLIENT_ID=your_client_id
TESLA_CLIENT_SECRET=your_client_secret
TESLA_REGION=cn
TESLA_VIN=your_vehicle_vin  # 可选

# OpenAI
OPENAI_API_KEY=sk-...

# Discord (如使用)
DISCORD_BOT_TOKEN=...

# Telegram (如使用)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USERS=12345678,87654321  # 你的 Telegram 用户 ID
```

获取 Telegram 用户 ID:
- 发送消息给 @userinfobot
- 或在 Bot 中运行 `/start` 查看日志

## 运行

### 运行 Discord Bot

```bash
python run.py discord

# 或直接运行
python -m extensions.discord_bot.bot
```

### 运行 Telegram Bot

```bash
python run.py telegram

# 或直接运行
python -m extensions.telegram_bot.bot
```

### 运行示例

```bash
# 基本示例
python run.py example

# 交互模式
python run.py interactive

# 监控模式
python run.py monitor
```

## 使用

### Discord 命令

```
!status          - 查看车辆状态
!lock            - 锁定车辆
!unlock          - 解锁车辆 (需确认)
!climate on/off  - 开启/关闭空调
!climate 22      - 设置温度
!charge status   - 查看充电状态
!charge start    - 开始充电
!charge stop     - 停止充电
!honk            - 鸣笛
!flash           - 闪灯
!sentry on/off   - 哨兵模式
!help            - 帮助
```

### Telegram 命令

```
/status          - 查看车辆状态
/lock            - 锁定车辆
/unlock          - 解锁车辆 (需确认)
/climate on/off  - 开启/关闭空调
/climate 22      - 设置温度
/charge start    - 开始充电
/charge stop     - 停止充电
/honk            - 鸣笛
/flash           - 闪灯
/help            - 帮助
```

### 自然语言示例

直接发送消息，AI 会自动理解并执行:

```
"帮我锁车"
"车里太热了"
"开启空调到24度"
"还剩多少电"
"开始充电"
"鸣笛找车"
"打开后备箱"
```

## 故障排除

### 车辆显示离线

1. 确保车辆有网络连接
2. 车辆可能需要唤醒，Bot 会自动尝试
3. 长时间未使用，车辆会进入睡眠模式

### API 认证失败

1. 检查 `TESLA_CLIENT_ID` 和 `TESLA_CLIENT_SECRET`
2. 确保已完成 OAuth 授权流程
3. 检查 token 是否过期

### OpenAI API 错误

1. 检查 `OPENAI_API_KEY` 是否正确
2. 确保账户有余额
3. 检查 API 调用限制

### Bot 无响应

1. 检查 Bot Token 是否正确
2. 查看日志: `python run.py <command> 2>&1 | tee bot.log`
3. 确保 Bot 已被添加到群组/频道

## 安全建议

1. **不要将 `.env` 文件提交到 Git**
2. **限制 Bot 使用权限**:
   - Discord: 只在信任的频道使用
   - Telegram: 使用 `TELEGRAM_ALLOWED_USERS` 白名单
3. **敏感操作二次确认**: 解锁、远程启动等操作需要确认
4. **定期更换 API Key**

## 下一步

- [查看架构文档](ARCHITECTURE.md)
- [查看 API 文档](https://developer.tesla.cn/docs/fleet-api)
- [贡献代码](../CONTRIBUTING.md)
