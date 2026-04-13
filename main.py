"""
main.py — Entry point: chạy đồng thời Telethon sync + Telegram bot
"""

import asyncio
import logging
import sys

from app.db.database import init_db
from app.sync.sync_service import create_telethon_client, start_sync
from app.bot.bot import build_app


# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging() -> None:
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("shop.log", encoding="utf-8"),
        ],
    )
    # Giảm noise từ thư viện
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


# ── Main ──────────────────────────────────────────────────────────────────────

async def run_bot(app) -> None:
    """Chạy python-telegram-bot (polling) trong async context."""
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info("Bot started. Polling...")

    # Giữ bot chạy mãi (sẽ bị cancel khi shutdown)
    await asyncio.Event().wait()


async def main() -> None:
    setup_logging()
    logger.info("=== Shop Bot starting ===")

    # Init DB
    await init_db()

    # Telethon client
    telethon = create_telethon_client()

    # PTB Application
    ptb_app = build_app()

    # Chạy song song cả hai
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(start_sync(telethon, bot=ptb_app.bot))
            tg.create_task(run_bot(ptb_app))
    except* KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Graceful shutdown
        try:
            if getattr(ptb_app, "updater", None) and ptb_app.updater.running:
                await ptb_app.updater.stop()
        except Exception:
            pass

        try:
            await ptb_app.stop()
        except RuntimeError:
            # App có thể chưa kịp start nếu lỗi network/token.
            pass
        except Exception:
            pass

        try:
            await ptb_app.shutdown()
        except Exception:
            pass

        try:
            await telethon.disconnect()
        except Exception:
            pass
        logger.info("=== Shop Bot stopped ===")


if __name__ == "__main__":
    asyncio.run(main())
