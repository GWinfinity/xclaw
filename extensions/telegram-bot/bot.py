"""
Telegram Bot for xClaw

Provides Telegram interface for controlling Tesla vehicles.
"""

import os
import sys
import logging
from typing import Optional, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from packages.xclaw_core import XClawAgent, VehicleContext


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class XClawTelegramBot:
    """Telegram bot for xClaw."""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_users = self._parse_allowed_users()
        self.agents: dict[str, XClawAgent] = {}
        self.contexts: dict[str, VehicleContext] = {}
    
    def _parse_allowed_users(self) -> Optional[List[int]]:
        """Parse allowed user IDs from environment."""
        users_str = os.getenv("TELEGRAM_ALLOWED_USERS", "")
        if not users_str:
            return None
        try:
            return [int(uid.strip()) for uid in users_str.split(",") if uid.strip()]
        except ValueError:
            logger.warning("Invalid TELEGRAM_ALLOWED_USERS format")
            return None
    
    def _is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized."""
        if self.allowed_users is None:
            return True
        return user_id in self.allowed_users
    
    async def get_agent(self, chat_id: str) -> XClawAgent:
        """Get or create agent for chat."""
        if chat_id not in self.agents:
            context = VehicleContext()
            self.agents[chat_id] = XClawAgent(context)
            self.contexts[chat_id] = context
        return self.agents[chat_id]
    
    # ==================== Command Handlers ====================
    
    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        if not self._is_authorized(user.id):
            await update.message.reply_text(
                "⛔ 你没有权限使用此 Bot。请联系管理员添加你的用户 ID。"
            )
            return
        
        welcome_text = f"""
🦞 **欢迎使用 xClaw！**

你好 {user.first_name}！

我是你的特斯拉智能助手，可以帮助你：
• 🔒 控制车门锁定
• ❄️ 管理车内空调
• 🔋 查看充电状态
• 📍 获取车辆位置
• 👁️ 控制哨兵模式

**快速开始:**
发送 `!help` 查看所有命令
或直接发送自然语言，例如："帮我锁车"

⚠️ **安全提示**: 某些敏感操作需要二次确认
"""
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🦞 **xClaw 命令列表**

**车辆状态:**
/status - 查看完整车辆状态
/battery - 查看电池和充电状态
/location - 获取车辆位置

**车辆控制:**
/lock - 锁定车辆
/unlock - 解锁车辆 (需确认)
/honk - 鸣笛
/flash - 闪灯

**空调控制:**
/climate on - 开启空调
/climate off - 关闭空调
/climate 22 - 设置温度

**充电管理:**
/charge start - 开始充电
/charge stop - 停止充电
/charge limit 80 - 设置充电限制

**其他:**
/sentry on/off - 哨兵模式
/trunk - 打开后备箱
/frunk - 打开前备箱

**自然语言:**
直接发送消息，例如：
• "车里太热了"
• "还剩多少电"
• "开启空调"
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        try:
            summary = await agent.get_vehicle_summary()
            await update.message.reply_text(summary, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ 错误: {str(e)}")
    
    async def lock_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lock command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        try:
            response = await agent.process("帮我锁定车辆")
            await update.message.reply_text(response.message)
        except Exception as e:
            await update.message.reply_text(f"❌ 错误: {str(e)}")
    
    async def unlock_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unlock command with confirmation."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        keyboard = [
            [
                InlineKeyboardButton("✅ 确认解锁", callback_data="unlock_confirm"),
                InlineKeyboardButton("❌ 取消", callback_data="unlock_cancel"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ **安全警告**\n\n你确定要解锁车辆吗？\n这会让车辆处于未锁定状态。",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    
    async def climate_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /climate command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        args = context.args
        if not args:
            # Show climate status
            response = await agent.process("查看空调状态")
        elif args[0].lower() in ["on", "开", "开启"]:
            response = await agent.process("开启空调")
        elif args[0].lower() in ["off", "关", "关闭"]:
            response = await agent.process("关闭空调")
        elif args[0].isdigit():
            temp = int(args[0])
            response = await agent.process(f"设置空调温度到{temp}度")
        else:
            response = await agent.process("查看空调状态")
        
        await update.message.reply_text(response.message)
    
    async def charge_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /charge command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        args = context.args
        if not args:
            response = await agent.process("查看充电状态")
        elif args[0].lower() in ["start", "开始"]:
            response = await agent.process("开始充电")
        elif args[0].lower() in ["stop", "停止"]:
            response = await agent.process("停止充电")
        elif args[0].lower() in ["limit", "限制"] and len(args) > 1:
            try:
                percent = int(args[1])
                response = await agent.process(f"设置充电限制到{percent}%")
            except ValueError:
                response = await agent.process("查看充电状态")
        else:
            response = await agent.process("查看充电状态")
        
        await update.message.reply_text(response.message)
    
    async def honk_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /honk command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        try:
            response = await agent.process("鸣笛")
            await update.message.reply_text(response.message)
        except Exception as e:
            await update.message.reply_text(f"❌ 错误: {str(e)}")
    
    async def flash_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /flash command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        try:
            response = await agent.process("闪灯")
            await update.message.reply_text(response.message)
        except Exception as e:
            await update.message.reply_text(f"❌ 错误: {str(e)}")
    
    async def sentry_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /sentry command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        args = context.args
        if args and args[0].lower() in ["on", "开", "开启"]:
            response = await agent.process("开启哨兵模式")
        elif args and args[0].lower() in ["off", "关", "关闭"]:
            response = await agent.process("关闭哨兵模式")
        else:
            response = await agent.process("查看哨兵模式状态")
        
        await update.message.reply_text(response.message)
    
    async def trunk_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trunk command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        try:
            response = await agent.process("打开后备箱")
            await update.message.reply_text(response.message)
        except Exception as e:
            await update.message.reply_text(f"❌ 错误: {str(e)}")
    
    async def frunk_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /frunk command."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        chat_id = str(update.effective_chat.id)
        agent = await self.get_agent(chat_id)
        
        try:
            response = await agent.process("打开前备箱")
            await update.message.reply_text(response.message)
        except Exception as e:
            await update.message.reply_text(f"❌ 错误: {str(e)}")
    
    # ==================== Callback Handlers ====================
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "unlock_confirm":
            chat_id = str(update.effective_chat.id)
            agent = await self.get_agent(chat_id)
            
            try:
                response = await agent.process("帮我解锁车辆")
                await query.edit_message_text(response.message)
            except Exception as e:
                await query.edit_message_text(f"❌ 错误: {str(e)}")
        
        elif query.data == "unlock_cancel":
            await query.edit_message_text("🚫 已取消解锁")
    
    # ==================== Message Handler ====================
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle natural language messages."""
        if not self._is_authorized(update.effective_user.id):
            return
        
        message_text = update.message.text
        
        # Skip commands
        if message_text.startswith("/"):
            return
        
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        try:
            agent = await self.get_agent(chat_id)
            response = await agent.process(message_text, user_id=user_id)
            await update.message.reply_text(response.message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(f"❌ 处理消息时出错: {str(e)}")
    
    def run(self):
        """Run the bot."""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            print("❌ Error: TELEGRAM_BOT_TOKEN not set")
            return
        
        # Create application
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_cmd))
        application.add_handler(CommandHandler("help", self.help_cmd))
        application.add_handler(CommandHandler("status", self.status_cmd))
        application.add_handler(CommandHandler("battery", self.status_cmd))
        application.add_handler(CommandHandler("lock", self.lock_cmd))
        application.add_handler(CommandHandler("unlock", self.unlock_cmd))
        application.add_handler(CommandHandler("climate", self.climate_cmd))
        application.add_handler(CommandHandler("charge", self.charge_cmd))
        application.add_handler(CommandHandler("honk", self.honk_cmd))
        application.add_handler(CommandHandler("flash", self.flash_cmd))
        application.add_handler(CommandHandler("sentry", self.sentry_cmd))
        application.add_handler(CommandHandler("trunk", self.trunk_cmd))
        application.add_handler(CommandHandler("frunk", self.frunk_cmd))
        
        # Callback handler
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Run
        print("🦞 xClaw Telegram Bot started!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_bot():
    """Entry point."""
    bot = XClawTelegramBot()
    bot.run()


if __name__ == "__main__":
    run_bot()
