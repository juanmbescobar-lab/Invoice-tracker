from pathlib import Path

from telegram import Bot

from src.core.config import settings


def get_bot() -> Bot:
    """Create a Telegram bot instance."""
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured.")
    return Bot(token=settings.telegram_bot_token)


async def send_message(text: str) -> None:
    """Send a text message to the configured chat."""
    bot = get_bot()
    async with bot:
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=text,
        )


async def send_pdf(file_path: str, caption: str = "") -> None:
    """Send a PDF file to the configured chat."""
    bot = get_bot()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    async with bot:
        with open(path, "rb") as pdf_file:
            await bot.send_document(
                chat_id=settings.telegram_chat_id,
                document=pdf_file,
                caption=caption,
            )
