"""Service layer for expense operations."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CustomCategory, Expense
from database.repositories import CustomCategoryRepository, ExpenseRepository
from utils.parser import ParsedAmount

logger = logging.getLogger(__name__)


class ExpenseService:
    """Business logic for expenses."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ExpenseRepository(session)
        self._cat_repo = CustomCategoryRepository(session)

    async def add_expense(
        self,
        user_id: int,
        category: str,
        parsed: ParsedAmount,
        expense_date: date,
    ) -> Expense:
        """Save a new expense record."""
        expense = await self._repo.create(
            user_id=user_id,
            category=category,
            amount=parsed.amount,
            currency=parsed.currency,
            note=parsed.note,
            expense_date=expense_date,
        )
        logger.info("Expense saved: user=%s category=%s amount=%s %s", user_id, category, parsed.amount, parsed.currency)
        return expense

    async def get_monthly_expenses(self, user_id: int, year: int, month: int) -> list[Expense]:
        return list(await self._repo.get_by_month(user_id, year, month))

    async def get_category_totals(
        self, user_id: int, year: int, month: int
    ) -> dict[str, dict[str, float]]:
        """Return totals per category per currency for the given month."""
        expenses = await self.get_monthly_expenses(user_id, year, month)
        totals: dict[str, dict[str, float]] = {}
        for exp in expenses:
            cat = exp.category
            cur = exp.currency
            totals.setdefault(cat, {})
            totals[cat][cur] = totals[cat].get(cur, 0.0) + float(exp.amount)
        return totals

    async def get_months_with_data(self, user_id: int) -> list[tuple[int, int]]:
        return await self._repo.get_months_with_data(user_id)

    # Custom categories

    async def get_custom_categories(self, user_id: int) -> list[CustomCategory]:
        return list(await self._cat_repo.get_all(user_id))

    async def add_custom_category(
        self, user_id: int, name: str, emoji: str = "📌"
    ) -> Optional[CustomCategory]:
        """Add a custom category; return None if name already exists."""
        existing = await self._cat_repo.get_by_name(user_id, name)
        if existing:
            return None
        return await self._cat_repo.create(user_id=user_id, name=name, emoji=emoji)

    async def delete_custom_category(self, category_id: int, user_id: int) -> bool:
        return await self._cat_repo.delete(category_id, user_id)
