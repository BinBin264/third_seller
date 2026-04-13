"""
database.py — Async SQLite wrapper dùng aiosqlite
"""

import logging
from contextlib import asynccontextmanager

import aiosqlite
from app.config import DB_PATH
from app.db.models import CREATE_PRODUCTS_TABLE, CREATE_PAYMENTS_TABLE, CREATE_USERS_TABLE

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_db():
    """Context manager trả về connection đã bật row_factory."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    """Tạo bảng nếu chưa tồn tại."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_PRODUCTS_TABLE)
        await db.execute(CREATE_PAYMENTS_TABLE)
        await db.execute(CREATE_USERS_TABLE)
        await db.commit()
    logger.info("Database initialised at %s", DB_PATH)
