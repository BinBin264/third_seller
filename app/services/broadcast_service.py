"""
broadcast_service.py — Gửi thông báo kho mới tới tất cả user đã /start
"""

import asyncio
import logging

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import Forbidden, BadRequest

from app.services.product_service import get_all_user_ids
from app.services.pricing_service import format_price

logger = logging.getLogger(__name__)

# Delay giữa mỗi lần gửi để tránh flood Telegram
_BROADCAST_DELAY = 0.05


async def broadcast_new_product(bot: Bot, name: str, price: float, stock: int) -> None:
    """
    Gửi thông báo sản phẩm mới tới tất cả user.
    Tự động bỏ qua user đã block bot (Forbidden).
    """
    user_ids = await get_all_user_ids()
    if not user_ids:
        logger.info("[Broadcast] No users to notify.")
        return

    text = (
        f'<tg-emoji emoji-id="5458603043203327669">🔔</tg-emoji> <b>KHO HÀNG VỪA CẬP NHẬT!</b>\n\n'
        f'<tg-emoji emoji-id="5424972470023104089">🔥</tg-emoji> <b>{name}</b>\n'
        f'<tg-emoji emoji-id="5417924076503062111">💰</tg-emoji> Giá: <code>{format_price(price)}/acc</code>\n'
        f'<tg-emoji emoji-id="5203993413346680064">📊</tg-emoji> Tồn kho: <code>{stock} acc</code>\n\n'
        f'<tg-emoji emoji-id="5400090058030075645">🛒</tg-emoji> /menu để xem và mua hàng'
    )

    success = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(
                chat_id=uid,
                text=text,
                parse_mode=ParseMode.HTML,
            )
            success += 1
        except Forbidden:
            # User đã block bot — bỏ qua
            logger.debug("[Broadcast] User %d blocked bot, skipping.", uid)
            failed += 1
        except BadRequest as e:
            logger.warning("[Broadcast] BadRequest for user %d: %s", uid, e)
            failed += 1
        except Exception as e:
            logger.error("[Broadcast] Error sending to user %d: %s", uid, e)
            failed += 1

        await asyncio.sleep(_BROADCAST_DELAY)

    logger.info("[Broadcast] Done. success=%d failed=%d total=%d", success, failed, len(user_ids))
