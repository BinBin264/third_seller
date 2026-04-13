"""
bot.py — Khởi tạo Application và đăng ký handlers
"""

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from app.config import BOT_TOKEN
from app.bot.handlers import (
    cmd_start,
    cmd_menu,
    cb_product,
    cb_quantity,
    handle_photo,
    handle_text,
)

logger = logging.getLogger(__name__)


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu",  cmd_menu))

    # Inline callbacks
    app.add_handler(CallbackQueryHandler(cb_product,  pattern=r"^product:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_quantity, pattern=r"^qty:\d+:.+$"))

    # Ảnh bill từ user (private chat)
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_photo))

    # User nhập số lượng custom (private chat, chỉ text số)
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, handle_text))

    logger.info("Bot handlers registered.")
    return app
