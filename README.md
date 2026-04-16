# Telegram Auto-Reply for New DMs

Sends a one-time hello when a **brand-new person** DMs your personal Telegram account. Repeat messages from the same user are never greeted twice.

Built to deploy on **Railway** (or any container host) and run 24/7.

---

## How it works

- Uses [Telethon](https://docs.telethon.dev) (MTProto) logged into your **personal account** — bots can't receive DMs from strangers, so a user-account client is required.
- For every incoming private message, it checks:
  1. Is this a 1:1 private chat? (ignores groups/channels)
  2. Have I already greeted this user? (tracked in `greeted_users.json`)
  3. Is there any prior message history with them? (if yes → not new)
  4. Did I DM them first? (if yes → skip)
  5. Is it a bot / Telegram contact / service account? (skippable)
- If all pass → send hello, remember their user ID, never greet again.

---

## Deploying on Railway

### 1. Get Telegram API credentials
- Go to https://my.telegram.org/apps → log in with your phone
- Create an app (any name), copy **api_id** and **api_hash**

### 2. Generate your session string (do this ONCE, locally)

```bash
git clone https://github.com/dandysuper/telegram-auto-reply.git
cd telegram-auto-reply
pip install -r requirements.txt
cp .env.example .env
# edit .env: fill in TG_API_ID and TG_API_HASH
python login.py
```

Enter your phone, the login code Telegram sends you, and your 2FA password if you have one. The script will print a long `TG_SESSION_STRING`. Copy it.

> ⚠️ **Keep the session string secret.** Anyone with it has full access to your Telegram account. Never commit it to git.

### 3. Deploy to Railway

1. Push this repo to your GitHub (it already will be, at `dandysuper/telegram-auto-reply`).
2. On [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo** → pick `telegram-auto-reply`.
3. Railway auto-detects the `Dockerfile`.
4. In the service → **Variables** tab, add:
   - `TG_API_ID`
   - `TG_API_HASH`
   - `TG_SESSION_STRING` (the one from step 2)
   - (optional) `TG_HELLO_MESSAGE`, etc.
5. (Recommended) Service → **Settings → Volumes → Add Volume** → mount path `/data`. This persists the greeted-users list across redeploys.
6. Deploy. Check logs — you should see `Logged in as @yourname ... Waiting for new DMs...`

That's it. Railway keeps it running forever.

---

## Config (env vars)

| Var | Required | Default | Purpose |
|---|---|---|---|
| `TG_API_ID` | ✅ | — | From my.telegram.org/apps |
| `TG_API_HASH` | ✅ | — | From my.telegram.org/apps |
| `TG_SESSION_STRING` | ✅ | — | Generated locally via `login.py` |
| `TG_HELLO_MESSAGE` | | friendly default | The auto-reply text |
| `TG_SKIP_IF_YOU_MESSAGED_FIRST` | | `true` | Don't greet people you DM'd first |
| `TG_IGNORE_BOTS` | | `true` | Skip bot senders |
| `TG_IGNORE_CONTACTS` | | `true` | Skip people in your Telegram contacts |

---

## Running locally (optional)

```bash
pip install -r requirements.txt
# put everything in .env including TG_SESSION_STRING
python auto_reply.py
```

---

## Files

| File | Purpose |
|---|---|
| `auto_reply.py` | The worker — runs 24/7 |
| `login.py` | One-time local helper to generate `TG_SESSION_STRING` |
| `Dockerfile` | Container image used by Railway |
| `railway.toml` | Railway build/deploy config |
| `requirements.txt` | Python deps |
| `.env.example` | Template — copy to `.env` locally (never commit `.env`) |

---

## Safety notes

- The session string = full account access. Treat like a password. Regenerate via `login.py` if leaked (and then remove the old "Telethon" device at Settings → Devices in Telegram).
- This script sends **at most one message per unique user, ever**. That's well within Telegram's rate limits. Don't loosen this — spamming strangers can get your account flagged.
- All other events (groups, channels, bots, contacts, your own messages) are ignored.
