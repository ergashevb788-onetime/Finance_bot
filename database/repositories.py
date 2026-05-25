"""Repository pattern — all raw DB access lives here."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional, Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CustomCategory, Expense, MoneyLent, MonthState, User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User Repository
# ---------------------------------------------------------------------------

class UserRepository:
    """CRUD for users."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, user_id: int) -> Optional[User]:
        result = await self._s.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> User:
        user = await self.get(user_id)
        if user is None:
            user = User(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            self._s.add(user)
            logger.info("Created new user %s", user_id)
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
        return user


# ---------------------------------------------------------------------------
# Expense Repository
# ---------------------------------------------------------------------------

class ExpenseRepository:
    """CRUD for expenses."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        user_id: int,
        category: str,
        amount: float,
        currency: str,
        note: Optional[str],
        expense_date: date,
    ) -> Expense:
        expense = Expense(
            user_id=user_id,
            category=category,
            amount=amount,
            currency=currency,
            note=note,
            expense_date=expense_date,
        )
        self._s.add(expense)
        await self._s.flush()
        return expense

    async def get_by_month(self, user_id: int, year: int, month: int) -> Sequence[Expense]:
        result = await self._s.execute(
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= date(year, month, 1),
                Expense.expense_date < _next_month_date(year, month),
            )
            .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        )
        return result.scalars().all()

    async def get_months_with_data(self, user_id: int) -> list[tuple[int, int]]:
        """Return sorted list of (year, month) tuples that have expenses."""
        result = await self._s.execute(
            select(
                Expense.expense_date,
            )
            .where(Expense.user_id == user_id)
            .distinct()
        )
        months: set[tuple[int, int]] = set()
        for row in result.scalars().all():
            months.add((row.year, row.month))
        return sorted(months, reverse=True)


def _next_month_date(year: int, month: int) -> date:
    if month == 12:
        return date(year + 1, 1, 1)
    return date(year, month + 1, 1)


# ---------------------------------------------------------------------------
# Money Lent Repository
# ---------------------------------------------------------------------------

class MoneyLentRepository:
    """CRUD for money lent entries."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        user_id: int,
        person_name: str,
        amount: float,
        currency: str,
        note: Optional[str],
        lent_date: date,
    ) -> MoneyLent:
        entry = MoneyLent(
            user_id=user_id,
            person_name=person_name,
            amount=amount,
            currency=currency,
            note=note,
            lent_date=lent_date,
        )
        self._s.add(entry)
        await self._s.flush()
        return entry

    async def get(self, entry_id: int, user_id: int) -> Optional[MoneyLent]:
        result = await self._s.execute(
            select(MoneyLent).where(MoneyLent.id == entry_id, MoneyLent.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_active(self, user_id: int) -> Sequence[MoneyLent]:
        result = await self._s.execute(
            select(MoneyLent)
            .where(MoneyLent.user_id == user_id, MoneyLent.returned == False)  # noqa: E712
            .order_by(MoneyLent.lent_date.desc())
        )
        return result.scalars().all()

    async def get_history(self, user_id: int) -> Sequence[MoneyLent]:
        result = await self._s.execute(
            select(MoneyLent)
            .where(MoneyLent.user_id == user_id, MoneyLent.returned == True)  # noqa: E712
            .order_by(MoneyLent.returned_date.desc())
        )
        return result.scalars().all()

    async def mark_returned(self, entry_id: int, user_id: int, returned_date: date) -> bool:
        result = await self._s.execute(
            update(MoneyLent)
            .where(MoneyLent.id == entry_id, MoneyLent.user_id == user_id)
            .values(returned=True, returned_date=returned_date)
        )
        return result.rowcount > 0

    async def update(
        self,
        entry_id: int,
        user_id: int,
        person_name: str,
        amount: float,
        currency: str,
        note: Optional[str],
    ) -> bool:
        result = await self._s.execute(
            update(MoneyLent)
            .where(MoneyLent.id == entry_id, MoneyLent.user_id == user_id)
            .values(
                person_name=person_name,
                amount=amount,
                currency=currency,
                note=note,
            )
        )
        return result.rowcount > 0

    async def delete(self, entry_id: int, user_id: int) -> bool:
        result = await self._s.execute(
            delete(MoneyLent).where(MoneyLent.id == entry_id, MoneyLent.user_id == user_id)
        )
        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Custom Category Repository
# ---------------------------------------------------------------------------

class CustomCategoryRepository:
    """CRUD for user-defined categories."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_all(self, user_id: int) -> Sequence[CustomCategory]:
        result = await self._s.execute(
            select(CustomCategory)
            .where(CustomCategory.user_id == user_id)
            .order_by(CustomCategory.created_at)
        )
        return result.scalars().all()

    async def create(self, user_id: int, name: str, emoji: str = "📌") -> CustomCategory:
        cat = CustomCategory(user_id=user_id, name=name, emoji=emoji)
        self._s.add(cat)
        await self._s.flush()
        return cat

    async def delete(self, category_id: int, user_id: int) -> bool:
        result = await self._s.execute(
            delete(CustomCategory).where(
                CustomCategory.id == category_id,
                CustomCategory.user_id == user_id,
            )
        )
        return result.rowcount > 0

    async def get_by_name(self, user_id: int, name: str) -> Optional[CustomCategory]:
        result = await self._s.execute(
            select(CustomCategory).where(
                CustomCategory.user_id == user_id,
                CustomCategory.name == name,
            )
        )
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Month State Repository
# ---------------------------------------------------------------------------

class MonthStateRepository:
    """Track which months have been initialized per user."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def has_month(self, user_id: int, year: int, month: int) -> bool:
        result = await self._s.execute(
            select(MonthState).where(
                MonthState.user_id == user_id,
                MonthState.year == year,
                MonthState.month == month,
            )
        )
        return result.scalar_one_or_none() is not None

    async def mark_month(self, user_id: int, year: int, month: int) -> MonthState:
        state = MonthState(user_id=user_id, year=year, month=month)
        self._s.add(state)
        await self._s.flush()
        return state

    async def get_last(self, user_id: int) -> Optional[MonthState]:
        result = await self._s.execute(
            select(MonthState)
            .where(MonthState.user_id == user_id)
            .order_by(MonthState.year.desc(), MonthState.month.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
