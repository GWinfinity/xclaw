"""
Discord Bot Example

Example of running the xClaw Discord bot.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from extensions.discord_bot.bot import run_bot

if __name__ == "__main__":
    print("🦞 Starting xClaw Discord Bot...")
    print("Make sure DISCORD_BOT_TOKEN is set in your .env file\n")
    run_bot()
