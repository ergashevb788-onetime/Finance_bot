"""Async SQLAlchemy engine and session factory."""

import logging
import ssl as _ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import config
from database.models import Base

logger = logging.getLogger(__name__)


def _build_engine_url_and_ssl(database_url: str) -> tuple[str, dict]:
    """
    Convert a standard postgres:// URL to asyncpg-compatible form.

    asyncpg does not accept ?sslmode= query param — it must be passed as
    an ssl= connect_arg. Strip sslmode from the URL and build the ssl context.
    """
    url = database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    sslmode = qs.pop("sslmode", ["disable"])[0]
    qs.pop("channel_binding", None)  # asyncpg doesn't accept this param


    # Rebuild URL without sslmode
    new_query = urlencode({k: v[0] for k, v in qs.items()})
    clean_url = urlunparse(parsed._replace(query=new_query))

    connect_args: dict = {}
    if sslmode in ("require", "verify-ca", "verify-full"):
        ssl_ctx = _ssl.create_default_context()
        if sslmode == "require":
            # Neon provides valid certs; still set CERT_NONE to avoid
            # hostname mismatch issues with some connection poolers.
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = _ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx
    elif sslmode == "prefer":
        connect_args["ssl"] = True

    return clean_url, connect_args


_engine_url, _connect_args = _build_engine_url_and_ssl(config.DATABASE_URL)

engine = create_async_engine(
    _engine_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables if they don't exist (fallback for non-Alembic setups)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")


async def close_db() -> None:
    """Dispose engine connections."""
    await engine.dispose()
    logger.info("Database connections closed.")
