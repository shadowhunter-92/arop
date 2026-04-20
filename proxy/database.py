from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings


def _async_url(url: str) -> str:
    """Force psycopg3 async driver regardless of what Railway provides."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg" + url[len(prefix) - 3:]
    return url


engine = create_async_engine(
    _async_url(settings.database_url),
    echo=False,
    pool_timeout=15,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
