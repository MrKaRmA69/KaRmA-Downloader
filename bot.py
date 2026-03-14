import asyncio
import logging
import os
import re
import shutil
import threading
from pathlib import Path
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, LoginRequired
from yt_dlp import YoutubeDL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
IG_USER = os.getenv("IG_USER")
IG_PASS = os.getenv("IG_PASS")
TG_MAX_MB = float(os.getenv("TG_MAX_MB", "49.0"))
IG_PROXY = os.getenv("IG_PROXY")
YTDLP_PROXY = os.getenv("YTDLP_PROXY")
YTDLP_COOKIES_FILE = os.getenv("YTDLP_COOKIES_FILE")

if not TOKEN:
    raise ValueError("BOT_TOKEN not set in .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

YDL_OPTS_BASE: dict = {
    "quiet": True,
    "no_warnings": True,
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "noplaylist": True,
    "continuedl": True,
    "retries": 10,
    "restrictfilenames": True,
    "merge_output_format": "mp4",
}

_ig_client_lock = threading.Lock()
_ig_client: Client | None = None
_ig_client_error: str | None = None
_cookies_file: Path | None = None

if YTDLP_COOKIES_FILE:
    candidate = Path(YTDLP_COOKIES_FILE).expanduser()
    if candidate.exists() and candidate.is_file():
        _cookies_file = candidate


def _get_instagram_client() -> Client:
    global _ig_client, _ig_client_error
    with _ig_client_lock:
        if _ig_client is not None:
            return _ig_client
        if _ig_client_error is not None:
            raise RuntimeError(_ig_client_error)

        client = Client()
        if IG_PROXY:
            client.set_proxy(IG_PROXY)
        if IG_USER and IG_PASS:
            try:
                client.login(IG_USER, IG_PASS)
                logger.info("Instagram login successful")
            except ChallengeRequired:
                _ig_client_error = (
                    "Instagram login challenge required. "
                    "Complete login manually / provide a session, or omit IG_USER/IG_PASS."
                )
                raise RuntimeError(_ig_client_error)
            except Exception as e:
                _ig_client_error = f"Instagram login failed: {e}"
                raise RuntimeError(_ig_client_error)

        _ig_client = client
        return client


def _extract_urls(text: str) -> list[str]:
    urls = re.findall(r"(https?://\S+)", text)
    cleaned: list[str] = []
    for url in urls:
        url = url.strip().strip("()[]{}<>\"'")
        url = url.rstrip(".,;:!?")
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            cleaned.append(url)
    return cleaned


def _display_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or ""
    path = parsed.path or ""
    if len(path) > 64:
        path = path[:61] + "..."
    return f"{host}{path}"


def _download_with_ytdlp(url: str, request_dir: Path) -> list[Path]:
    ydl_opts = dict(YDL_OPTS_BASE)
    ydl_opts["outtmpl"] = str(request_dir / "%(title).80B_%(id)s.%(ext)s")
    if YTDLP_PROXY:
        ydl_opts["proxy"] = YTDLP_PROXY
    if _cookies_file is not None:
        ydl_opts["cookiefile"] = str(_cookies_file)
    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
    return sorted([p for p in request_dir.iterdir() if p.is_file()])


def _download_with_instagrapi(url: str, request_dir: Path) -> list[Path]:
    cl = _get_instagram_client()
    parsed = urlparse(url)
    if "instagram.com" not in (parsed.netloc or ""):
        return []

    if parsed.path.startswith("/stories/"):
        path = cl.story_download_by_url(url, folder=request_dir)
        return [Path(path)]

    pk: int | None = None
    try:
        pk = cl.media_pk_from_url(url)
    except Exception:
        pk = None

    if pk is None:
        return []

    media = cl.media_info(pk)
    if media.media_type == 1:
        return [Path(cl.photo_download(pk, folder=request_dir))]
    if media.media_type == 2:
        return [Path(cl.video_download(pk, folder=request_dir))]
    if media.media_type == 8:
        return [Path(p) for p in cl.album_download(pk, folder=request_dir)]
    return []


async def _safe_delete_message(msg: types.Message) -> None:
    try:
        await msg.delete()
    except Exception:
        return


def _failure_hint(url: str, ytdlp_error: str | None, ig_error: str | None) -> str:
    if "instagram.com" in url:
        if ig_error and ("blacklist" in ig_error.lower() or "ip address" in ig_error.lower()):
            return (
                "Instagram blocked login from this IP. Try running the bot from another network/IP "
                "(mobile hotspot/VPN/VPS) or set `IG_PROXY`."
            )
        if ytdlp_error and ("cookie" in ytdlp_error.lower() or "empty media response" in ytdlp_error.lower()):
            return (
                "Instagram requires login/cookies for this link. Export browser cookies and set "
                "`YTDLP_COOKIES_FILE=/path/to/cookies.txt` (or try another IP)."
            )
        if ytdlp_error or ig_error:
            return "Instagram blocked this request. Try another IP, or provide cookies/proxy."
        return "Instagram blocked this request."

    if ytdlp_error:
        short = ytdlp_error.replace("\n", " ")
        if len(short) > 160:
            short = short[:157] + "..."
        return f"Downloader error: {short}"
    return "Unknown error."


@dp.message(CommandStart())
async def start(message: types.Message):
    logger.info(f"/start from chat_id={message.chat.id} user_id={getattr(message.from_user, 'id', None)}")
    await message.answer(
        "Send an Instagram link (reel/post/story) or YouTube link.\n"
        "I’ll try to download and send it back."
    )


@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return
    if message.text.lstrip().startswith("/"):
        return

    urls = _extract_urls(message.text)
    if not urls:
        await message.reply("No link found. Send a valid URL.")
        return

    status = await message.reply("Processing…")

    for idx, url in enumerate(urls, start=1):
        request_dir = DOWNLOAD_DIR / f"{message.chat.id}_{message.message_id}_{idx}"
        request_dir.mkdir(parents=True, exist_ok=True)
        try:
            await status.edit_text(f"Processing {idx}/{len(urls)}: {_display_url(url)}")

            files: list[Path] = []
            ytdlp_error: str | None = None
            ig_error: str | None = None
            try:
                files = await asyncio.to_thread(_download_with_ytdlp, url, request_dir)
            except Exception as e:
                ytdlp_error = str(e)
                logger.info(f"yt-dlp failed for {url}: {ytdlp_error}")

            if not files:
                try:
                    files = await asyncio.to_thread(_download_with_instagrapi, url, request_dir)
                except LoginRequired:
                    files = []
                except Exception as e:
                    ig_error = str(e)
                    logger.info(f"instagrapi failed for {url}: {ig_error}")
                    files = []

            if not files:
                await message.reply(f"Couldn’t download: {url}\n{_failure_hint(url, ytdlp_error, ig_error)}")
                continue

            for file_path in files:
                if not file_path.exists():
                    continue
                size_mb = file_path.stat().st_size / (1024**2)
                if size_mb > TG_MAX_MB:
                    await message.reply(f"File too big to send ({size_mb:.1f} MB): {file_path.name}")
                    continue
                try:
                    if file_path.suffix.lower() in {".mp4", ".mov"}:
                        await message.reply_video(FSInputFile(file_path))
                    else:
                        await message.reply_document(FSInputFile(file_path))
                except Exception as e:
                    logger.error(f"Send failed for {file_path}: {e}")
                    await message.reply(f"Failed to send {file_path.name}.")
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            await message.reply(f"Error for {url}: {str(e)[:150]}")
        finally:
            shutil.rmtree(request_dir, ignore_errors=True)

    await _safe_delete_message(status)


async def main():
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
