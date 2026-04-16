"""
Telegram auto-reply for first-time DMs.

Sends a hello message the first time a new user messages you in a private chat.
Uses Telethon (MTProto) with your personal account.

Designed to run on Railway / any container host:
  - Uses StringSession (no session file needed) -> login via TG_SESSION_STRING env
  - Persists greeted-user list to /data if available (Railway volume), else ./
  - Logs to stdout

Local first-time setup: run login.py once to generate TG_SESSION_STRING.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import User

# Optional: load .env only when running locally
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        sys.stderr.write(f"ERROR: env var {name} is required\n")
        sys.exit(1)
    return val


API_ID = int(_require("TG_API_ID"))
API_HASH = _require("TG_API_HASH")
SESSION_STRING = _require("TG_SESSION_STRING")

HELLO_MESSAGE = os.environ.get(
    "TG_HELLO_MESSAGE",
    "Hey! 👋 Thanks for reaching out — this is an automated first-time hello. "
    "I'll get back to you personally as soon as I can.",
)
SKIP_IF_YOU_MESSAGED_FIRST = (
    os.environ.get("TG_SKIP_IF_YOU_MESSAGED_FIRST", "true").lower() == "true"
)
IGNORE_BOTS = os.environ.get("TG_IGNORE_BOTS", "true").lower() == "true"
IGNORE_CONTACTS = os.environ.get("TG_IGNORE_CONTACTS", "true").lower() == "true"

# Railway persistent volume goes to /data; fall back to local dir.
DATA_DIR = Path("/data") if Path("/data").is_dir() and os.access("/data", os.W_OK) else Path(__file__).parent
STATE_FILE = DATA_DIR / "greeted_users.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("auto_reply")


def load_greeted() -> set[int]:
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()))
        except json.JSONDecodeError:
            log.warning("greeted_users.json corrupt, starting fresh")
    return set()


def save_greeted(greeted: set[int]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(sorted(greeted)))


greeted_users: set[int] = load_greeted()
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


async def has_prior_history(user_id: int, current_msg_id: int) -> bool:
    async for msg in client.iter_messages(user_id, limit=2):
        if msg.id != current_msg_id:
            return True
    return False


async def i_messaged_first(user_id: int) -> bool:
    async for msg in client.iter_messages(user_id, limit=20, reverse=True):
        return bool(msg.out)
    return False


@client.on(events.NewMessage(incoming=True))
async def handler(event: events.NewMessage.Event) -> None:
    if not event.is_private:
        return

    sender = await event.get_sender()
    if not isinstance(sender, User):
        return
    if sender.is_self:
        return
    if IGNORE_BOTS and sender.bot:
        return
    if IGNORE_CONTACTS and sender.contact:
        return
    if sender.id == 777000:
        return

    if sender.id in greeted_users:
        return

    if await has_prior_history(sender.id, event.message.id):
        greeted_users.add(sender.id)
        save_greeted(greeted_users)
        log.info("Skipping %s (prior history exists)", sender.id)
        return

    if SKIP_IF_YOU_MESSAGED_FIRST and await i_messaged_first(sender.id):
        greeted_users.add(sender.id)
        save_greeted(greeted_users)
        log.info("Skipping %s (you messaged first)", sender.id)
        return

    try:
        await event.reply(HELLO_MESSAGE)
        greeted_users.add(sender.id)
        save_greeted(greeted_users)
        name = sender.username or sender.first_name or str(sender.id)
        log.info("Greeted new DM from @%s (id=%s)", name, sender.id)
    except Exception as exc:  # noqa: BLE001
        log.exception("Failed to greet %s: %s", sender.id, exc)


async def main() -> None:
    await client.connect()
    if not await client.is_user_authorized():
        log.error("Session string is invalid or expired. Re-run login.py to generate a new one.")
        sys.exit(1)
    me = await client.get_me()
    log.info(
        "Logged in as @%s (id=%s). State file: %s. Waiting for new DMs...",
        me.username or me.first_name, me.id, STATE_FILE,
    )
    log.info("Already-greeted users tracked: %d", len(greeted_users))
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
