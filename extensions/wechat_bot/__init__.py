"""
xClaw WeChat Bot

WeChat integration for xClaw supporting:
- WeChat Official Account (微信公众号)
- WeCom/WeWork (企业微信)
- Personal WeChat via Wechaty

Usage:
    from extensions.wechat_bot import WeChatWebhookServer
    
    server = WeChatWebhookServer()
    await server.start()
"""

from .server import WeChatWebhookServer
from .bot import WeChatBot

__all__ = ["WeChatWebhookServer", "WeChatBot"]
