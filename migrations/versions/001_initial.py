"""Initial schema: users, expenses, money_lent, custom_categories, month_state

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("first_name", sa.String(128), nullable=False),
        sa.Column("last_name", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # expenses
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="UZS"),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_expenses_user_id", "expenses", ["user_id"])
    op.create_index("ix_expenses_expense_date", "expenses", ["expense_date"])
    op.create_index("ix_expenses_user_date", "expenses", ["user_id", "expense_date"])

    # money_lent
    op.create_table(
        "money_lent",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("person_name", sa.String(128), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="UZS"),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("lent_date", sa.Date, nullable=False),
        sa.Column("returned", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("returned_date", sa.Date, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_money_lent_user_id", "money_lent", ["user_id"])
    op.create_index("ix_money_lent_returned", "money_lent", ["returned"])
    op.create_index("ix_money_lent_user_returned", "money_lent", ["user_id", "returned"])

    # custom_categories
    op.create_table(
        "custom_categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("emoji", sa.String(8), nullable=False, server_default="📌"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_custom_categories_user_id", "custom_categories", ["user_id"])

    # month_state
    op.create_table(
        "month_state",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column(
            "initialized_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_month_state_user_id", "month_state", ["user_id"])


def downgrade() -> None:
    op.drop_table("month_state")
    op.drop_table("custom_categories")
    op.drop_table("money_lent")
    op.drop_table("expenses")
    op.drop_table("users")
