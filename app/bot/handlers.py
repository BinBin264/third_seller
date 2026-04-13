"""
handlers.py — Toàn bộ handler cho python-telegram-bot
"""

import logging
import random
import string

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.config import (
    ADMIN_USERNAME,
    BANK_NAME, BANK_ID, BANK_ACCOUNT, BANK_OWNER,
)
from app.bot.keyboards import menu_keyboard, quantity_keyboard
from app.services.product_service import (
    get_menu_products,
    get_product_by_id,
    create_payment,
    save_user,
)
from app.services.pricing_service import format_price

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _gen_order_code() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"KLG{suffix}"


def _fmt_user(update: Update) -> str:
    u = update.effective_user
    return f"@{u.username}" if u.username else f"id:{u.id}"


# ── Commands ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await save_user(user.id, user.username or "", user.first_name or "")
    name = user.first_name or "bạn"
    text = (
        f'<tg-emoji emoji-id="5461151367559141950">🎉</tg-emoji> Chào bạn! Chào mừng đến với shop tài khoản của <b>Bin</b>\n\n'
        f'<tg-emoji emoji-id="5397782960512444700">📌</tg-emoji> /menu — Xem danh sách sản phẩm\n'
        f'<tg-emoji emoji-id="5458603043203327669">🔔</tg-emoji> Thông báo cập nhật sản phẩm sẽ tự động gửi đến bạn\n'
        f'<tg-emoji emoji-id="5443038326535759644">💬</tg-emoji> Hỗ trợ: @{ADMIN_USERNAME}'
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    logger.info("[/start] user=%s", _fmt_user(update))


async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    products = await get_menu_products()
    if not products:
        await update.message.reply_text("😔 Hiện chưa có sản phẩm nào. Vui lòng quay lại sau.")
        return

    product_list = [dict(p) for p in products]
    kb = menu_keyboard(product_list)

    # Dùng custom animated emoji trong header (HTML mode)
    text = (
        '<tg-emoji emoji-id="5229064374403998351">🛍</tg-emoji> <b>DANH SÁCH SẢN PHẨM</b>\n\n'
        '<tg-emoji emoji-id="5400090058030075645">🛒</tg-emoji> Chọn sản phẩm để mua:'
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML, reply_markup=kb
    )
    logger.info("[/menu] user=%s | products=%d", _fmt_user(update), len(product_list))


# ── Callback: Chọn sản phẩm ──────────────────────────────────────────────────

async def cb_product(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """User bấm chọn sản phẩm → hiện chọn số lượng."""
    query = update.callback_query
    await query.answer()

    try:
        product_id = int(query.data.split(":")[1])
    except (IndexError, ValueError):
        return

    product = await get_product_by_id(product_id)
    if not product:
        await query.message.reply_text("⚠️ Sản phẩm không còn tồn tại.")
        return

    # Lưu product_id vào user_data để dùng khi nhập số khác
    ctx.user_data["pending_product_id"] = product_id

    text = (
        f"📦 *{product['name']}*\n"
        f"💰 Giá: `{format_price(product['price'])}/acc`\n"
        f"📊 Tồn kho: `{product['stock']} acc`\n\n"
        f"🔢 *Chọn số lượng:*"
    )
    await query.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=quantity_keyboard(product_id),
    )


# ── Callback: Chọn số lượng ───────────────────────────────────────────────────

async def cb_quantity(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """User chọn số lượng (1/2/3/custom)."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")  # qty:{product_id}:{qty}
    if len(parts) < 3:
        return

    try:
        product_id = int(parts[1])
    except ValueError:
        return

    qty_str = parts[2]

    if qty_str == "custom":
        # Yêu cầu user nhập số
        ctx.user_data["pending_product_id"] = product_id
        ctx.user_data["waiting_qty"] = True
        await query.message.reply_text(
            "✏️ Nhập số lượng bạn muốn mua:",
        )
        return

    try:
        qty = int(qty_str)
    except ValueError:
        return

    await _send_payment_info(query.message, ctx, product_id, qty, update.effective_user)


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Nhận số lượng user nhập vào (khi waiting_qty=True)."""
    if not ctx.user_data.get("waiting_qty"):
        return

    text = update.message.text.strip()
    try:
        qty = int(text)
        if qty <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Vui lòng nhập số nguyên dương.")
        return

    ctx.user_data["waiting_qty"] = False
    product_id = ctx.user_data.get("pending_product_id")
    if not product_id:
        return

    await _send_payment_info(update.message, ctx, product_id, qty, update.effective_user)


def _build_vietqr_url(amount_k: float, order_code: str) -> str:
    """
    Tạo URL ảnh QR từ VietQR.
    amount_k: đơn vị K (VD: 50.0 → 50000đ)
    """
    amount_vnd = int(amount_k * 1000)
    from urllib.parse import quote
    info = quote(order_code)
    owner = quote(BANK_OWNER)
    return (
        f"https://img.vietqr.io/image/{BANK_ID}-{BANK_ACCOUNT}-compact2.png"
        f"?amount={amount_vnd}&addInfo={info}&accountName={owner}"
    )


async def _send_payment_info(message, ctx, product_id: int, qty: int, user) -> None:
    """Gửi QR + thông tin thanh toán sau khi chọn sản phẩm + số lượng."""
    product = await get_product_by_id(product_id)
    if not product:
        await message.reply_text("⚠️ Sản phẩm không còn tồn tại.")
        return

    order_code  = _gen_order_code()
    total_price = product["price"] * qty

    await create_payment(
        order_code=order_code,
        user_id=user.id,
        username=user.username or "",
        product_id=product_id,
    )

    qr_url = _build_vietqr_url(total_price, order_code)

    caption = (
        f"🛒 *XÁC NHẬN ĐƠN HÀNG*\n\n"
        f"📦 *{product['name']}*\n"
        f"🔢 Số lượng: `{qty} acc`\n"
        f"💰 Đơn giá: `{format_price(product['price'])}/acc`\n"
        f"💵 Tổng tiền: `{format_price(total_price)}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 NH: `{BANK_NAME}` — TK: `{BANK_ACCOUNT}`\n"
        f"👤 Chủ TK: `{BANK_OWNER}`\n"
        f"📝 Nội dung CK: `{order_code}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📸 Sau khi CK:\n"
        f"   • Gửi *ảnh bill* cho @{ADMIN_USERNAME}\n"
        f"   • Hoặc nhắn Zalo SDT: `0929359373` để được hỗ trợ"
    )

    try:
        await message.reply_photo(
            photo=qr_url,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        # Fallback nếu QR lỗi: gửi text thuần
        await message.reply_text(caption, parse_mode=ParseMode.MARKDOWN)

    logger.info("[Order] order=%s user=%d product=%d qty=%d total=%.1fK",
                order_code, user.id, product_id, qty, total_price)


# ── Nhận ảnh chuyển khoản ─────────────────────────────────────────────────────

async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"📩 Vui lòng gửi ảnh bill cho @{ADMIN_USERNAME}\n"
        f"Hoặc nhắn Zalo SDT: `0929359373` để được hỗ trợ.",
        parse_mode=ParseMode.MARKDOWN,
    )
    logger.info("[Photo] Redirected user=%s to admin contact.", _fmt_user(update))
