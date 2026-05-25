"""Service layer for monthly reports."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import MoneyLent
from database.repositories import MoneyLentRepository, MonthStateRepository
from services.expense_service import ExpenseService
from services.lent_service import LentService
from utils.parser import format_amount
from utils.scheduler import current_month, month_label

logger = logging.getLogger(__name__)


class ReportService:
    """Build monthly report text and manage month transitions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._expense_svc = ExpenseService(session)
        self._lent_svc = LentService(session)
        self._month_repo = MonthStateRepository(session)

    async def check_month_transition(self, user_id: int) -> Optional[str]:
        """
        Call on every user interaction.
        If a new month has started and hasn't been initialized yet, mark it and
        return a notification message. Otherwise return None.
        """
        year, month = current_month()
        already = await self._month_repo.has_month(user_id, year, month)
        if already:
            return None

        # Mark new month
        await self._month_repo.mark_month(user_id, year, month)

        # Build transition message
        active_entries = await self._lent_svc.get_active(user_id)
        lines = [
            f"🗓 *{month_label(year, month)}* started!",
            "",
            "📊 Monthly statistics have been reset.",
        ]
        if active_entries:
            lines.append("")
            lines.append("💵 *Outstanding Money Lent carried forward:*")
            for e in active_entries:
                lines.append(
                    f"  🟢 {e.person_name} — {format_amount(float(e.amount), e.currency)}"
                )
        return "\n".join(lines)

    async def build_report(self, user_id: int, year: int, month: int) -> str:
        """Build formatted report text for the given month."""
        totals = await self._expense_svc.get_category_totals(user_id, year, month)
        active_lent = await self._lent_svc.get_active(user_id)

        lines = [f"📊 *{month_label(year, month)}*\n"]

        # --- Expenses ---
        if totals:
            grand_total_uzs = 0.0
            expense_lines: list[str] = []
            for cat, currencies in sorted(totals.items()):
                for currency, amount in currencies.items():
                    expense_lines.append(f"  {cat} — {format_amount(amount, currency)}")
                    if currency == "UZS":
                        grand_total_uzs += amount

            lines.append(f"💸 *Total Expenses:* {format_amount(grand_total_uzs, 'UZS')}")
            lines.append("")
            lines.append("*Category Breakdown:*")
            lines.extend(expense_lines)

            # Largest category
            if totals:
                largest_cat = max(
                    totals.items(),
                    key=lambda kv: sum(v for v in kv[1].values()),
                )
                lines.append(f"\n🏆 Largest category: *{largest_cat[0]}*")
        else:
            lines.append("💸 No expenses recorded this month.")

        # --- Active Money Lent ---
        lines.append("")
        if active_lent:
            lines.append("💵 *Active Money Lent:*")
            for e in active_lent:
                note_str = f" ({e.note})" if e.note else ""
                lines.append(
                    f"  🟢 {e.person_name} — {format_amount(float(e.amount), e.currency)}{note_str}"
                )
        else:
            lines.append("💵 No active money lent.")

        return "\n".join(lines)

    async def get_available_months(self, user_id: int) -> list[tuple[int, int]]:
        """Return all months that have expense data, excluding current month."""
        year, month = current_month()
        all_months = await self._expense_svc.get_months_with_data(user_id)
        return [(y, m) for y, m in all_months if (y, m) != (year, month)]
