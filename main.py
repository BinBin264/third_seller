"""
main.py — Entry point: chạy đồng thời Telethon sync + Telegram bot
"""

import asyncio
import logging
import os
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

async def run_health_server() -> None:
    """
    Render Free yêu cầu Web Service phải listen trên $PORT.
    Ta chạy một HTTP server cực nhỏ để healthcheck, đồng thời bot vẫn chạy bình thường.
    """
    port = int(os.getenv("PORT", "10000"))

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            data = await reader.read(1024)
            first_line = data.split(b"\r\n", 1)[0] if data else b""
            path = b"/"
            try:
                parts = first_line.split()
                if len(parts) >= 2:
                    path = parts[1]
            except Exception:
                path = b"/"

            if path in (b"/health", b"/"):
                body = b"ok"
                writer.write(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    + f"Content-Length: {len(body)}\r\n".encode()
                    + b"Connection: close\r\n\r\n"
                    + body
                )
            else:
                body = b"not found"
                writer.write(
                    b"HTTP/1.1 404 Not Found\r\n"
                    b"Content-Type: text/plain\r\n"
                    + f"Content-Length: {len(body)}\r\n".encode()
                    + b"Connection: close\r\n\r\n"
                    + body
                )
            await writer.drain()
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(handler, host="0.0.0.0", port=port)
    sockets = server.sockets or []
    actual = sockets[0].getsockname()[1] if sockets else port
    logger.info("Health server listening on :%s", actual)
    async with server:
        await server.serve_forever()


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
            tg.create_task(run_health_server())
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
