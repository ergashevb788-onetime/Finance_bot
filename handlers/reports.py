"""Monthly reports handler."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

from database.db import get_session
from services.report_service import ReportService
from utils.keyboards import (
    main_menu_keyboard,
    previous_months_keyboard,
    report_keyboard,
)
from utils.scheduler import current_month

logger = logging.getLogger(__name__)


async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the current month's report."""
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    year, month = current_month()

    async with get_session() as session:
        svc = ReportService(session)
        transition_msg = await svc.check_month_transition(user_id)
        if transition_msg:
            await update.message.reply_text(transition_msg, parse_mode="Markdown")

        report_text = await svc.build_report(user_id, year, month)

    await update.message.reply_text(
        report_text,
        parse_mode="Markdown",
        reply_markup=report_keyboard(),
    )


async def report_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle report inline keyboard callbacks."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
    await query.answer()

    user_id = update.effective_user.id
    data: str = query.data or ""

    if data == "report_prev_months":
        async with get_session() as session:
            svc = ReportService(session)
            months = await svc.get_available_months(user_id)

        if not months:
            await query.edit_message_text(
                "📅 No previous months data available.",
                reply_markup=report_keyboard(),
            )
            return

        await query.edit_message_text(
            "📅 *Select a month:*",
            parse_mode="Markdown",
            reply_markup=previous_months_keyboard(months),
        )

    elif data.startswith("report_month:"):
        _, year_str, month_str = data.split(":")
        year, month = int(year_str), int(month_str)

        async with get_session() as session:
            svc = ReportService(session)
            report_text = await svc.build_report(user_id, year, month)

        await query.edit_message_text(
            report_text,
            parse_mode="Markdown",
            reply_markup=report_keyboard(),
        )

    elif data == "report_back":
        year, month = current_month()
        async with get_session() as session:
            svc = ReportService(session)
            report_text = await svc.build_report(user_id, year, month)

        await query.edit_message_text(
            report_text,
            parse_mode="Markdown",
            reply_markup=report_keyboard(),
        )

    elif data == "report_main_menu":
        await query.edit_message_text("🏠 Returning to main menu...")
