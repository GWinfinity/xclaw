"""
Discord Bot for xClaw

Provides Discord interface for controlling Tesla vehicles.
"""

import os
import asyncio
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import xClaw core
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from packages.xclaw_core import XClawAgent, VehicleContext


class XClawDiscordBot(commands.Bot):
    """Discord bot for xClaw."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )
        
        self.agents: dict[str, XClawAgent] = {}
        self.contexts: dict[str, VehicleContext] = {}
    
    async def setup_hook(self):
        """Setup bot."""
        print(f"🦞 xClaw Discord Bot logged in as {self.user}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="你的特斯拉"
            )
        )
    
    async def get_agent(self, guild_id: str) -> XClawAgent:
        """Get or create agent for guild."""
        if guild_id not in self.agents:
            context = VehicleContext()
            self.agents[guild_id] = XClawAgent(context)
            self.contexts[guild_id] = context
        return self.agents[guild_id]


bot = XClawDiscordBot()


@bot.event
async def on_ready():
    """Called when bot is ready."""
    print(f"✅ Bot is ready!")
    print(f"📝 Invite URL: {discord.utils.oauth_url(bot.user.id)}")


@bot.command(name="status")
async def status_cmd(ctx: commands.Context):
    """Get vehicle status."""
    async with ctx.typing():
        try:
            agent = await bot.get_agent(str(ctx.guild.id))
            summary = await agent.get_vehicle_summary()
            await ctx.send(summary)
        except Exception as e:
            await ctx.send(f"❌ 错误: {str(e)}")


@bot.command(name="lock")
async def lock_cmd(ctx: commands.Context):
    """Lock the vehicle."""
    async with ctx.typing():
        try:
            agent = await bot.get_agent(str(ctx.guild.id))
            response = await agent.process("帮我锁定车辆")
            await ctx.send(response.message)
        except Exception as e:
            await ctx.send(f"❌ 错误: {str(e)}")


@bot.command(name="unlock")
async def unlock_cmd(ctx: commands.Context):
    """Unlock the vehicle."""
    async with ctx.typing():
        # Confirmation for security
        confirm_msg = await ctx.send(
            "⚠️ **安全警告**: 你确定要解锁车辆吗？\n"
            "这会让车辆处于未锁定状态。\n"
            "✅ 确认解锁 | ❌ 取消"
        )
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == confirm_msg.id
            )
        
        try:
            reaction, user = await bot.wait_for(
                "reaction_add",
                timeout=30.0,
                check=check
            )
            
            if str(reaction.emoji) == "✅":
                agent = await bot.get_agent(str(ctx.guild.id))
                response = await agent.process("帮我解锁车辆")
                await ctx.send(response.message)
            else:
                await ctx.send("🚫 已取消解锁")
                
        except asyncio.TimeoutError:
            await ctx.send("⏰ 操作超时，未执行解锁")


@bot.command(name="climate")
async def climate_cmd(ctx: commands.Context, *, args: str = ""):
    """
    Control climate.
    Usage: !climate on | !climate off | !climate 22
    """
    async with ctx.typing():
        try:
            agent = await bot.get_agent(str(ctx.guild.id))
            
            if args.lower() in ["on", "开", "开启"]:
                response = await agent.process("开启空调")
            elif args.lower() in ["off", "关", "关闭"]:
                response = await agent.process("关闭空调")
            elif args.isdigit():
                temp = int(args)
                response = await agent.process(f"设置空调温度到{temp}度")
            else:
                response = await agent.process("查看空调状态")
            
            await ctx.send(response.message)
        except Exception as e:
            await ctx.send(f"❌ 错误: {str(e)}")


@bot.command(name="charge")
async def charge_cmd(ctx: commands.Context, *, args: str = ""):
    """
    Control charging.
    Usage: !charge status | !charge start | !charge stop
    """
    async with ctx.typing():
        try:
            agent = await bot.get_agent(str(ctx.guild.id))
            
            if args.lower() in ["start", "开始"]:
                response = await agent.process("开始充电")
            elif args.lower() in ["stop", "停止"]:
                response = await agent.process("停止充电")
            else:
                response = await agent.process("查看充电状态")
            
            await ctx.send(response.message)
        except Exception as e:
            await ctx.send(f"❌ 错误: {str(e)}")


@bot.command(name="honk")
async def honk_cmd(ctx: commands.Context):
    """Honk the horn."""
    async with ctx.typing():
        try:
            agent = await bot.get_agent(str(ctx.guild.id))
            response = await agent.process("鸣笛")
            await ctx.send(response.message)
        except Exception as e:
            await ctx.send(f"❌ 错误: {str(e)}")


@bot.command(name="flash")
async def flash_cmd(ctx: commands.Context):
    """Flash the lights."""
    async with ctx.typing():
        try:
            agent = await bot.get_agent(str(ctx.guild.id))
            response = await agent.process("闪灯")
            await ctx.send(response.message)
        except Exception as e:
            await ctx.send(f"❌ 错误: {str(e)}")


@bot.command(name="sentry")
async def sentry_cmd(ctx: commands.Context, state: str = ""):
    """
    Control sentry mode.
    Usage: !sentry on | !sentry off
    """
    async with ctx.typing():
        try:
            agent = await bot.get_agent(str(ctx.guild.id))
            
            if state.lower() in ["on", "开", "开启"]:
                response = await agent.process("开启哨兵模式")
            elif state.lower() in ["off", "关", "关闭"]:
                response = await agent.process("关闭哨兵模式")
            else:
                response = await agent.process("查看哨兵模式状态")
            
            await ctx.send(response.message)
        except Exception as e:
            await ctx.send(f"❌ 错误: {str(e)}")


@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    """Show help message."""
    help_text = """
🦞 **xClaw Discord Bot - 特斯拉智能助手**

**基本命令:**
`!status` - 查看车辆状态
`!help` - 显示此帮助

**车辆控制:**
`!lock` - 锁定车辆
`!unlock` - 解锁车辆 (需要确认)
`!honk` - 鸣笛
`!flash` - 闪灯

**空调控制:**
`!climate on` / `!climate 开` - 开启空调
`!climate off` / `!climate 关` - 关闭空调
`!climate 22` - 设置温度到22度

**充电管理:**
`!charge status` - 查看充电状态
`!charge start` - 开始充电
`!charge stop` - 停止充电

**哨兵模式:**
`!sentry on` / `!sentry off` - 开启/关闭哨兵模式

**自然语言:**
你也可以直接发送自然语言消息，例如：
• "帮我锁车"
• "车里太热了"
• "还剩多少电"
• "开启空调到24度"

---
📱 使用 Tesla Fleet API 安全连接
"""
    await ctx.send(help_text)


@bot.event
async def on_message(message: discord.Message):
    """Handle direct messages and mentions."""
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Process commands
    await bot.process_commands(message)
    
    # Handle mentions and DMs
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions
    
    if is_dm or is_mentioned:
        # Remove bot mention from message
        content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        if not content:
            await message.reply("你好！我是 xClaw 🦞，你的特斯拉智能助手。发送 `!help` 查看可用命令。")
            return
        
        # Don't process if it's a command
        if content.startswith("!"):
            return
        
        async with message.channel.typing():
            try:
                guild_id = str(message.guild.id) if message.guild else "dm"
                agent = await bot.get_agent(guild_id)
                user_id = str(message.author.id)
                
                response = await agent.process(content, user_id=user_id)
                await message.reply(response.message)
            except Exception as e:
                await message.reply(f"❌ 处理消息时出错: {str(e)}")


def run_bot():
    """Run the Discord bot."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ Error: DISCORD_BOT_TOKEN not set")
        print("Please set the DISCORD_BOT_TOKEN environment variable")
        return
    
    bot.run(token)


if __name__ == "__main__":
    run_bot()
