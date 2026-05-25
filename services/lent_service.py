"""Service layer for money lent operations."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import MoneyLent
from database.repositories import MoneyLentRepository
from utils.parser import ParsedLentEntry

logger = logging.getLogger(__name__)


class LentService:
    """Business logic for money lent."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = MoneyLentRepository(session)

    async def add_entry(
        self,
        user_id: int,
        parsed: ParsedLentEntry,
        lent_date: date,
    ) -> MoneyLent:
        entry = await self._repo.create(
            user_id=user_id,
            person_name=parsed.person_name,
            amount=parsed.amount,
            currency=parsed.currency,
            note=parsed.note,
            lent_date=lent_date,
        )
        logger.info("Lent entry saved: user=%s person=%s amount=%s", user_id, parsed.person_name, parsed.amount)
        return entry

    async def get_active(self, user_id: int) -> list[MoneyLent]:
        return list(await self._repo.get_active(user_id))

    async def get_history(self, user_id: int) -> list[MoneyLent]:
        return list(await self._repo.get_history(user_id))

    async def get_entry(self, entry_id: int, user_id: int) -> Optional[MoneyLent]:
        return await self._repo.get(entry_id, user_id)

    async def mark_returned(self, entry_id: int, user_id: int, returned_date: date) -> bool:
        return await self._repo.mark_returned(entry_id, user_id, returned_date)

    async def update_entry(
        self,
        entry_id: int,
        user_id: int,
        parsed: ParsedLentEntry,
    ) -> bool:
        return await self._repo.update(
            entry_id=entry_id,
            user_id=user_id,
            person_name=parsed.person_name,
            amount=parsed.amount,
            currency=parsed.currency,
            note=parsed.note,
        )

    async def delete_entry(self, entry_id: int, user_id: int) -> bool:
        return await self._repo.delete(entry_id, user_id)
