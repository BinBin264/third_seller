"""
Chạy script này để lấy custom emoji ID từ một sticker pack.
Sau đó copy ID vào keyboards.py

Cách dùng:
    python get_emoji_ids.py
"""

import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

from telethon import TelegramClient
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

API_ID   = int(os.getenv("TELETHON_API_ID"))
API_HASH = os.getenv("TELETHON_API_HASH")
PHONE    = os.getenv("TELETHON_PHONE")

# Danh sách sticker pack muốn lấy emoji
# Tìm tên pack: vào Telegram → bấm vào sticker → "View pack" → lấy tên cuối URL
PACKS = [
    "TonEmoji",        # TON Emoji
    "NewsEmoji",       # News Emoji
    "AIEmoji",         # AI apps icons
    "AppIcons",        # App icons
    "SocialEmoji",     # Social media icons
]


async def main():
    client = TelegramClient("telethon_session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    for pack_name in PACKS:
        print(f"\n{'='*50}")
        print(f"Pack: {pack_name}")
        print(f"{'='*50}")
        try:
            sticker_set = await client(GetStickerSetRequest(
                stickerset=InputStickerSetShortName(short_name=pack_name),
                hash=0,
            ))
            for doc in sticker_set.documents:
                emoji = ""
                for attr in doc.attributes:
                    if hasattr(attr, "alt"):
                        emoji = attr.alt
                print(f"  {emoji}  →  emoji_id={doc.id}")
        except Exception as e:
            print(f"  Error: {e}")

    await client.disconnect()


asyncio.run(main())
