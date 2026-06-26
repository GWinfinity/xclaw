# 微信接入指南

xClaw 支持多种微信接入方式：

| 方式 | 难度 | 稳定性 | 风险 | 推荐度 |
|------|------|--------|------|--------|
| **微信公众号** | ⭐⭐ | ⭐⭐⭐⭐ | 🟢 无 | ⭐⭐⭐⭐ |
| **企业微信** | ⭐⭐ | ⭐⭐⭐⭐⭐ | 🟢 无 | ⭐⭐⭐⭐⭐ |
| **个人微信 (Wechaty)** | ⭐⭐⭐ | ⭐⭐ | 🔴 封号风险 | ⭐⭐ |

---

## 方式一：微信公众号 (推荐个人用户)

### 前置条件

- 已认证的微信服务号（订阅号功能受限）
- 服务器（需要公网 IP 和域名）

### 1. 申请微信服务号

1. 访问 [微信公众平台](https://mp.weixin.qq.com)
2. 注册服务号（订阅号无法使用高级接口）
3. 完成微信认证（300元/年）
4. 开启开发者模式

### 2. 配置服务器

1. 登录公众平台 → 开发 → 基本配置
2. 配置服务器 URL：
   - **URL**: `https://your-domain.com/wechat/callback`
   - **Token**: 自定义令牌（任意字符串）
   - **EncodingAESKey**: 点击随机生成
   - **消息加解密方式**: 兼容模式（推荐）

### 3. 获取凭证

在「开发 → 基本配置」中获取：
- **AppID**: 应用 ID
- **AppSecret**: 应用密钥（仅显示一次，请保存）

### 4. 配置 xClaw

```env
WECHAT_MODE=mp
WECHAT_HOST=0.0.0.0
WECHAT_PORT=8080
WECHAT_PATH=/wechat/callback

WECHAT_MP_APP_ID=wx_xxxxxxxxxxxxxxxx
WECHAT_MP_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WECHAT_MP_TOKEN=your_custom_token
WECHAT_MP_ENCODING_AES_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 5. 启动服务

```bash
# 方式1: 直接运行
python -m extensions.wechat_bot.bot

# 方式2: 使用 run.py
python run.py wechat

# 方式3: Docker
docker-compose up -d xclaw-wechat
```

### 6. 验证配置

在微信公众平台点击「提交」验证服务器配置。

---

## 方式二：企业微信 (推荐企业用户)

### 前置条件

- 企业微信认证账号
- 服务器（可选，可主动推送消息）

### 1. 创建企业微信应用

1. 访问 [企业微信管理后台](https://work.weixin.qq.com)
2. 应用管理 → 创建应用
3. 获取 **AgentId** 和 **Secret**

### 2. 配置接收消息

1. 应用详情 → 接收消息 → 设置 API
2. 配置 URL：
   - **URL**: `https://your-domain.com/wechat/callback`
   - **Token**: 自定义令牌
   - **EncodingAESKey**: 随机生成

### 3. 获取凭证

在「我的企业」页面获取：
- **CorpID**: 企业 ID
- 在应用详情页获取 **Secret**

### 4. 配置 xClaw

```env
WECHAT_MODE=wework
WECHAT_HOST=0.0.0.0
WECHAT_PORT=8080
WECHAT_PATH=/wechat/callback

WEWORK_CORP_ID=ww_xxxxxxxxxxxxxxxx
WEWORK_CORP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WEWORK_AGENT_ID=1000002
WEWORK_TOKEN=your_custom_token
WEWORK_ENCODING_AES_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 5. 邀请成员使用

1. 企业微信中添加成员
2. 成员在应用列表中找到机器人
3. 发送消息即可交互

---

## 方式三：个人微信 (⚠️ 有风险)

**警告**: 使用自动化工具控制个人微信可能违反微信服务条款，可能导致账号被限制或封禁。仅供测试使用，**不建议用于生产环境**。

### 使用 Wechaty 接入

Wechaty 是一个开源的微信机器人框架，支持多种 Puppet（协议实现）。

### 1. 安装依赖

```bash
pip install wechaty wechaty-puppet-wechat qrcode
```

### 2. 配置 xClaw

```env
WECHAT_MODE=wechaty
WECHATY_PUPPET=wechaty-puppet-wechat
```

### 3. 启动并扫码登录

```bash
python -m extensions.wechat_bot.bot
```

启动后会显示二维码，使用微信扫码登录。

### 可选：PadLocal 协议（更稳定但收费）

PadLocal 是一个更稳定的微信协议实现，但需要付费。

```bash
pip install wechaty-puppet-padlocal
```

```env
WECHAT_MODE=wechaty
WECHATY_PUPPET=wechaty-puppet-padlocal
WECHATY_PUPPET_PADLOCAL_TOKEN=your_padlocal_token
```

---

## 使用示例

配置完成后，在微信中发送消息：

```
用户: 帮我锁车
Bot: 🔒 正在锁定车辆...
     ✅ 车辆已锁定

用户: 还剩多少电
Bot: 🔋 当前电量: 78%
     预估续航: 412 km

用户: 开启空调24度
Bot: ❄️ 空调已开启
     温度设置为 24°C
```

---

## 常见问题

### Q: 微信公众号回复有延迟？

微信公众号被动回复必须在 5 秒内响应，否则微信会认为失败。如果需要长时间处理：

1. 先回复「处理中...」
2. 使用客服消息接口异步发送结果

### Q: 如何限制特定用户使用？

可以在代码中添加白名单：

```python
ALLOWED_USERS = ["openid_1", "openid_2"]  # 微信用户的 OpenID

async def handle_message(msg_data):
    user_id = msg_data.get("FromUserName")
    if user_id not in ALLOWED_USERS:
        return "⛔ 您没有权限使用此服务"
    # ... 处理消息
```

### Q: 个人微信被封号怎么办？

⚠️ **警告**: 个人微信使用机器人有封号风险！

- 不要使用主号测试
- 控制消息频率
- 建议使用微信公众号或企业微信

### Q: 需要 HTTPS 吗？

是的，微信要求服务器必须使用 HTTPS（443端口）。

可以使用：
- Nginx 反向代理
- Cloudflare
- Let's Encrypt 免费证书

### Q: 如何获取用户的 OpenID？

用户发送消息时，`FromUserName` 字段就是 OpenID。

可以在日志中查看：
```python
print(f"User OpenID: {msg_data.get('FromUserName')}")
```

---

## 部署建议

### 使用 Nginx 反向代理

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /wechat/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker 部署

```yaml
services:
  xclaw-wechat:
    build: .
    environment:
      - WECHAT_MODE=mp
      - WECHAT_MP_APP_ID=${WECHAT_MP_APP_ID}
      - WECHAT_MP_APP_SECRET=${WECHAT_MP_APP_SECRET}
      - WECHAT_MP_TOKEN=${WECHAT_MP_TOKEN}
    ports:
      - "8080:8080"
```

---

## 参考文档

- [微信公众平台开发文档](https://developers.weixin.qq.com/doc/offiaccount/)
- [企业微信开发文档](https://developer.work.weixin.qq.com/)
- [Wechaty 文档](https://wechaty.js.org/docs/)
