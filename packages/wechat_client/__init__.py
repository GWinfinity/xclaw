"""
xClaw WeChat Client

WeChat integration for xClaw supporting:
- WeChat Official Account (微信公众号)
- WeCom/WeWork (企业微信)
- Personal WeChat via Wechaty (个人微信)
"""

from .crypto import WeChatCrypto
from .mp import WeChatMPClient
from .wework import WeWorkClient

__version__ = "0.1.0"
__all__ = [
    "WeChatCrypto",
    "WeChatMPClient", 
    "WeWorkClient",
]
