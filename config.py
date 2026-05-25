"""Application configuration loaded from environment variables."""

import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration class."""

    # Telegram
    BOT_TOKEN: str = os.environ["BOT_TOKEN"]
    WEBHOOK_URL: str = os.environ["WEBHOOK_URL"]
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database
    DATABASE_URL: str = os.environ["DATABASE_URL"]

    # App
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tashkent")
    TZ: ZoneInfo = ZoneInfo(TIMEZONE)

    # Default currency
    DEFAULT_CURRENCY: str = "UZS"

    # Webhook path
    WEBHOOK_PATH: str = "/webhook"
    HEALTH_PATH: str = "/health"


config = Config()
