"""SQLAlchemy ORM models for the Finance Tracker Bot."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """Telegram user record."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    expenses: Mapped[list["Expense"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    lent_entries: Mapped[list["MoneyLent"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    custom_categories: Mapped[list["CustomCategory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    month_states: Mapped[list["MonthState"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"


class Expense(Base):
    """Individual expense record."""

    __tablename__ = "expenses"
    __table_args__ = (
        Index("ix_expenses_user_id", "user_id"),
        Index("ix_expenses_expense_date", "expense_date"),
        Index("ix_expenses_user_date", "user_id", "expense_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(64))
    amount: Mapped[float] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(8), default="UZS")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expense_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expense id={self.id} category={self.category} amount={self.amount} {self.currency}>"


class MoneyLent(Base):
    """Money lent to someone."""

    __tablename__ = "money_lent"
    __table_args__ = (
        Index("ix_money_lent_user_id", "user_id"),
        Index("ix_money_lent_returned", "returned"),
        Index("ix_money_lent_user_returned", "user_id", "returned"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    person_name: Mapped[str] = mapped_column(String(128))
    amount: Mapped[float] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(8), default="UZS")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lent_date: Mapped[date] = mapped_column(Date)
    returned: Mapped[bool] = mapped_column(Boolean, default=False)
    returned_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="lent_entries")

    def __repr__(self) -> str:
        return f"<MoneyLent id={self.id} person={self.person_name} amount={self.amount}>"


class CustomCategory(Base):
    """User-defined expense category."""

    __tablename__ = "custom_categories"
    __table_args__ = (
        Index("ix_custom_categories_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(64))
    emoji: Mapped[str] = mapped_column(String(8), default="📌")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="custom_categories")

    def __repr__(self) -> str:
        return f"<CustomCategory id={self.id} name={self.name}>"


class MonthState(Base):
    """Tracks month transitions per user."""

    __tablename__ = "month_state"
    __table_args__ = (
        Index("ix_month_state_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    initialized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="month_states")

    def __repr__(self) -> str:
        return f"<MonthState user={self.user_id} {self.year}-{self.month}>"
