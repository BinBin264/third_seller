"""
keyboards.py — Inline keyboards cho bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


_ICON_MAP = [
    (["chatgpt", "gpt", "openai", "cdk", "code"],        "🤖"),
    (["gemini", "google"],                                "✨"),
    (["grok", "xai"],                                     "⚡️"),
    (["capcut", "cap cut"],                               "🎬"),
    (["kling"],                                           "🎥"),
    (["veo"],                                             "🎞️"),
    (["elevenlabs", "eleven"],                            "🎙️"),
    (["expressvpn", "hma", "vpn"],                        "🔒"),
    (["meitu"],                                           "🖼️"),
    (["perplexity"],                                      "🔍"),
    (["netflix"],                                         "🎬"),
    (["spotify"],                                         "🎵"),
]


def _icon_for(name: str) -> str:
    lower = name.lower()
    for keywords, icon in _ICON_MAP:
        if any(k in lower for k in keywords):
            return icon
    return "📦"


def menu_keyboard(products: list) -> InlineKeyboardMarkup:
    """
    Format: {icon} {giá} | {tên} ({tồn kho})
    """
    from app.services.pricing_service import format_price
    buttons = []
    for p in products:
        icon  = _icon_for(p["name"])
        price = format_price(p["price"])
        name  = p["name"]
        stock = p["stock"]

        label = f"{icon} {price} | {name}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"product:{p['id']}")])

    return InlineKeyboardMarkup(buttons)


def quantity_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Chọn số lượng sau khi chọn sản phẩm."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1",       callback_data=f"qty:{product_id}:1"),
            InlineKeyboardButton("2",       callback_data=f"qty:{product_id}:2"),
            InlineKeyboardButton("3",       callback_data=f"qty:{product_id}:3"),
        ],
        [
            InlineKeyboardButton("🔢 Số khác", callback_data=f"qty:{product_id}:custom"),
        ],
    ])
