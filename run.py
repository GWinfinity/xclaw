#!/usr/bin/env python3
"""
xClaw Launcher

Simple launcher script for xClaw bots.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def run_discord():
    """Run Discord bot."""
    from extensions.discord_bot.bot import run_bot
    print("🦞 Starting Discord Bot...")
    run_bot()


def run_wechat():
    """Run WeChat bot."""
    import asyncio
    from extensions.wechat_bot.bot import main
    print("🦞 Starting WeChat Bot...")
    asyncio.run(main())


def run_telegram():
    """Run Telegram bot."""
    from extensions.telegram_bot.bot import run_bot
    print("🦞 Starting Telegram Bot...")
    run_bot()


def run_example():
    """Run basic example."""
    import asyncio
    from examples.basic_usage import basic_vehicle_control
    print("🦞 Running basic example...")
    asyncio.run(basic_vehicle_control())


def run_monitor():
    """Run vehicle monitor."""
    import asyncio
    from examples.monitor_example import main
    print("🦞 Running vehicle monitor...")
    asyncio.run(main())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="🦞 xClaw - Natural language Tesla vehicle control"
    )
    
    parser.add_argument(
        "command",
        choices=["discord", "telegram", "wechat", "example", "monitor", "interactive"],
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    commands = {
        "discord": run_discord,
        "telegram": run_telegram,
        "wechat": run_wechat,
        "example": run_example,
        "monitor": run_monitor,
        "interactive": lambda: __import__("asyncio").run(
            __import__("examples.basic_usage", fromlist=["interactive_mode"]).interactive_mode()
        ),
    }
    
    try:
        commands[args.command]()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
