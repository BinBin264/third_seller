"""
config.py — Load toàn bộ cấu hình từ .env
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"[Config] Thiếu biến môi trường bắt buộc: {key}")
    return val


# ── Telegram Bot ──────────────────────────────────────────────
BOT_TOKEN: str = _require("BOT_TOKEN")
ADMIN_ID: int = int(_require("ADMIN_ID"))
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")

# ── Bank ──────────────────────────────────────────────────────
BANK_NAME: str    = os.getenv("BANK_NAME", "TPBank")
BANK_ID: str      = os.getenv("BANK_ID", "TPB")       # mã ngân hàng VietQR, xem tại vietqr.io/danh-sach-ngan-hang
BANK_ACCOUNT: str = os.getenv("BANK_ACCOUNT", "0000000000")
BANK_OWNER: str   = os.getenv("BANK_OWNER", "CHU TAI KHOAN")

# ── Telethon ──────────────────────────────────────────────────
TELETHON_API_ID: int = int(_require("TELETHON_API_ID"))
TELETHON_API_HASH: str = _require("TELETHON_API_HASH")
TELETHON_PHONE: str = _require("TELETHON_PHONE")
SOURCE_BOT: str = os.getenv("SOURCE_BOT", "mmoshopacc_bot")
TRIGGER_KEYWORD: str = os.getenv("TRIGGER_KEYWORD", "Cập nhật kho hàng")
TELETHON_SESSION_PATH: str = os.getenv("TELETHON_SESSION_PATH", "telethon_session")
TELETHON_STRING_SESSION: str = os.getenv("TELETHON_STRING_SESSION", "")

# ── Pricing ───────────────────────────────────────────────────
PRICE_MARKUP: float = float(os.getenv("PRICE_MARKUP", "25"))

# ── Misc ──────────────────────────────────────────────────────
SYNC_DELAY: float = float(os.getenv("SYNC_DELAY", "1.0"))
MENU_LIMIT: int = int(os.getenv("MENU_LIMIT", "0"))  # 0 = hiện toàn bộ
HISTORY_LIMIT: int = int(os.getenv("HISTORY_LIMIT", "200"))  # số tin lịch sử đọc khi khởi động
DB_PATH: str = os.getenv("DB_PATH", "data/shop.db")
