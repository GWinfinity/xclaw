"""
Telegram Bot Example

Example of running the xClaw Telegram bot.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from extensions.telegram_bot.bot import run_bot

if __name__ == "__main__":
    print("🦞 Starting xClaw Telegram Bot...")
    print("Make sure TELEGRAM_BOT_TOKEN is set in your .env file\n")
    run_bot()
