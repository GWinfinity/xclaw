"""
WeChat Official Account (微信公众号) Client

Integration with WeChat MP (订阅号/服务号).
"""

import json
from typing import Optional, Dict, Any, List
import httpx
from xml.etree import ElementTree as ET

from .crypto import WeChatCrypto


class WeChatMPClient:
    """
    WeChat Official Account Client.
    
    Supports both subscription and service accounts.
    Service account recommended for better features.
    
    Docs: https://developers.weixin.qq.com/doc/offiaccount/
    """
    
    API_BASE = "https://api.weixin.qq.com/cgi-bin"
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        token: Optional[str] = None,
        encoding_aes_key: Optional[str] = None,
    ):
        """
        Initialize WeChat MP client.
        
        Args:
            app_id: App ID from WeChat MP
            app_secret: App Secret from WeChat MP
            token: Verification token (optional)
            encoding_aes_key: AES encryption key (optional)
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.token = token
        
        self.crypto: Optional[WeChatCrypto] = None
        if token and encoding_aes_key:
            self.crypto = WeChatCrypto(token, encoding_aes_key, app_id)
        
        self._access_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_access_token(self) -> str:
        """Get access token (cached)."""
        if self._access_token:
            return self._access_token
        
        url = f"{self.API_BASE}/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }
        
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if "access_token" not in data:
            raise Exception(f"Failed to get access token: {data}")
        
        self._access_token = data["access_token"]
        return self._access_token
    
    async def verify_server(
        self,
        signature: str,
        timestamp: str,
        nonce: str,
        echostr: str,
    ) -> str:
        """
        Verify server configuration.
        
        Returns echostr if verification passes.
        """
        if not self.crypto:
            raise ValueError("Crypto not initialized, token required")
        
        if self.crypto.verify_signature(signature, timestamp, nonce):
            return echostr
        raise ValueError("Invalid signature")
    
    async def parse_message(self, xml_data: str) -> Dict[str, str]:
        """
        Parse incoming WeChat message.
        
        Args:
            xml_data: XML message from WeChat
            
        Returns:
            Dict with message fields
        """
        root = ET.fromstring(xml_data)
        
        result = {}
        for child in root:
            result[child.tag] = child.text or ""
        
        return result
    
    async def parse_encrypted_message(
        self,
        xml_data: str,
        msg_signature: str,
        timestamp: str,
        nonce: str,
    ) -> Dict[str, str]:
        """
        Parse encrypted WeChat message.
        
        Args:
            xml_data: Encrypted XML
            msg_signature: Message signature
            timestamp: Timestamp
            nonce: Nonce
            
        Returns:
            Dict with message fields
        """
        if not self.crypto:
            raise ValueError("Crypto not initialized")
        
        # Parse XML to get encrypted content
        root = ET.fromstring(xml_data)
        encrypt_node = root.find("Encrypt")
        if encrypt_node is None:
            raise ValueError("No Encrypt node found")
        
        encrypted_msg = encrypt_node.text
        
        # Verify signature
        if not self.crypto.verify_signature(msg_signature, timestamp, nonce, encrypted_msg):
            raise ValueError("Invalid message signature")
        
        # Decrypt
        decrypted, app_id = self.crypto.decrypt(encrypted_msg)
        if app_id != self.app_id:
            raise ValueError("App ID mismatch")
        
        # Parse decrypted XML
        return await self.parse_message(decrypted)
    
    async def send_text_message(
        self,
        user_id: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Send text message to user (24h limit for service accounts).
        
        Args:
            user_id: OpenID of user
            content: Message content
        """
        token = await self.get_access_token()
        url = f"{self.API_BASE}/message/custom/send?access_token={token}"
        
        data = {
            "touser": user_id,
            "msgtype": "text",
            "text": {"content": content},
        }
        
        response = await self.client.post(url, json=data)
        return response.json()
    
    async def send_template_message(
        self,
        user_id: str,
        template_id: str,
        url: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Send template message.
        
        Args:
            user_id: OpenID of user
            template_id: Template ID
            url: Optional URL to open
            data: Template data
        """
        token = await self.get_access_token()
        api_url = f"{self.API_BASE}/message/template/send?access_token={token}"
        
        payload = {
            "touser": user_id,
            "template_id": template_id,
            "data": data or {},
        }
        if url:
            payload["url"] = url
        
        response = await self.client.post(api_url, json=payload)
        return response.json()
    
    def build_reply_xml(
        self,
        to_user: str,
        from_user: str,
        content: str,
        msg_type: str = "text",
    ) -> str:
        """
        Build reply XML message.
        
        Args:
            to_user: User OpenID
            from_user: Official Account ID
            content: Message content
            msg_type: Message type
        """
        import time
        
        timestamp = int(time.time())
        
        if msg_type == "text":
            xml = f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
        else:
            raise ValueError(f"Unsupported message type: {msg_type}")
        
        return xml
    
    def build_encrypted_reply(
        self,
        to_user: str,
        from_user: str,
        content: str,
        msg_type: str = "text",
        timestamp: Optional[str] = None,
        nonce: Optional[str] = None,
    ) -> str:
        """
        Build encrypted reply XML.
        
        Args:
            to_user: User OpenID
            from_user: Official Account ID
            content: Message content
            msg_type: Message type
            timestamp: Optional timestamp
            nonce: Optional nonce
        """
        if not self.crypto:
            raise ValueError("Crypto not initialized")
        
        import time
        import random
        
        timestamp = timestamp or str(int(time.time()))
        nonce = nonce or "".join(random.choices("0123456789", k=10))
        
        # Build plain XML
        plain_xml = self.build_reply_xml(to_user, from_user, content, msg_type)
        
        # Encrypt
        encrypted = self.crypto.encrypt(plain_xml)
        
        # Generate signature
        signature = self.crypto.generate_signature(timestamp, nonce, encrypted)
        
        # Build encrypted XML
        return f"""<xml>
<Encrypt><![CDATA[{encrypted}]]></Encrypt>
<MsgSignature><![CDATA[{signature}]]></MsgSignature>
<TimeStamp>{timestamp}</TimeStamp>
<Nonce><![CDATA[{nonce}]]></Nonce>
</xml>"""
    
    async def get_user_info(self, openid: str) -> Dict[str, Any]:
        """Get user basic info."""
        token = await self.get_access_token()
        url = f"{self.API_BASE}/user/info"
        params = {
            "access_token": token,
            "openid": openid,
            "lang": "zh_CN",
        }
        
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
