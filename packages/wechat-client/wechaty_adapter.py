"""
Wechaty Adapter for Personal WeChat

⚠️  WARNING: Use with caution!
- Personal WeChat automation may violate WeChat ToS
- Risk of account suspension/ban
- Recommended for testing only

This adapter uses Wechaty (Python) to control personal WeChat.
"""

import asyncio
import os
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass

try:
    from wechaty import Wechaty, Contact, Message, Room
    from wechaty_puppet import PuppetOptions, EventReadyPayload
    WECHATY_AVAILABLE = True
except ImportError:
    WECHATY_AVAILABLE = False


@dataclass
class WechatyConfig:
    """Configuration for Wechaty adapter."""
    name: str = "xClaw-Bot"
    puppet: str = "wechaty-puppet-wechat"  # or wechaty-puppet-padlocal
    puppet_options: Optional[Dict] = None


class WechatyAdapter:
    """
    Wechaty adapter for personal WeChat.
    
    ⚠️  IMPORTANT RISK NOTICE:
    - Using automation on personal WeChat may result in account ban
    - WeChat actively detects and blocks automated accounts
    - Use only for testing, not production
    - Consider using WeCom (企业微信) for business use
    
    Installation:
        pip install wechaty wechaty-puppet-wechat
    
    Docs: https://github.com/wechaty/python-wechaty
    """
    
    def __init__(self, config: Optional[WechatyConfig] = None):
        """
        Initialize Wechaty adapter.
        
        Args:
            config: Wechaty configuration
        """
        if not WECHATY_AVAILABLE:
            raise ImportError(
                "Wechaty not installed. Run: pip install wechaty wechaty-puppet-wechat"
            )
        
        self.config = config or WechatyConfig()
        self.bot: Optional[Wechaty] = None
        self._message_handler: Optional[Callable] = None
        self._login_handler: Optional[Callable] = None
        self._ready = False
    
    def on_message(self, handler: Callable[[str, str, Any], Any]):
        """
        Register message handler.
        
        Args:
            handler: Function(msg_text, sender_id, raw_message)
        """
        self._message_handler = handler
    
    def on_login(self, handler: Callable[[str], Any]):
        """
        Register login handler.
        
        Args:
            handler: Function(user_name)
        """
        self._login_handler = handler
    
    async def start(self):
        """Start Wechaty bot."""
        print("🚀 Starting Wechaty bot...")
        print("⚠️  Warning: Scan QR code with CAUTION - personal account risk!")
        
        options = PuppetOptions(
            puppet=self.config.puppet,
            **(self.config.puppet_options or {})
        )
        
        self.bot = Wechaty(options=options)
        
        # Register event handlers
        self.bot.on("scan", self._on_scan)
        self.bot.on("login", self._on_login)
        self.bot.on("message", self._on_message)
        self.bot.on("logout", self._on_logout)
        self.bot.on("error", self._on_error)
        
        await self.bot.start()
    
    async def stop(self):
        """Stop Wechaty bot."""
        if self.bot:
            await self.bot.stop()
            print("🛑 Wechaty bot stopped")
    
    async def send_text(
        self,
        contact_id: Optional[str] = None,
        room_id: Optional[str] = None,
        text: str = "",
    ):
        """
        Send text message.
        
        Args:
            contact_id: User ID for private message
            room_id: Room ID for group message
            text: Message content
        """
        if not self.bot or not self._ready:
            raise RuntimeError("Bot not ready")
        
        if room_id:
            # Send to room
            room = await self.bot.Room.find(room_id)
            if room:
                await room.say(text)
        elif contact_id:
            # Send to contact
            contact = await self.bot.Contact.find(contact_id)
            if contact:
                await contact.say(text)
    
    async def send_mention(
        self,
        room_id: str,
        text: str,
        mention_ids: list,
    ):
        """
        Send mention message in room.
        
        Args:
            room_id: Room ID
            text: Message content
            mention_ids: List of contact IDs to mention
        """
        if not self.bot or not self._ready:
            raise RuntimeError("Bot not ready")
        
        room = await self.bot.Room.find(room_id)
        if room:
            contacts = []
            for contact_id in mention_ids:
                contact = await self.bot.Contact.find(contact_id)
                if contact:
                    contacts.append(contact)
            await room.say(text, contacts)
    
    # ============ Event Handlers ============
    
    async def _on_scan(self, qr_code: str, status: int, data: Optional[str] = None):
        """Handle QR code scan event."""
        import qrcode
        
        print("\n" + "="*50)
        print("📱 Scan QR Code to Login")
        print("="*50)
        
        # Print QR code to console
        qr = qrcode.QRCode()
        qr.add_data(qr_code)
        qr.print_ascii(invert=True)
        
        print(f"\nQR Code URL: {qr_code[:80]}...")
        print("="*50 + "\n")
    
    async def _on_login(self, contact: Contact):
        """Handle login event."""
        print(f"✅ Logged in as: {contact.name}")
        self._ready = True
        
        if self._login_handler:
            await self._login_handler(contact.name)
    
    async def _on_logout(self, contact: Contact):
        """Handle logout event."""
        print(f"👋 Logged out: {contact.name}")
        self._ready = False
    
    async def _on_message(self, msg: Message):
        """Handle incoming message."""
        # Skip self messages
        if msg.is_self():
            return
        
        text = msg.text()
        sender = msg.talker()
        sender_id = sender.contact_id
        sender_name = sender.name
        
        # Get room info if group message
        room = msg.room()
        room_id = room.room_id if room else None
        
        print(f"📩 Message from {sender_name}: {text[:50]}")
        
        if self._message_handler:
            # Build message info
            msg_info = {
                "text": text,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "room_id": room_id,
                "is_group": room is not None,
                "raw_message": msg,
            }
            
            response = await self._message_handler(text, sender_id, msg_info)
            
            # Send response if handler returns text
            if response and isinstance(response, str):
                await msg.say(response)
    
    async def _on_error(self, error: Exception):
        """Handle error event."""
        print(f"❌ Wechaty Error: {error}")
