"""Expenses conversation handler."""

from __future__ import annotations

import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from database.db import get_session
from services.expense_service import ExpenseService
from services.report_service import ReportService
from utils.keyboards import (
    BUILTIN_CATEGORIES,
    expense_categories_keyboard,
    main_menu_keyboard,
    manage_categories_keyboard,
)
from utils.parser import format_amount, parse_amount
from utils.scheduler import current_date

logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_CATEGORY = 0
ENTERING_AMOUNT = 1
ADDING_CATEGORY_NAME = 2

# Context keys
CTX_CATEGORY = "expense_category"
CTX_CUSTOM_CATS = "expense_custom_cats"

# All built-in category labels
BUILTIN_LABELS = {f"{emoji} {name}" for emoji, name in BUILTIN_CATEGORIES}


async def _get_categories(user_id: int):
    async with get_session() as session:
        svc = ExpenseService(session)
        return await svc.get_custom_categories(user_id)


async def expenses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point — show category keyboard."""
    if not update.effective_user or not update.message:
        return ConversationHandler.END

    user_id = update.effective_user.id

    # Check month transition
    async with get_session() as session:
        report_svc = ReportService(session)
        transition_msg = await report_svc.check_month_transition(user_id)

    if transition_msg:
        await update.message.reply_text(transition_msg, parse_mode="Markdown")

    custom_cats = await _get_categories(user_id)
    await update.message.reply_text(
        "💸 *Expenses*\n\nChoose a category:",
        parse_mode="Markdown",
        reply_markup=expense_categories_keyboard(custom_cats),
    )
    return CHOOSING_CATEGORY


async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User selected a category."""
    if not update.effective_user or not update.message or not update.message.text:
        return CHOOSING_CATEGORY

    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "🏠 Main Menu":
        await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    if text == "➕ Add Category":
        await update.message.reply_text(
            "✏️ Enter the name for your new category:\n(e.g. <code>Gym</code> or <code>🎮 Gaming</code>)",
            parse_mode="HTML",
        )
        return ADDING_CATEGORY_NAME

    if text == "⚙ Manage Categories":
        custom_cats = await _get_categories(user_id)
        if not custom_cats:
            await update.message.reply_text("You have no custom categories to manage.")
            return CHOOSING_CATEGORY
        await update.message.reply_text(
            "🗑 Tap a category to delete it:",
            reply_markup=manage_categories_keyboard(custom_cats),
        )
        return CHOOSING_CATEGORY

    # Validate it's a known category
    custom_cats = await _get_categories(user_id)
    custom_labels = {f"{c.emoji} {c.name}" for c in custom_cats}
    all_labels = BUILTIN_LABELS | custom_labels

    if text not in all_labels:
        await update.message.reply_text("Please choose a category from the keyboard.")
        return CHOOSING_CATEGORY

    context.user_data[CTX_CATEGORY] = text
    await update.message.reply_text(
        f"📂 Category: *{text}*\n\n"
        "Enter amount and optional note:\n"
        "<code>29000 Osh</code>\n"
        "<code>150000 Grocery</code>\n"
        "<code>100$ Medicine</code>",
        parse_mode="HTML",
    )
    return ENTERING_AMOUNT


async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User typed an amount (and optional note)."""
    if not update.effective_user or not update.message or not update.message.text:
        return ENTERING_AMOUNT

    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "🏠 Main Menu":
        await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    parsed = parse_amount(text)
    if parsed is None:
        await update.message.reply_text(
            "❌ Could not parse the amount. Try:\n"
            "<code>29000</code>, <code>29k</code>, <code>1.5m</code>, <code>100$</code>",
            parse_mode="HTML",
        )
        return ENTERING_AMOUNT

    category: str = context.user_data.get(CTX_CATEGORY, "📦 Other")
    today = current_date()

    async with get_session() as session:
        svc = ExpenseService(session)
        expense = await svc.add_expense(
            user_id=user_id,
            category=category,
            parsed=parsed,
            expense_date=today,
        )

    # Confirmation
    note_str = f"\n📝 Note: {parsed.note}" if parsed.note else ""
    confirmation = (
        f"✅ *Saved!*\n\n"
        f"📂 {category}\n"
        f"💰 {format_amount(parsed.amount, parsed.currency)}{note_str}\n"
        f"📅 {today.strftime('%d %b %Y')}"
    )

    # Reopen category keyboard
    custom_cats = await _get_categories(user_id)
    await update.message.reply_text(
        confirmation,
        parse_mode="Markdown",
        reply_markup=expense_categories_keyboard(custom_cats),
    )
    return CHOOSING_CATEGORY


async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User typed a name for a new custom category."""
    if not update.effective_user or not update.message or not update.message.text:
        return ADDING_CATEGORY_NAME

    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "🏠 Main Menu":
        await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    # Extract emoji if provided
    emoji = "📌"
    name = text
    # Simple check: if first char is emoji-ish, split
    if len(text) > 1 and not text[0].isalnum():
        parts = text.split(None, 1)
        if len(parts) == 2:
            emoji = parts[0]
            name = parts[1]

    async with get_session() as session:
        svc = ExpenseService(session)
        cat = await svc.add_custom_category(user_id=user_id, name=name, emoji=emoji)

    if cat is None:
        await update.message.reply_text(f"⚠️ Category '{name}' already exists.")
    else:
        await update.message.reply_text(f"✅ Category *{emoji} {name}* added!", parse_mode="Markdown")

    custom_cats = await _get_categories(user_id)
    await update.message.reply_text(
        "Choose a category:",
        reply_markup=expense_categories_keyboard(custom_cats),
    )
    return CHOOSING_CATEGORY


async def manage_categories_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle category deletion inline callbacks."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
    await query.answer()

    user_id = update.effective_user.id
    data: str = query.data or ""

    if data.startswith("del_cat:"):
        cat_id = int(data.split(":")[1])
        async with get_session() as session:
            svc = ExpenseService(session)
            deleted = await svc.delete_custom_category(cat_id, user_id)

        if deleted:
            await query.answer("✅ Category deleted", show_alert=False)
        else:
            await query.answer("❌ Could not delete", show_alert=True)

        # Refresh keyboard
        async with get_session() as session:
            svc = ExpenseService(session)
            custom_cats = await svc.get_custom_categories(user_id)

        if custom_cats:
            await query.edit_message_reply_markup(reply_markup=manage_categories_keyboard(custom_cats))
        else:
            await query.edit_message_text("✅ No more custom categories.")

    elif data == "manage_cats_done":
        await query.edit_message_text("✅ Done managing categories.")


def build_expense_conversation() -> ConversationHandler:
    """Build and return the expense ConversationHandler."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💸 Expenses$"), expenses_menu),
        ],
        states={
            CHOOSING_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_chosen),
            ],
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_entered),
            ],
            ADDING_CATEGORY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^🏠 Main Menu$"), main_menu_handler_fallback),
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
    )


async def main_menu_handler_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text("🏠 Main Menu", reply_markup=main_menu_keyboard())
    return ConversationHandler.END
