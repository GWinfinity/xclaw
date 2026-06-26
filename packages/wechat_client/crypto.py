"""
WeChat Crypto Utilities

Message encryption/decryption for WeChat.
Based on WeChat official SDK.
"""

import base64
import hashlib
import struct
import random
import string
from typing import Optional, Tuple
from Crypto.Cipher import AES
from xml.etree import ElementTree as ET


class WeChatCrypto:
    """
    WeChat message encryption/decryption.
    
    Used for:
    - WeChat Official Account (微信公众号)
    - WeCom/WeWork (企业微信)
    
    Docs: https://developers.weixin.qq.com/doc/
    """
    
    def __init__(self, token: str, encoding_aes_key: str, app_id: str):
        """
        Initialize crypto.
        
        Args:
            token: Verification token
            encoding_aes_key: 43-character AES key
            app_id: App ID
        """
        self.token = token
        self.app_id = app_id
        
        # Decode AES key (base64 encoded)
        self.aes_key = base64.b64decode(encoding_aes_key + "=")
        self.cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str, msg: str = "") -> bool:
        """
        Verify WeChat message signature.
        
        Args:
            signature: Signature from WeChat
            timestamp: Timestamp from WeChat
            nonce: Nonce from WeChat
            msg: Optional message body
            
        Returns:
            True if signature is valid
        """
        tmp_arr = [self.token, timestamp, nonce]
        if msg:
            tmp_arr.append(msg)
        tmp_arr.sort()
        tmp_str = "".join(tmp_arr)
        
        hash_code = hashlib.sha1(tmp_str.encode()).hexdigest()
        return hash_code == signature
    
    def encrypt(self, msg: str) -> str:
        """
        Encrypt message for WeChat.
        
        Args:
            msg: Plain text message
            
        Returns:
            Base64 encoded encrypted message
        """
        # Generate random string
        random_str = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        
        # Build message: random(16B) + msg_length(4B) + msg + appid
        msg_bytes = msg.encode('utf-8')
        msg_len = struct.pack("I", socket.htonl(len(msg_bytes)))
        app_id_bytes = self.app_id.encode('utf-8')
        
        full_msg = random_str.encode('utf-8') + msg_len + msg_bytes + app_id_bytes
        
        # PKCS7 padding
        block_size = 32
        pad_len = block_size - (len(full_msg) % block_size)
        padded_msg = full_msg + bytes([pad_len] * pad_len)
        
        # Encrypt
        encrypted = self.cipher.encrypt(padded_msg)
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_msg: str) -> Tuple[str, str]:
        """
        Decrypt message from WeChat.
        
        Args:
            encrypted_msg: Base64 encoded encrypted message
            
        Returns:
            Tuple of (decrypted_message, app_id)
        """
        # Decode base64
        encrypted_bytes = base64.b64decode(encrypted_msg)
        
        # Decrypt
        decrypted = self.cipher.decrypt(encrypted_bytes)
        
        # Remove PKCS7 padding
        pad_len = decrypted[-1]
        decrypted = decrypted[:-pad_len]
        
        # Parse message: random(16B) + msg_length(4B) + msg + appid
        content = decrypted[16:]  # Skip random
        msg_len = struct.unpack("I", content[:4])[0]
        msg_len = socket.ntohl(msg_len)
        
        msg = content[4:4+msg_len].decode('utf-8')
        app_id = content[4+msg_len:].decode('utf-8')
        
        return msg, app_id
    
    def generate_signature(self, timestamp: str, nonce: str, msg: str = "") -> str:
        """
        Generate signature for WeChat.
        
        Args:
            timestamp: Timestamp
            nonce: Nonce
            msg: Optional message
            
        Returns:
            SHA1 signature
        """
        tmp_arr = [self.token, timestamp, nonce]
        if msg:
            tmp_arr.append(msg)
        tmp_arr.sort()
        tmp_str = "".join(tmp_arr)
        
        return hashlib.sha1(tmp_str.encode()).hexdigest()


import socket  # Required for htonl/ntohl
