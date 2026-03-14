# Telegram Media Downloader Bot

Telegram bot that downloads media from links you send it (YouTube + many sites via `yt-dlp`, with an Instagram fallback via `instagrapi`) and sends the file back in chat.

## Features

* **Multi-Platform:** Support for YouTube, Twitter, TikTok, and more via `yt-dlp`.
* **Instagram Specialist:** Dedicated fallback handling using `instagrapi`.
* **Fast Delivery:** Directly sends the media file back to your Telegram chat.
* **Environment Ready:** Easily configurable via `.env` file.
## Requirements

- Python 3.10+
- A Telegram bot token from @BotFather

1. **Clone the repository:**
```bash
   git clone [https://github.com/MrKaRmA69/KaRmA-Downloader.git](https://github.com/MrKaRmA69/KaRmA-Downloader.git)
   cd KaRmA-Downloader
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (see `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and set:

- `BOT_TOKEN` (required)
- `IG_USER` / `IG_PASS` (optional, improves Instagram access)

## Run

```bash
python bot.py
```

## Usage

1. Open your bot in Telegram
2. Send `/start`
3. Paste a YouTube / Instagram / other supported URL
4. The bot downloads and replies with the media file(s)

## Configuration

These are read from `.env`:

- `BOT_TOKEN` (required): Telegram bot token
- `IG_USER` (optional): Instagram username
- `IG_PASS` (optional): Instagram password
- `TG_MAX_MB` (optional, default `49.0`): Max file size (MB) the bot will attempt to send
- `IG_PROXY` (optional): Proxy DSN for Instagram requests (example: `socks5://user:pass@host:port`)
- `YTDLP_PROXY` (optional): Proxy for `yt-dlp` (example: `http://user:pass@host:port`)
- `YTDLP_COOKIES_FILE` (optional): Path to a `yt-dlp` cookies file (Netscape format)

## Notes / Troubleshooting

- Instagram may require a challenge/verification during login. If that happens, either complete it with a saved session flow, or remove `IG_USER`/`IG_PASS` and rely on `yt-dlp` where possible.
- If Instagram downloads fail with “requires cookies” or “empty media response”, export cookies from your browser and set `YTDLP_COOKIES_FILE`.
- If Instagram says your IP is blocked/blacklisted, run the bot from a different network/IP (or set `IG_PROXY` / `YTDLP_PROXY`).
- Some links may fail due to site restrictions, rate limits, private content, or geo blocks.
- If you deploy to a server, run behind a process manager (systemd, pm2, supervisor) so it restarts automatically.

## Security

- Never commit `.env` to git (this repo includes `.gitignore` entries for it).
- If a token/password is ever shared publicly, rotate it immediately (Telegram token in @BotFather; Instagram password in Instagram).

## Legal

Respect the Terms of Service for the sites you download from. You are responsible for how you use this bot.
