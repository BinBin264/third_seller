"""
Chạy script này MỘT LẦN để tạo telethon_session.session
Sau đó Docker sẽ dùng lại session đó, không cần nhập OTP nữa.
"""

import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

from telethon import TelegramClient

API_ID   = int(os.getenv("TELETHON_API_ID"))
API_HASH = os.getenv("TELETHON_API_HASH")
PHONE    = os.getenv("TELETHON_PHONE")


async def main():
    client = TelegramClient("telethon_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("✅ Auth thành công! File telethon_session.session đã được tạo.")
    await client.disconnect()


asyncio.run(main())
