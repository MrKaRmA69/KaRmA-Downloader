# ⚠️ NOTICE: This repository is for personal educational purposes only. It is a study of API integration (Telethon/yt-dlp) and Python asynchronous programming. It is not intended to bypass platform security or violate Copyright Laws.

# KaRmA Integration Framework

An asynchronous Python framework for managing and archiving media metadata from various platforms via `Telethon`. This project is a technical study of the `yt-dlp` and `instagrapi` engines for personal data management.

## Features

* **Multi-Protocol Support:** Researching metadata extraction for various platforms via `yt-dlp`.
* **Session Handling:** Implementation of fallback logic using `instagrapi`.
* **Asynchronous Delivery:** Direct transmission of processed data to your private Telegram storage.
* **Environment Ready:** Fully modular configuration via `.env` file.

## Requirements

- Python 3.10+
- A Telegram API token from @BotFather

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/MrKaRmA69/KaRmA-Downloader.git
cd KaRmA-Downloader
```

2. **Setup:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Create .env (see .env.example):**
```bash
cp .env.example .env
```

Edit `.env` and set:
- `BOT_TOKEN` (required)
- `IG_USER` / `IG_PASS` (optional)

## Run

```bash
python bot.py
```

## Usage

1. Open your instance in Telegram.
2. Initialize with `/start`.
3. Provide a URL to media you personally own or have permission to archive.
4. The system processes the request and mirrors the file to your chat.

## Configuration

These parameters are managed via `.env`:

- `BOT_TOKEN`: Your private API token.
- `IG_USER` / `IG_PASS`: Optional session credentials.
- `TG_MAX_MB`: Maximum file size threshold (default 49.0).
- `IG_PROXY` / `YTDLP_PROXY`: Proxy DSN for network research.
- `YTDLP_COOKIES_FILE`: Path to a local cookies file for authenticated requests.

## Notes / Troubleshooting

- Authentication challenges may occur during login. Use a saved session flow or rely on standard library defaults.
- If network restrictions occur, utilize the `IG_PROXY` or `YTDLP_PROXY` settings.
- System performance may vary based on site-specific rate limits or geo-restrictions.

## Security

- **Strict Exclusion:** Never commit `.env` or session files. This repository uses `.gitignore` to prevent credential leakage.
- **Rotation:** If credentials are compromised, rotate them immediately via the respective platform providers.

## Legal

Users are strictly responsible for complying with the Terms of Service of any platforms accessed. This tool is for personal archival of content you have the legal right to access.
