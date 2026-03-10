# LLM 提供商配置指南

xClaw 支持多种国内外大模型，你可以根据需要选择最适合的提供商。

## 支持的提供商

| 提供商 | 环境变量 | 推荐模型 | 特点 |
|--------|----------|----------|------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o | 功能最强，需国际支付 |
| 百度文心一言 | `WENXIN_API_KEY` | ernie-bot-4 | 中文理解好 |
| 阿里通义千问 | `QWEN_API_KEY` | qwen-max | 中文能力强，性价比高 |
| 智谱清言 | `ZHIPU_API_KEY` | glm-4 | GLM-4-Flash 免费 |
| Moonshot Kimi | `KIMI_API_KEY` | kimi-latest | 长文本处理强 |
| 讯飞星火 | `SPARK_API_KEY` | spark-4 | 语音交互优势 |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat | 性价比高 |
| OpenRouter | `OPENROUTER_API_KEY` | 多种可选 | 聚合平台，灵活 |

## 快速配置

### 1. 选择提供商

设置 `LLM_PROVIDER` 环境变量：

```bash
# OpenAI
export LLM_PROVIDER=openai

# 阿里通义千问 (推荐国内用户)
export LLM_PROVIDER=qwen

# 智谱清言 (有免费额度)
export LLM_PROVIDER=zhipu

# Kimi
export LLM_PROVIDER=kimi
```

### 2. 获取 API Key

根据选择的提供商，获取对应的 API Key：

#### OpenAI
1. 访问 [platform.openai.com](https://platform.openai.com)
2. 注册账户并绑定支付方式
3. 创建 API Key

#### 阿里通义千问
1. 访问 [dashscope.aliyun.com](https://dashscope.aliyun.com)
2. 阿里云账号登录
3. 创建 API Key

#### 智谱清言
1. 访问 [open.bigmodel.cn](https://open.bigmodel.cn)
2. 注册账号
3. 创建 API Key
4. 新用户有免费额度

#### Moonshot Kimi
1. 访问 [platform.moonshot.cn](https://platform.moonshot.cn)
2. 注册账号
3. 创建 API Key

#### 百度文心一言
1. 访问 [cloud.baidu.com](https://cloud.baidu.com)
2. 进入千帆大模型平台
3. 创建应用获取 API Key 和 Secret Key

#### 讯飞星火
1. 访问 [xinghuo.xfyun.cn](https://xinghuo.xfyun.cn)
2. 注册开发者账号
3. 创建应用获取 AppID, API Key, API Secret

#### DeepSeek
1. 访问 [platform.deepseek.com](https://platform.deepseek.com)
2. 注册账号
3. 充值并创建 API Key

#### OpenRouter
1. 访问 [openrouter.ai](https://openrouter.ai)
2. 注册账号
3. 创建 API Key

### 3. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

根据选择的提供商，配置对应的环境变量。

**示例 - 阿里通义千问：**

```env
LLM_PROVIDER=qwen
QWEN_API_KEY=sk-xxxxxxxxxxxx
QWEN_MODEL=qwen-max
```

**示例 - 智谱清言 (免费版)：**

```env
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=xxxxxxxx.xxxxxxxxx
ZHIPU_MODEL=glm-4-flash
```

**示例 - Kimi：**

```env
LLM_PROVIDER=kimi
KIMI_API_KEY=sk-xxxxxxxxxxxx
KIMI_MODEL=kimi-latest
```

## 各提供商详细配置

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o  # gpt-4o, gpt-4, gpt-3.5-turbo
```

**可选 - 使用代理：**

```env
OPENAI_API_BASE=https://your-proxy.com/v1
```

### 百度文心一言

```env
LLM_PROVIDER=wenxin
WENXIN_API_KEY=...
WENXIN_SECRET_KEY=...
WENXIN_MODEL=ernie-bot-4  # ernie-bot-4, ernie-bot, ernie-bot-turbo
```

### 阿里通义千问

```env
LLM_PROVIDER=qwen
QWEN_API_KEY=sk-...
QWEN_MODEL=qwen-max  # qwen-max, qwen-plus, qwen-turbo, qwen-72b
```

### 智谱清言

```env
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=...
ZHIPU_MODEL=glm-4  # glm-4, glm-4-air, glm-4-flash(免费), glm-3-turbo
```

### Moonshot Kimi

```env
LLM_PROVIDER=kimi
KIMI_API_KEY=sk-...
KIMI_MODEL=kimi-latest  # kimi-latest, kimi-k2, kimi-k2-72b, kimi-k1.5
```

### 讯飞星火

```env
LLM_PROVIDER=spark
SPARK_APP_ID=...
SPARK_API_KEY=...
SPARK_API_SECRET=...
SPARK_MODEL=spark-4  # spark-4, spark-3.5, spark-3.1, spark-3
```

### DeepSeek

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat  # deepseek-chat, deepseek-reasoner
```

### OpenRouter

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4o
OPENROUTER_SITE_URL=https://github.com/yourusername/xClaw
OPENROUTER_SITE_NAME=xClaw
```

**可用模型示例：**
- `openai/gpt-4o` - OpenAI GPT-4o
- `anthropic/claude-3-opus` - Claude 3 Opus
- `google/gemini-pro` - Google Gemini
- `meta-llama/llama-3-70b-instruct` - Llama 3
- `qwen/qwen-72b-chat` - 通义千问

## 模型选择建议

### 追求效果最佳
- **OpenAI GPT-4o** - 功能最强，Function Calling 最稳定
- **Claude 3 Opus** (通过 OpenRouter) - 推理能力强

### 国内用户性价比
- **智谱 GLM-4-Flash** - 免费，效果够用
- **阿里 Qwen-Max** - 中文理解好，价格合理
- **DeepSeek-Chat** - 性价比高

### 长文本处理
- **Kimi** - 支持超长上下文 (200K+)

### 免费使用
- **智谱 GLM-4-Flash** - 免费额度充足
- **讯飞星火** - 有免费试用额度

## 测试配置

运行测试脚本验证配置：

```bash
python -c "
from packages.llm_adapters import LLMFactory
adapter = LLMFactory.create_from_env()
print(f'✅ Successfully created {adapter.provider.value} adapter')
print(f'   Model: {adapter.model}')
"
```

## 故障排除

### API Key 无效

检查对应的环境变量是否正确设置：

```bash
echo $OPENAI_API_KEY
echo $QWEN_API_KEY
```

### 模型不支持 Function Calling

确保选择的模型支持工具调用：

- ✅ OpenAI GPT-4, GPT-3.5
- ✅ 文心一言 ERNIE-Bot 4.0+
- ✅ 通义千问 Qwen-Max, Qwen-Plus
- ✅ 智谱 GLM-4, GLM-3-Turbo
- ✅ Kimi 全系
- ✅ 讯飞星火 4.0+
- ✅ DeepSeek 全系

### 网络连接问题

国内用户可能遇到 OpenAI 连接问题，建议：
1. 使用国内大模型 (Qwen, Zhipu, Kimi)
2. 或配置代理

### 查看日志

启用调试日志查看详细错误：

```env
LOG_LEVEL=DEBUG
```

## 切换提供商

只需修改 `LLM_PROVIDER` 和对应 API Key 即可切换：

```bash
# 从 OpenAI 切换到 Qwen
export LLM_PROVIDER=qwen
export QWEN_API_KEY=your_key
```

无需修改代码，即切即用！
