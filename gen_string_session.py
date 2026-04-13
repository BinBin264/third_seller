"""
Generate Telethon StringSession for cloud deploy.

Usage:
  1) Copy .env.example -> .env and fill TELETHON_API_ID/HASH/PHONE
  2) Run: python3 gen_string_session.py
  3) Copy the printed TELETHON_STRING_SESSION into Render Environment
"""

import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    load_dotenv()

    api_id = int(os.environ["TELETHON_API_ID"])
    api_hash = os.environ["TELETHON_API_HASH"]
    phone = os.environ["TELETHON_PHONE"]

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start(phone=phone)  # will prompt in terminal for OTP/2FA if needed
    print("\nTELETHON_STRING_SESSION=" + client.session.save())
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

