"""
Run this ONCE on your local machine to generate a TG_SESSION_STRING.

Usage:
  1. pip install -r requirements.txt
  2. Put your TG_API_ID and TG_API_HASH in .env (or export them)
  3. python login.py
  4. Enter phone number, login code, and 2FA password (if enabled)
  5. Copy the printed session string into Railway as TG_SESSION_STRING

Keep the session string SECRET — anyone with it has full access to your account.
"""

import asyncio
import os
import sys

from telethon import TelegramClient
from telethon.sessions import StringSession

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def main() -> None:
    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    if not api_id or not api_hash:
        sys.stderr.write("Set TG_API_ID and TG_API_HASH in .env or environment first.\n")
        sys.exit(1)

    print("Starting login. You'll be asked for your phone number and the code Telegram sends you.\n")
    async with TelegramClient(StringSession(), int(api_id), api_hash) as client:
        me = await client.get_me()
        session_string = client.session.save()
        print("\n" + "=" * 70)
        print(f"Logged in as @{me.username or me.first_name} (id={me.id})")
        print("=" * 70)
        print("\nYour TG_SESSION_STRING (paste into Railway as an env var):\n")
        print(session_string)
        print("\n" + "=" * 70)
        print("⚠️  Keep this string secret. Anyone with it can access your account.")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
