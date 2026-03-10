"""
WeChat Bot Example

Example of running xClaw with WeChat integration.
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from extensions.wechat_bot.bot import WeChatBot


async def mp_example():
    """WeChat Official Account example."""
    print("🦞 xClaw WeChat Official Account Example\n")
    
    bot = WeChatBot.create_mp_bot(
        app_id=os.getenv("WECHAT_MP_APP_ID"),
        app_secret=os.getenv("WECHAT_MP_APP_SECRET"),
        token=os.getenv("WECHAT_MP_TOKEN"),
        encoding_aes_key=os.getenv("WECHAT_MP_ENCODING_AES_KEY"),
    )
    
    print("✅ WeChat MP Bot created")
    print("📍 Webhook URL: http://localhost:8080/wechat/callback")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()


async def wework_example():
    """WeCom/WeWork example."""
    print("🦞 xClaw WeCom Bot Example\n")
    
    bot = WeChatBot.create_wework_bot(
        corp_id=os.getenv("WEWORK_CORP_ID"),
        corp_secret=os.getenv("WEWORK_CORP_SECRET"),
        agent_id=os.getenv("WEWORK_AGENT_ID"),
        token=os.getenv("WEWORK_TOKEN"),
        encoding_aes_key=os.getenv("WEWORK_ENCODING_AES_KEY"),
    )
    
    print("✅ WeWork Bot created")
    print("📍 Webhook URL: http://localhost:8080/wechat/callback")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()


async def wechaty_example():
    """Personal WeChat via Wechaty example."""
    print("🦞 xClaw Wechaty Example")
    print("="*60)
    print("⚠️  WARNING: Personal WeChat automation may result in ban!")
    print("="*60)
    print()
    
    bot = WeChatBot.create_wechaty_bot(
        puppet=os.getenv("WECHATY_PUPPET", "wechaty-puppet-wechat"),
    )
    
    print("✅ Wechaty Bot created")
    print("📱 Scan QR code to login\n")
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="xClaw WeChat Example")
    parser.add_argument(
        "mode",
        choices=["mp", "wework", "wechaty"],
        help="WeChat mode: mp=公众号, wework=企业微信, wechaty=个人微信"
    )
    
    args = parser.parse_args()
    
    if args.mode == "mp":
        await mp_example()
    elif args.mode == "wework":
        await wework_example()
    elif args.mode == "wechaty":
        await wechaty_example()


if __name__ == "__main__":
    asyncio.run(main())
