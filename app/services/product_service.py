"""
product_service.py — CRUD sản phẩm + logic anti-duplicate
"""

import hashlib
import logging
from typing import Optional

import aiosqlite

from app.db.database import get_db
from app.config import MENU_LIMIT

logger = logging.getLogger(__name__)


def _make_hash(name: str, raw_text: str) -> str:
    """
    Tạo hash định danh duy nhất cho một bản tin sản phẩm.
    Dùng tên + nội dung gốc để phát hiện duplicate chính xác.
    """
    payload = f"{name.strip().lower()}|{raw_text.strip()}"
    return hashlib.sha256(payload.encode()).hexdigest()


async def upsert_product(
    name: str,
    price: float,
    stock: int,
    raw_text: str,
) -> tuple[bool, str]:
    """
    Thêm mới hoặc cập nhật sản phẩm.

    Returns:
        (inserted: bool, action: str)
        action là "inserted" | "updated" | "skipped"
    """
    source_hash = _make_hash(name, raw_text)

    async with get_db() as db:
        # Kiểm tra hash trùng → bỏ qua hoàn toàn
        async with db.execute(
            "SELECT id FROM products WHERE source_hash = ?", (source_hash,)
        ) as cur:
            if await cur.fetchone():
                logger.debug("Duplicate product skipped: %s (hash=%s)", name, source_hash[:8])
                return False, "skipped"

        # Kiểm tra cùng tên → cập nhật giá + tồn kho
        async with db.execute(
            "SELECT id FROM products WHERE name = ?", (name.strip(),)
        ) as cur:
            existing = await cur.fetchone()

        if existing:
            await db.execute(
                """UPDATE products
                   SET price = ?, stock = ?, raw_text = ?, source_hash = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE name = ?""",
                (price, stock, raw_text, source_hash, name.strip()),
            )
            await db.commit()
            logger.info("Product updated: %s | price=%.1fK stock=%d", name, price, stock)
            return False, "updated"

        # Thêm mới
        await db.execute(
            """INSERT INTO products (name, price, stock, raw_text, source_hash)
               VALUES (?, ?, ?, ?, ?)""",
            (name.strip(), price, stock, raw_text, source_hash),
        )
        await db.commit()
        logger.info("Product inserted: %s | price=%.1fK stock=%d", name, price, stock)
        return True, "inserted"


async def clear_products() -> None:
    """Xóa toàn bộ sản phẩm để sync lại từ đầu."""
    async with get_db() as db:
        await db.execute("DELETE FROM products")
        await db.commit()
    logger.info("All products cleared.")


async def get_menu_products(limit: int = MENU_LIMIT) -> list[aiosqlite.Row]:
    """Lấy sản phẩm có tồn kho > 0. limit=0 thì lấy toàn bộ."""
    async with get_db() as db:
        if limit and limit > 0:
            query  = "SELECT id, name, price, stock FROM products WHERE stock > 0 ORDER BY updated_at DESC LIMIT ?"
            params = (limit,)
        else:
            query  = "SELECT id, name, price, stock FROM products WHERE stock > 0 ORDER BY updated_at DESC"
            params = ()
        async with db.execute(query, params) as cur:
            return await cur.fetchall()


async def get_product_by_id(product_id: int) -> Optional[aiosqlite.Row]:
    """Lấy sản phẩm theo ID."""
    async with get_db() as db:
        async with db.execute(
            "SELECT id, name, price, stock FROM products WHERE id = ?",
            (product_id,),
        ) as cur:
            return await cur.fetchone()


# ── Users ─────────────────────────────────────────────────────────────────────

async def save_user(user_id: int, username: str, first_name: str) -> None:
    """Lưu user khi /start, bỏ qua nếu đã tồn tại."""
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO users (user_id, username, first_name)
               VALUES (?, ?, ?)""",
            (user_id, username or "", first_name or ""),
        )
        await db.commit()


async def get_all_user_ids() -> list[int]:
    """Lấy toàn bộ user_id để broadcast."""
    async with get_db() as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [r["user_id"] for r in rows]


# ── Payments ──────────────────────────────────────────────────────────────────

async def create_payment(order_code: str, user_id: int, username: str, product_id: int) -> None:
    """Ghi nhận một đơn chờ xác nhận."""
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO payments (order_code, user_id, username, product_id)
               VALUES (?, ?, ?, ?)""",
            (order_code, user_id, username or "", product_id),
        )
        await db.commit()
    logger.info("Payment created: order=%s user=%d", order_code, user_id)


async def update_payment_status(order_code: str, status: str) -> None:
    """Cập nhật trạng thái đơn: confirmed | rejected."""
    async with get_db() as db:
        await db.execute(
            """UPDATE payments
               SET status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE order_code = ?""",
            (status, order_code),
        )
        await db.commit()
    logger.info("Payment %s → %s", order_code, status)


async def get_payment_by_code(order_code: str) -> Optional[aiosqlite.Row]:
    """Tìm đơn theo mã."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM payments WHERE order_code = ?", (order_code,)
        ) as cur:
            return await cur.fetchone()
