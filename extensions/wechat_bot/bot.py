"""
WeChat Bot for xClaw

Unified interface for all WeChat integrations.
"""

import os
import asyncio
from typing import Optional

from packages.wechat_client import WeChatMPClient, WeWorkClient
from packages.wechat_client.wechaty_adapter import WechatyAdapter, WechatyConfig
from packages.xclaw_core import XClawAgent, VehicleContext


class WeChatBot:
    """
    Unified WeChat Bot for xClaw.
    
    Supports:
    1. WeChat Official Account (微信公众号) - Service/Subscription
    2. WeCom/WeWork (企业微信) - Enterprise
    3. Personal WeChat via Wechaty - ⚠️ Risk of ban
    
    Usage:
        bot = WeChatBot.create_from_env()
        await bot.start()
    """
    
    MODE_MP = "mp"           # 微信公众号
    MODE_WECOM = "wework"    # 企业微信
    MODE_WECHATY = "wechaty" # 个人微信 (Wechaty)
    
    def __init__(self, mode: str, agent: XClawAgent, **kwargs):
        """
        Initialize WeChat bot.
        
        Args:
            mode: Bot mode (mp/wework/wechaty)
            agent: xClaw agent
            **kwargs: Mode-specific arguments
        """
        self.mode = mode
        self.agent = agent
        self.client = None
        self.wechaty = None
        self.server = None
        self._kwargs = kwargs
    
    @classmethod
    def create_mp_bot(
        cls,
        app_id: str,
        app_secret: str,
        token: Optional[str] = None,
        encoding_aes_key: Optional[str] = None,
        **agent_kwargs
    ) -> "WeChatBot":
        """
        Create WeChat Official Account bot.
        
        Args:
            app_id: App ID from MP
            app_secret: App Secret
            token: Verification token
            encoding_aes_key: AES key (optional, for encryption)
        """
        context = VehicleContext()
        agent = XClawAgent(vehicle_context=context, **agent_kwargs)
        
        bot = cls(cls.MODE_MP, agent)
        bot.client = WeChatMPClient(
            app_id=app_id,
            app_secret=app_secret,
            token=token,
            encoding_aes_key=encoding_aes_key,
        )
        return bot
    
    @classmethod
    def create_wework_bot(
        cls,
        corp_id: str,
        corp_secret: str,
        agent_id: str,
        token: Optional[str] = None,
        encoding_aes_key: Optional[str] = None,
        **agent_kwargs
    ) -> "WeChatBot":
        """
        Create WeCom/WeWork bot.
        
        Args:
            corp_id: Corp ID
            corp_secret: Corp Secret
            agent_id: Agent ID (应用ID)
            token: Verification token
            encoding_aes_key: AES key
        """
        context = VehicleContext()
        agent = XClawAgent(vehicle_context=context, **agent_kwargs)
        
        bot = cls(cls.MODE_WECOM, agent)
        bot.client = WeWorkClient(
            corp_id=corp_id,
            corp_secret=corp_secret,
            agent_id=agent_id,
            token=token,
            encoding_aes_key=encoding_aes_key,
        )
        return bot
    
    @classmethod
    def create_wechaty_bot(
        cls,
        puppet: str = "wechaty-puppet-wechat",
        **agent_kwargs
    ) -> "WeChatBot":
        """
        Create personal WeChat bot via Wechaty.
        
        ⚠️  WARNING: Risk of account ban!
        
        Args:
            puppet: Puppet type (wechaty-puppet-wechat, wechaty-puppet-padlocal, etc.)
        """
        print("="*60)
        print("⚠️  WARNING: Personal WeChat Bot")
        print("="*60)
        print("Using automation on personal WeChat may result in account ban!")
        print("WeChat actively detects and blocks automated accounts.")
        print("Use only for testing, not production.")
        print("="*60)
        
        context = VehicleContext()
        agent = XClawAgent(vehicle_context=context, **agent_kwargs)
        
        bot = cls(cls.MODE_WECHATY, agent)
        config = WechatyConfig(puppet=puppet)
        bot.wechaty = WechatyAdapter(config)
        
        # Register message handler
        bot.wechaty.on_message(bot._handle_wechaty_message)
        
        return bot
    
    @classmethod
    def create_from_env(cls) -> "WeChatBot":
        """
        Create bot from environment variables.
        
        Environment variables:
        - WECHAT_MODE: mp/wework/wechaty
        
        For MP:
        - WECHAT_MP_APP_ID
        - WECHAT_MP_APP_SECRET
        - WECHAT_MP_TOKEN
        - WECHAT_MP_ENCODING_AES_KEY (optional)
        
        For WeWork:
        - WEWORK_CORP_ID
        - WEWORK_CORP_SECRET
        - WEWORK_AGENT_ID
        - WEWORK_TOKEN
        - WEWORK_ENCODING_AES_KEY (optional)
        
        For Wechaty:
        - WECHATY_PUPPET (default: wechaty-puppet-wechat)
        """
        mode = os.getenv("WECHAT_MODE", "mp").lower()
        
        if mode == cls.MODE_MP:
            return cls.create_mp_bot(
                app_id=os.getenv("WECHAT_MP_APP_ID"),
                app_secret=os.getenv("WECHAT_MP_APP_SECRET"),
                token=os.getenv("WECHAT_MP_TOKEN"),
                encoding_aes_key=os.getenv("WECHAT_MP_ENCODING_AES_KEY"),
            )
        
        elif mode == cls.MODE_WECOM:
            return cls.create_wework_bot(
                corp_id=os.getenv("WEWORK_CORP_ID"),
                corp_secret=os.getenv("WEWORK_CORP_SECRET"),
                agent_id=os.getenv("WEWORK_AGENT_ID"),
                token=os.getenv("WEWORK_TOKEN"),
                encoding_aes_key=os.getenv("WEWORK_ENCODING_AES_KEY"),
            )
        
        elif mode == cls.MODE_WECHATY:
            return cls.create_wechaty_bot(
                puppet=os.getenv("WECHATY_PUPPET", "wechaty-puppet-wechat"),
            )
        
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    async def start(self):
        """Start the bot."""
        if self.mode == self.MODE_WECHATY and self.wechaty:
            await self.wechaty.start()
        else:
            # For MP and WeWork, start webhook server
            from .server import WeChatWebhookServer
            
            mp_client = self.client if self.mode == self.MODE_MP else None
            wework_client = self.client if self.mode == self.MODE_WECOM else None
            
            self.server = WeChatWebhookServer(
                mp_client=mp_client,
                wework_client=wework_client,
                agent=self.agent,
                host=os.getenv("WECHAT_HOST", "0.0.0.0"),
                port=int(os.getenv("WECHAT_PORT", "8080")),
            )
            await self.server.start()
    
    async def stop(self):
        """Stop the bot."""
        if self.wechaty:
            await self.wechaty.stop()
        if self.client:
            await self.client.close()
    
    async def _handle_wechaty_message(
        self,
        text: str,
        sender_id: str,
        msg_info: dict,
    ) -> str:
        """Handle Wechaty message."""
        try:
            response = await self.agent.process(text, user_id=sender_id)
            return response.message
        except Exception as e:
            return f"❌ 处理出错: {str(e)}"


async def main():
    """Main entry point."""
    print("🦞 xClaw WeChat Bot")
    print("="*60)
    
    bot = WeChatBot.create_from_env()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
