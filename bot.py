"""
Finance Tracker Telegram Bot
Entry point: webhook server + bot application.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import config
from database.db import close_db, init_db
from handlers.expenses import build_expense_conversation, manage_categories_callback
from handlers.money_lent import build_lent_conversation, lent_callback_handler
from handlers.reports import report_callback_handler, report_handler
from handlers.start import main_menu_handler, start_handler

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Build Telegram Application
# ---------------------------------------------------------------------------

def build_application() -> Application:
    """Construct and wire the bot application."""
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .updater(None)  # No polling — webhook only
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("menu", main_menu_handler))

    # Conversation handlers (order matters — more specific first)
    app.add_handler(build_expense_conversation())
    app.add_handler(build_lent_conversation())

    # Plain message handlers
    app.add_handler(MessageHandler(filters.Regex("^📊 Monthly Hisobot$"), report_handler))
    app.add_handler(MessageHandler(filters.Regex("^🏠 Main Menu$"), main_menu_handler))

    # Inline callback handlers
    app.add_handler(CallbackQueryHandler(manage_categories_callback, pattern="^(del_cat:|manage_cats_done)"))
    app.add_handler(CallbackQueryHandler(lent_callback_handler, pattern="^lent_"))
    app.add_handler(CallbackQueryHandler(report_callback_handler, pattern="^report_"))

    # Error handler
    async def error_handler(update: object, context: Any) -> None:
        logger.error("Unhandled exception: %s", context.error, exc_info=context.error)

    app.add_error_handler(error_handler)

    return app


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

bot_app: Application | None = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Startup and shutdown lifecycle."""
    global bot_app

    # Database
    await init_db()
    logger.info("Database initialized.")

    # Build bot
    bot_app = build_application()
    await bot_app.initialize()
    await bot_app.start()

    # Register webhook
    webhook_url = f"{config.WEBHOOK_URL.rstrip('/')}{config.WEBHOOK_PATH}"
    await bot_app.bot.set_webhook(
        url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    logger.info("Webhook registered: %s", webhook_url)

    yield

    # Shutdown
    logger.info("Shutting down...")
    await bot_app.stop()
    await bot_app.shutdown()
    await close_db()


web_app = FastAPI(title="Finance Tracker Bot", lifespan=lifespan)


@web_app.get(config.HEALTH_PATH)
async def health() -> dict:
    """Health check endpoint for Railway."""
    return {"status": "ok", "bot": "Finance Tracker"}


@web_app.post(config.WEBHOOK_PATH)
async def webhook(request: Request) -> Response:
    """Receive Telegram webhook updates."""
    if bot_app is None:
        return Response(status_code=503, content="Bot not ready")

    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return Response(status_code=200)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "bot:web_app",
        host="0.0.0.0",
        port=config.PORT,
        log_level="info",
    )
