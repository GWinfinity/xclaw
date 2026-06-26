"""
WeChat Webhook Server

FastAPI server to handle WeChat callbacks.
Supports both WeChat MP and WeCom.
"""

import os
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn

from packages.wechat_client import WeChatMPClient, WeWorkClient
from packages.xclaw_core import XClawAgent, VehicleContext


class WeChatWebhookServer:
    """
    FastAPI server for WeChat webhooks.
    
    Handles:
    - Server verification (GET)
    - Message callbacks (POST)
    
    Usage:
        server = WeChatWebhookServer()
        await server.start()
    """
    
    def __init__(
        self,
        mp_client: Optional[WeChatMPClient] = None,
        wework_client: Optional[WeWorkClient] = None,
        agent: Optional[XClawAgent] = None,
        host: str = "0.0.0.0",
        port: int = 8080,
        path: str = "/wechat/callback",
    ):
        """
        Initialize webhook server.
        
        Args:
            mp_client: WeChat MP client (for Official Account)
            wework_client: WeWork client (for Enterprise)
            agent: xClaw agent for processing messages
            host: Server host
            port: Server port
            path: Webhook path
        """
        self.mp_client = mp_client
        self.wework_client = wework_client
        self.agent = agent
        self.host = host
        self.port = port
        self.path = path
        
        self.app = FastAPI(title="xClaw WeChat Server")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get(self.path)
        async def verify_server(
            signature: str,
            timestamp: str,
            nonce: str,
            echostr: str,
        ):
            """Verify server configuration (GET request from WeChat)."""
            try:
                if self.mp_client and self.mp_client.crypto:
                    result = await self.mp_client.verify_server(
                        signature, timestamp, nonce, echostr
                    )
                    return PlainTextResponse(content=result)
                elif self.wework_client and self.wework_client.crypto:
                    result = await self.wework_client.verify_server(
                        signature, timestamp, nonce, echostr
                    )
                    return PlainTextResponse(content=result)
                else:
                    raise HTTPException(400, "No client configured")
            except Exception as e:
                raise HTTPException(400, str(e))
        
        @self.app.post(self.path)
        async def handle_message(
            request: Request,
            msg_signature: Optional[str] = None,
            timestamp: Optional[str] = None,
            nonce: Optional[str] = None,
        ):
            """Handle incoming WeChat message (POST request)."""
            try:
                xml_body = await request.body()
                xml_str = xml_body.decode('utf-8')
                
                # Parse message
                if self.mp_client:
                    if msg_signature and self.mp_client.crypto:
                        # Encrypted message
                        msg_data = await self.mp_client.parse_encrypted_message(
                            xml_str, msg_signature, timestamp, nonce
                        )
                    else:
                        # Plain message
                        msg_data = await self.mp_client.parse_message(xml_str)
                    
                    return await self._handle_mp_message(msg_data)
                
                elif self.wework_client:
                    msg_data = await self.wework_client.parse_message(xml_str)
                    return await self._handle_wework_message(msg_data)
                
                else:
                    raise HTTPException(400, "No client configured")
                    
            except Exception as e:
                print(f"Error handling message: {e}")
                # Return empty success to prevent WeChat retry
                return PlainTextResponse(content="success")
    
    async def _handle_mp_message(self, msg_data: Dict[str, str]) -> Response:
        """Handle WeChat MP message."""
        msg_type = msg_data.get("MsgType", "").lower()
        from_user = msg_data.get("FromUserName", "")
        to_user = msg_data.get("ToUserName", "")
        content = msg_data.get("Content", "")
        
        print(f"📩 WeChat MP [{msg_type}]: {content[:50]}")
        
        # Process with agent
        reply_content = "success"
        
        if msg_type == "text" and self.agent:
            try:
                response = await self.agent.process(content, user_id=from_user)
                reply_content = response.message
            except Exception as e:
                reply_content = f"❌ 处理出错: {str(e)}"
        
        # Build reply
        if reply_content and reply_content != "success":
            if self.mp_client.crypto:
                # Encrypted reply
                reply_xml = self.mp_client.build_encrypted_reply(
                    to_user=from_user,
                    from_user=to_user,
                    content=reply_content,
                )
            else:
                # Plain reply
                reply_xml = self.mp_client.build_reply_xml(
                    to_user=from_user,
                    from_user=to_user,
                    content=reply_content,
                )
            return PlainTextResponse(content=reply_xml, media_type="application/xml")
        
        return PlainTextResponse(content="success")
    
    async def _handle_wework_message(self, msg_data: Dict[str, str]) -> Response:
        """Handle WeWork message."""
        msg_type = msg_data.get("MsgType", "").lower()
        from_user = msg_data.get("FromUserName", "")
        to_user = msg_data.get("ToUserName", "")
        content = msg_data.get("Content", "")
        
        print(f"📩 WeWork [{msg_type}]: {content[:50]}")
        
        # Process with agent
        reply_content = "success"
        
        if msg_type == "text" and self.agent:
            try:
                response = await self.agent.process(content, user_id=from_user)
                reply_content = response.message
            except Exception as e:
                reply_content = f"❌ 处理出错: {str(e)}"
        
        # Build reply
        if reply_content and reply_content != "success":
            reply_xml = self.wework_client.build_reply_xml(
                to_user=from_user,
                from_user=to_user,
                content=reply_content,
            )
            return PlainTextResponse(content=reply_xml, media_type="application/xml")
        
        return PlainTextResponse(content="success")
    
    async def start(self):
        """Start the server."""
        print(f"🚀 Starting WeChat Webhook Server on {self.host}:{self.port}")
        print(f"📍 Webhook URL: http://{self.host}:{self.port}{self.path}")
        
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()


# Convenience function for quick start
def create_wechat_server_from_env() -> WeChatWebhookServer:
    """
    Create WeChat server from environment variables.
    
    Required env:
    - For WeChat MP: WECHAT_MP_APP_ID, WECHAT_MP_APP_SECRET
    - For WeWork: WEWORK_CORP_ID, WEWORK_CORP_SECRET, WEWORK_AGENT_ID
    """
    mp_client = None
    wework_client = None
    
    # Check for WeChat MP config
    mp_app_id = os.getenv("WECHAT_MP_APP_ID")
    mp_app_secret = os.getenv("WECHAT_MP_APP_SECRET")
    
    if mp_app_id and mp_app_secret:
        mp_client = WeChatMPClient(
            app_id=mp_app_id,
            app_secret=mp_app_secret,
            token=os.getenv("WECHAT_MP_TOKEN"),
            encoding_aes_key=os.getenv("WECHAT_MP_ENCODING_AES_KEY"),
        )
        print("✅ WeChat MP client configured")
    
    # Check for WeWork config
    wework_corp_id = os.getenv("WEWORK_CORP_ID")
    wework_corp_secret = os.getenv("WEWORK_CORP_SECRET")
    wework_agent_id = os.getenv("WEWORK_AGENT_ID")
    
    if wework_corp_id and wework_corp_secret and wework_agent_id:
        wework_client = WeWorkClient(
            corp_id=wework_corp_id,
            corp_secret=wework_corp_secret,
            agent_id=wework_agent_id,
            token=os.getenv("WEWORK_TOKEN"),
            encoding_aes_key=os.getenv("WEWORK_ENCODING_AES_KEY"),
        )
        print("✅ WeWork client configured")
    
    # Create agent
    context = VehicleContext()
    agent = XClawAgent(
        vehicle_context=context,
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    )
    
    return WeChatWebhookServer(
        mp_client=mp_client,
        wework_client=wework_client,
        agent=agent,
        host=os.getenv("WECHAT_HOST", "0.0.0.0"),
        port=int(os.getenv("WECHAT_PORT", "8080")),
        path=os.getenv("WECHAT_PATH", "/wechat/callback"),
    )
