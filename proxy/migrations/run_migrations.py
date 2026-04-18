"""
Run all SQL migration files in order, then create any ORM tables not covered by SQL.
Called automatically in main.py's lifespan, and can also be run standalone:

    python migrations/run_migrations.py
"""
import asyncio
import pathlib
import sys

import psycopg
from sqlalchemy.ext.asyncio import create_async_engine

# Allow running as a standalone script from any working directory
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from config import settings
from database import Base
import models  # noqa: F401 — registers all ORM models on Base.metadata


MIGRATIONS_DIR = pathlib.Path(__file__).parent
SQL_FILES = sorted(MIGRATIONS_DIR.glob("*.sql"))


async def run_sql_files() -> None:
    """Execute each .sql migration file using raw psycopg (no ORM overhead)."""
    # Convert the SQLAlchemy URL to a plain psycopg DSN
    dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://")

    async with await psycopg.AsyncConnection.connect(dsn, autocommit=True) as conn:
        for sql_file in SQL_FILES:
            print(f"  Applying {sql_file.name} ...", end=" ")
            sql = sql_file.read_text(encoding="utf-8")
            await conn.execute(sql)  # type: ignore[arg-type]
            print("OK")


async def create_orm_tables() -> None:
    """
    Create any tables defined in models.py that the SQL files don't cover yet.
    Safe to call repeatedly — uses CREATE TABLE IF NOT EXISTS semantics via checkfirst=True.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def main() -> None:
    print("Running AROP migrations...")
    await run_sql_files()
    await create_orm_tables()
    print("Migrations complete.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
