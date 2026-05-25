"""Money Lent conversation handler."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from database.db import get_session
from services.lent_service import LentService
from services.report_service import ReportService
from utils.keyboards import (
    active_lent_keyboard,
    confirm_delete_keyboard,
    lent_detail_keyboard,
    main_menu_keyboard,
    money_lent_menu_keyboard,
)
from utils.parser import format_amount, parse_lent_entry
from utils.scheduler import current_date

logger = logging.getLogger(__name__)

# States
LENT_MENU = 0
LENT_NEW_ENTRY = 1
LENT_EDIT_ENTRY = 2

CTX_EDIT_ID = "lent_edit_id"


async def money_lent_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point — show money lent submenu."""
    if not update.effective_user or not update.message:
        return ConversationHandler.END

    user_id = update.effective_user.id
    async with get_session() as session:
        report_svc = ReportService(session)
        transition_msg = await report_svc.check_month_transition(user_id)
    if transition_msg:
        await update.message.reply_text(transition_msg, parse_mode="Markdown")

    await update.message.reply_text(
        "💵 *Money Lent*\n\nChoose an option:",
        parse_mode="Markdown",
        reply_markup=money_lent_menu_keyboard(),
    )
    return LENT_MENU


async def lent_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Route user's menu choice."""
    if not update.message or not update.message.text:
        return LENT_MENU
    text = update.message.text.strip()

    if text == "🏠 Main Menu":
        await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    if text == "➕ New Entry":
        await update.message.reply_text(
            "✏️ Enter lent details:\n\n"
            "<code>Tohirmalik 29k Osh</code>\n"
            "<code>Aziz 100$ House</code>\n"
            "<code>Sardor 250000</code>\n\n"
            "Format: <b>Name Amount [note]</b>",
            parse_mode="HTML",
        )
        return LENT_NEW_ENTRY

    if text == "📋 Active":
        await show_active(update, context)
        return LENT_MENU

    if text == "📜 History":
        await show_history(update, context)
        return LENT_MENU

    return LENT_MENU


async def show_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display active lent entries."""
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    async with get_session() as session:
        svc = LentService(session)
        entries = await svc.get_active(user_id)

    if not entries:
        await update.message.reply_text("📋 No active money lent entries.")
        return

    await update.message.reply_text(
        "📋 *Active Money Lent:*",
        parse_mode="Markdown",
        reply_markup=active_lent_keyboard(entries),
    )


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display returned entries."""
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id
    async with get_session() as session:
        svc = LentService(session)
        entries = await svc.get_history(user_id)

    if not entries:
        await update.message.reply_text("📜 No history yet.")
        return

    lines = ["📜 *History:*\n"]
    for e in entries:
        returned_str = e.returned_date.strftime("%d %b %Y") if e.returned_date else "?"
        note_str = f" | {e.note}" if e.note else ""
        lines.append(
            f"✅ {e.person_name} — {format_amount(float(e.amount), e.currency)}{note_str}\n"
            f"   📅 Lent: {e.lent_date.strftime('%d %b %Y')} → Returned: {returned_str}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def new_entry_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parse and save a new lent entry."""
    if not update.effective_user or not update.message or not update.message.text:
        return LENT_NEW_ENTRY

    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "🏠 Main Menu":
        await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    parsed = parse_lent_entry(text)
    if parsed is None:
        await update.message.reply_text(
            "❌ Could not parse. Use format:\n"
            "<code>Name Amount [note]</code>\n\n"
            "<code>Tohirmalik 29k Osh</code>",
            parse_mode="HTML",
        )
        return LENT_NEW_ENTRY

    today = current_date()
    async with get_session() as session:
        svc = LentService(session)
        entry = await svc.add_entry(user_id=user_id, parsed=parsed, lent_date=today)

    note_str = f"\n📝 {parsed.note}" if parsed.note else ""
    await update.message.reply_text(
        f"✅ *Saved!*\n\n"
        f"👤 {parsed.person_name}\n"
        f"💰 {format_amount(parsed.amount, parsed.currency)}{note_str}\n"
        f"📅 {today.strftime('%d %b %Y')}",
        parse_mode="Markdown",
        reply_markup=money_lent_menu_keyboard(),
    )
    return LENT_MENU


async def edit_entry_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parse and apply edit to a lent entry."""
    if not update.effective_user or not update.message or not update.message.text:
        return LENT_EDIT_ENTRY

    text = update.message.text.strip()
    user_id = update.effective_user.id
    entry_id: int = context.user_data.get(CTX_EDIT_ID, 0)

    if text == "🏠 Main Menu":
        await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    parsed = parse_lent_entry(text)
    if parsed is None:
        await update.message.reply_text(
            "❌ Could not parse. Use: <code>Name Amount [note]</code>",
            parse_mode="HTML",
        )
        return LENT_EDIT_ENTRY

    async with get_session() as session:
        svc = LentService(session)
        updated = await svc.update_entry(entry_id=entry_id, user_id=user_id, parsed=parsed)

    if updated:
        await update.message.reply_text(
            f"✅ Updated: *{parsed.person_name}* — {format_amount(parsed.amount, parsed.currency)}",
            parse_mode="Markdown",
            reply_markup=money_lent_menu_keyboard(),
        )
    else:
        await update.message.reply_text("❌ Entry not found.", reply_markup=money_lent_menu_keyboard())

    return LENT_MENU


# ---------------------------------------------------------------------------
# Inline callback handlers (outside ConversationHandler)
# ---------------------------------------------------------------------------

async def lent_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle lent inline keyboard callbacks."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
    await query.answer()

    user_id = update.effective_user.id
    data: str = query.data or ""

    if data.startswith("lent_view:"):
        entry_id = int(data.split(":")[1])
        await _show_lent_detail(query, user_id, entry_id)

    elif data.startswith("lent_returned:"):
        entry_id = int(data.split(":")[1])
        today = current_date()
        async with get_session() as session:
            svc = LentService(session)
            ok = await svc.mark_returned(entry_id, user_id, today)
        if ok:
            await query.edit_message_text(
                f"✅ Marked as returned on {today.strftime('%d %b %Y')}."
            )
        else:
            await query.edit_message_text("❌ Could not update entry.")

    elif data.startswith("lent_delete:"):
        entry_id = int(data.split(":")[1])
        await query.edit_message_text(
            "⚠️ Are you sure you want to delete this entry?",
            reply_markup=confirm_delete_keyboard(entry_id),
        )

    elif data.startswith("lent_confirm_delete:"):
        entry_id = int(data.split(":")[1])
        async with get_session() as session:
            svc = LentService(session)
            ok = await svc.delete_entry(entry_id, user_id)
        if ok:
            await query.edit_message_text("🗑 Entry deleted.")
        else:
            await query.edit_message_text("❌ Could not delete.")

    elif data.startswith("lent_edit:"):
        entry_id = int(data.split(":")[1])
        context.user_data[CTX_EDIT_ID] = entry_id
        await query.edit_message_text(
            "✏️ Enter updated details:\n<code>Name Amount [note]</code>",
            parse_mode="HTML",
        )

    elif data == "lent_active_back":
        async with get_session() as session:
            svc = LentService(session)
            entries = await svc.get_active(user_id)
        if entries:
            await query.edit_message_text(
                "📋 *Active Money Lent:*",
                parse_mode="Markdown",
                reply_markup=active_lent_keyboard(entries),
            )
        else:
            await query.edit_message_text("📋 No active entries.")


async def _show_lent_detail(query, user_id: int, entry_id: int) -> None:
    async with get_session() as session:
        svc = LentService(session)
        entry = await svc.get_entry(entry_id, user_id)

    if not entry:
        await query.edit_message_text("❌ Entry not found.")
        return

    note_str = f"\n📝 Note: {entry.note}" if entry.note else ""
    text = (
        f"👤 *{entry.person_name}*\n"
        f"💰 {format_amount(float(entry.amount), entry.currency)}{note_str}\n"
        f"📅 Lent: {entry.lent_date.strftime('%d %b %Y')}"
    )
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=lent_detail_keyboard(entry_id),
    )


def build_lent_conversation() -> ConversationHandler:
    """Build and return the money lent ConversationHandler."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💵 Money Lent$"), money_lent_menu),
        ],
        states={
            LENT_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, lent_menu_router),
            ],
            LENT_NEW_ENTRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_entry_input),
            ],
            LENT_EDIT_ENTRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_entry_input),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^🏠 Main Menu$"), _lent_fallback),
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
    )


async def _lent_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
    return ConversationHandler.END
