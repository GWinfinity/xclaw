"""
WeCom/WeWork (企业微信) Client

Integration with WeCom for enterprise messaging.
"""

import json
from typing import Optional, Dict, Any, List
import httpx
from xml.etree import ElementTree as ET

from .crypto import WeChatCrypto


class WeWorkClient:
    """
    WeCom (企业微信) Client.
    
    Recommended for business use - official API support.
    
    Docs: https://developer.work.weixin.qq.com/
    """
    
    API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"
    
    def __init__(
        self,
        corp_id: str,
        corp_secret: str,
        agent_id: str,
        token: Optional[str] = None,
        encoding_aes_key: Optional[str] = None,
    ):
        """
        Initialize WeWork client.
        
        Args:
            corp_id: Corp ID from WeCom
            corp_secret: Corp Secret
            agent_id: Agent ID (应用ID)
            token: Verification token
            encoding_aes_key: AES encryption key
        """
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.token = token
        
        self.crypto: Optional[WeChatCrypto] = None
        if token and encoding_aes_key:
            self.crypto = WeChatCrypto(token, encoding_aes_key, corp_id)
        
        self._access_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_access_token(self) -> str:
        """Get access token (cached)."""
        if self._access_token:
            return self._access_token
        
        url = f"{self.API_BASE}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret,
        }
        
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if data.get("errcode") != 0:
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
        """Verify server configuration."""
        if not self.crypto:
            raise ValueError("Crypto not initialized")
        
        if self.crypto.verify_signature(signature, timestamp, nonce):
            return echostr
        raise ValueError("Invalid signature")
    
    async def parse_message(self, xml_data: str) -> Dict[str, str]:
        """Parse incoming WeWork message."""
        root = ET.fromstring(xml_data)
        
        result = {}
        for child in root:
            result[child.tag] = child.text or ""
        
        return result
    
    async def send_text_message(
        self,
        user_id: Optional[str] = None,
        party_id: Optional[str] = None,
        tag_id: Optional[str] = None,
        content: str = "",
    ) -> Dict[str, Any]:
        """
        Send text message to user(s).
        
        Args:
            user_id: User ID(s), comma separated for multiple
            party_id: Department ID(s)
            tag_id: Tag ID(s)
            content: Message content
        """
        token = await self.get_access_token()
        url = f"{self.API_BASE}/message/send?access_token={token}"
        
        data = {
            "agentid": self.agent_id,
            "msgtype": "text",
            "text": {"content": content},
        }
        
        if user_id:
            data["touser"] = user_id
        elif party_id:
            data["toparty"] = party_id
        elif tag_id:
            data["totag"] = tag_id
        else:
            data["touser"] = "@all"
        
        response = await self.client.post(url, json=data)
        return response.json()
    
    async def send_markdown_message(
        self,
        user_id: Optional[str] = None,
        content: str = "",
    ) -> Dict[str, Any]:
        """
        Send markdown message.
        
        Args:
            user_id: User ID
            content: Markdown content
        """
        token = await self.get_access_token()
        url = f"{self.API_BASE}/message/send?access_token={token}"
        
        data = {
            "agentid": self.agent_id,
            "msgtype": "markdown",
            "markdown": {"content": content},
        }
        
        if user_id:
            data["touser"] = user_id
        else:
            data["touser"] = "@all"
        
        response = await self.client.post(url, json=data)
        return response.json()
    
    async def send_card_message(
        self,
        user_id: str,
        title: str,
        description: str,
        url: str,
        btntxt: str = "查看详情",
    ) -> Dict[str, Any]:
        """
        Send text card message.
        
        Args:
            user_id: User ID
            title: Card title
            description: Card description
            url: Click URL
            btntxt: Button text
        """
        token = await self.get_access_token()
        api_url = f"{self.API_BASE}/message/send?access_token={token}"
        
        data = {
            "touser": user_id,
            "agentid": self.agent_id,
            "msgtype": "textcard",
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": btntxt,
            },
        }
        
        response = await self.client.post(api_url, json=data)
        return response.json()
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user info by ID."""
        token = await self.get_access_token()
        url = f"{self.API_BASE}/user/get"
        params = {
            "access_token": token,
            "userid": user_id,
        }
        
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def get_department_list(self, department_id: Optional[str] = None) -> List[Dict]:
        """Get department list."""
        token = await self.get_access_token()
        url = f"{self.API_BASE}/department/list"
        params = {"access_token": token}
        
        if department_id:
            params["id"] = department_id
        
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if data.get("errcode") == 0:
            return data.get("department", [])
        return []
    
    async def upload_temp_media(
        self,
        media_type: str,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Upload temporary media file.
        
        Args:
            media_type: image/voice/video/file
            file_path: Path to file
        """
        token = await self.get_access_token()
        url = f"{self.API_BASE}/media/upload?access_token={token}&type={media_type}"
        
        with open(file_path, "rb") as f:
            files = {"media": (file_path.split("/")[-1], f)}
            response = await self.client.post(url, files=files)
        
        return response.json()
    
    def build_reply_xml(
        self,
        to_user: str,
        from_user: str,
        content: str,
        msg_type: str = "text",
    ) -> str:
        """Build reply XML."""
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
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
