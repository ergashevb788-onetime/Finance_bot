"""Keyboard builders for the Finance Tracker Bot."""

from __future__ import annotations

from typing import Sequence

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from database.models import CustomCategory, MoneyLent
from utils.parser import format_amount

# ---------------------------------------------------------------------------
# Static categories (built-in)
# ---------------------------------------------------------------------------

BUILTIN_CATEGORIES: list[tuple[str, str]] = [
    ("🍔", "Food"),
    ("🍽", "Dine Out"),
    ("🏠", "House"),
    ("🚕", "Transport"),
    ("🛒", "Shopping"),
    ("💊", "Health"),
    ("📚", "Education"),
    ("🎁", "Gifts"),
    ("📦", "Other"),
]


# ---------------------------------------------------------------------------
# Main Menu
# ---------------------------------------------------------------------------

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Return the main menu reply keyboard."""
    return ReplyKeyboardMarkup(
        [
            ["💸 Expenses", "💵 Money Lent"],
            ["📊 Monthly Hisobot"],
        ],
        resize_keyboard=True,
    )


# ---------------------------------------------------------------------------
# Expense keyboards
# ---------------------------------------------------------------------------

def expense_categories_keyboard(custom_categories: Sequence[CustomCategory]) -> ReplyKeyboardMarkup:
    """Category selection keyboard with built-in + custom categories."""
    rows: list[list[str]] = []
    all_cats: list[str] = [f"{emoji} {name}" for emoji, name in BUILTIN_CATEGORIES]
    for cc in custom_categories:
        all_cats.append(f"{cc.emoji} {cc.name}")

    # 3 buttons per row
    for i in range(0, len(all_cats), 3):
        rows.append(all_cats[i : i + 3])

    # Bottom controls
    rows.append(["➕ Add Category", "⚙ Manage Categories"])
    rows.append(["🏠 Main Menu"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def manage_categories_keyboard(custom_categories: Sequence[CustomCategory]) -> InlineKeyboardMarkup:
    """Inline keyboard to delete custom categories."""
    buttons: list[list[InlineKeyboardButton]] = []
    for cat in custom_categories:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"🗑 {cat.emoji} {cat.name}",
                    callback_data=f"del_cat:{cat.id}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton("✅ Done", callback_data="manage_cats_done")])
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Money Lent keyboards
# ---------------------------------------------------------------------------

def money_lent_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["➕ New Entry", "📋 Active"],
            ["📜 History", "🏠 Main Menu"],
        ],
        resize_keyboard=True,
    )


def active_lent_keyboard(entries: Sequence[MoneyLent]) -> InlineKeyboardMarkup:
    """One button per active lent entry."""
    buttons: list[list[InlineKeyboardButton]] = []
    for entry in entries:
        label = f"🟢 {entry.person_name} — {format_amount(float(entry.amount), entry.currency)}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"lent_view:{entry.id}")])
    return InlineKeyboardMarkup(buttons)


def lent_detail_keyboard(entry_id: int) -> InlineKeyboardMarkup:
    """Detail view keyboard for a single lent entry."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Returned", callback_data=f"lent_returned:{entry_id}"),
                InlineKeyboardButton("✏ Edit", callback_data=f"lent_edit:{entry_id}"),
            ],
            [InlineKeyboardButton("❌ Delete", callback_data=f"lent_delete:{entry_id}")],
            [InlineKeyboardButton("⬅ Back", callback_data="lent_active_back")],
        ]
    )


def confirm_delete_keyboard(entry_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Yes, delete", callback_data=f"lent_confirm_delete:{entry_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"lent_view:{entry_id}"),
            ]
        ]
    )


# ---------------------------------------------------------------------------
# Report keyboards
# ---------------------------------------------------------------------------

def report_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📅 Previous Months", callback_data="report_prev_months")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="report_main_menu")],
        ]
    )


def previous_months_keyboard(months: list[tuple[int, int]]) -> InlineKeyboardMarkup:
    """One button per month that has expense data."""
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    buttons: list[list[InlineKeyboardButton]] = []
    for year, month in months:
        label = f"{month_names[month - 1]} {year}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"report_month:{year}:{month}")])
    buttons.append([InlineKeyboardButton("⬅ Back", callback_data="report_back")])
    return InlineKeyboardMarkup(buttons)
