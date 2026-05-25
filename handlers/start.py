"""Start handler and main menu routing."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from database.db import get_session
from database.repositories import UserRepository
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — register user and show main menu."""
    if not update.effective_user or not update.message:
        return

    tg_user = update.effective_user
    async with get_session() as session:
        repo = UserRepository(session)
        await repo.upsert(
            user_id=tg_user.id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            username=tg_user.username,
        )

    await update.message.reply_text(
        f"👋 Welcome, {tg_user.first_name}!\n\nChoose an option:",
        reply_markup=main_menu_keyboard(),
    )
    logger.info("User %s started the bot", tg_user.id)


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return user to main menu."""
    if not update.message:
        return
    await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
