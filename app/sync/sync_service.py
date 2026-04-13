"""
sync_service.py — Telethon: forward message + sync DB qua /menu định kỳ
"""

import asyncio
import logging
import re

from telethon import TelegramClient, events

from app.config import (
    TELETHON_API_ID,
    TELETHON_API_HASH,
    TELETHON_PHONE,
    SOURCE_BOT,
    SYNC_DELAY,
    TRIGGER_KEYWORD,
    TELETHON_SESSION_PATH,
)
from app.services.product_service import upsert_product, get_all_user_ids, clear_products
from app.services.pricing_service import apply_markup

logger = logging.getLogger(__name__)

# ── Parser: Inline button từ /menu ───────────────────────────────────────────
# Format: "15K | Grok Super 40-50 Ngày | KBH (27)"
_BUTTON_RE = re.compile(
    r"^(?P<price>\d+(?:[.,]\d+)?)[Kk]\s*\|"
    r"(?P<name>.+?)"
    r"\((?P<stock>\d+)\)\s*$",
    re.UNICODE,
)


def _price_to_k(num_str: str) -> float:
    cleaned = num_str.replace(".", "").replace(",", "")
    value   = float(cleaned)
    return value


# ── Forward message tới tất cả user ──────────────────────────────────────────

_PRICE_REPLACE_RE = re.compile(
    r"(Giá[:\s]+)([\d.,]+)([Kk]|\.?000đ|,?000đ|đ)?",
    re.IGNORECASE,
)


def _rewrite_price(text: str) -> str:
    """Tìm giá trong text → tăng theo PRICE_MARKUP → làm tròn 1K → thay thế. Bỏ dòng tồn kho."""
    # Xoá dòng chứa "Tổng tồn kho" và "Vừa thêm"
    lines = [
        l for l in text.splitlines()
        if "tổng tồn kho" not in l.lower() and "vừa thêm" not in l.lower()
    ]
    cleaned = "\n".join(lines)

    def replacer(m):
        prefix  = m.group(1)
        num_str = m.group(2).replace(".", "").replace(",", "")
        unit    = (m.group(3) or "").strip().lower()
        try:
            value   = float(num_str)
            price_k = value if unit == "k" else (value / 1000 if value >= 1000 else value)
            new_price_k = apply_markup(price_k)
            return f"{prefix}{int(new_price_k)}K"
        except ValueError:
            return m.group(0)

    return _PRICE_REPLACE_RE.sub(replacer, cleaned)


async def _forward_to_all_users(client: TelegramClient, message, bot) -> None:
    """
    Đọc message từ Telethon → sửa giá +25% → gửi qua PTB bot tới tất cả user.
    """
    if bot is None:
        logger.warning("[Forward] bot is None, cannot forward.")
        return

    user_ids = await get_all_user_ids()
    if not user_ids:
        logger.info("[Forward] No users to forward to.")
        return

    raw_text     = message.raw_text or ""
    rewritten    = _rewrite_price(raw_text)  # giá đã được markup
    photo        = None

    if message.photo:
        try:
            photo = await message.download_media(bytes)
        except Exception as e:
            logger.warning("[Forward] Could not download photo: %s", e)

    success = failed = 0
    for uid in user_ids:
        try:
            if photo:
                await bot.send_photo(
                    chat_id=uid,
                    photo=photo,
                    caption=rewritten or None,
                )
            elif rewritten:
                await bot.send_message(chat_id=uid, text=rewritten)
            success += 1
        except Exception as e:
            logger.debug("[Forward] Failed uid=%d: %s", uid, e)
            failed += 1
        await asyncio.sleep(0.05)

    logger.info("[Forward] Done. success=%d failed=%d", success, failed)


# ── Fetch /menu và cập nhật DB ────────────────────────────────────────────────

async def _fetch_via_menu(client: TelegramClient) -> None:
    """
    Gửi /menu → xóa sạch DB → insert lại toàn bộ từ inline buttons.
    Đảm bảo menu bot mình luôn khớp chính xác với shop nguồn.
    """
    logger.info("[Sync] Sending /menu to @%s ...", SOURCE_BOT)
    try:
        await client.send_message(SOURCE_BOT, "/menu")
        await asyncio.sleep(6)

        products = []
        async for message in client.iter_messages(SOURCE_BOT, limit=10):
            if not message.buttons:
                continue

            logger.info("[Sync] Found menu with %d rows.", len(message.buttons))
            for row in message.buttons:
                for btn in row:
                    text = btn.text.strip()
                    m    = _BUTTON_RE.match(text)
                    if not m:
                        logger.debug("[Sync] Button no match: %r", text)
                        continue
                    try:
                        price_raw = _price_to_k(m.group("price"))
                        name      = m.group("name").strip(" |")
                        stock     = int(m.group("stock"))
                        products.append({
                            "name": name,
                            "price_raw": price_raw,
                            "stock": stock,
                            "raw": text,
                        })
                    except Exception as e:
                        logger.warning("[Sync] Button parse error %r: %s", text, e)
            break

        if not products:
            logger.warning("[Sync] No products parsed — keeping existing DB.")
            return

        # Xóa sạch rồi insert lại
        await clear_products()
        logger.info("[Sync] DB cleared. Inserting %d products...", len(products))

        for item in products:
            sell_price = apply_markup(item["price_raw"])
            await upsert_product(
                name=item["name"], price=sell_price,
                stock=item["stock"], raw_text=item["raw"],
            )
            await asyncio.sleep(SYNC_DELAY)

        logger.info("[Sync] /menu sync done. Total=%d", len(products))
    except Exception as e:
        logger.error("[Sync] Error fetching /menu: %s", e)


async def _menu_cron(client: TelegramClient, interval_hours: int = 4) -> None:
    """Cron job: cập nhật DB từ /menu mỗi interval_hours tiếng."""
    while True:
        await asyncio.sleep(interval_hours * 3600)
        logger.info("[Cron] Running scheduled /menu sync...")
        await _fetch_via_menu(client)


# ── Client & event handler ────────────────────────────────────────────────────

def create_telethon_client() -> TelegramClient:
    # Telethon sẽ tự thêm đuôi ".session" nếu cần. Cho phép set path bền vững trên cloud.
    return TelegramClient(TELETHON_SESSION_PATH, TELETHON_API_ID, TELETHON_API_HASH)


async def start_sync(client: TelegramClient, bot=None) -> None:

    @client.on(events.NewMessage(from_users=SOURCE_BOT))
    async def on_new_message(event: events.NewMessage.Event) -> None:
        """Chỉ forward tin có 'Cập nhật kho hàng', bỏ qua tất cả tin khác."""
        text = event.raw_text or ""
        if TRIGGER_KEYWORD not in text:
            return

        logger.info("[Telethon] Inventory update — forwarding...")
        try:
            await _forward_to_all_users(client, event.message, bot)
        except Exception as exc:
            logger.exception("[Telethon] Forward error: %s", exc)

    await client.start(phone=TELETHON_PHONE)
    logger.info("[Telethon] Connected. Listening to @%s ...", SOURCE_BOT)

    # Lần đầu: load /menu vào DB
    await _fetch_via_menu(client)

    # Chạy cron 4 tiếng song song
    asyncio.ensure_future(_menu_cron(client, interval_hours=4))

    await client.run_until_disconnected()
