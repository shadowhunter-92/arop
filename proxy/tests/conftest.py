# Windows: psycopg3 is incompatible with the default ProactorEventLoop.
# Must be set before any async code or imports that trigger it.
import asyncio
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Environment vars must be set BEFORE any app module is imported so that
# pydantic-settings picks up the test DB URL at Settings() instantiation time.
import os
os.environ["DATABASE_URL"] = "postgresql+psycopg://arop:arop_dev@localhost:5432/arop_test"
os.environ.setdefault("AROP_MASTER_KEY", "test-master-key-for-ci")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")

import asyncio
import hashlib
from unittest.mock import AsyncMock, patch

import psycopg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import database
import models  # noqa: F401 — registers ORM models on Base.metadata
from database import Base, get_db
from main import app

TEST_DB_URL = os.environ["DATABASE_URL"]

# Canned LLM response reused across proxy/replay tests
CANNED_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "The answer is 4."},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}


def pytest_configure(config):
    """Create arop_test database if it does not exist."""
    try:
        conn = psycopg.connect(
            "postgresql://arop:arop_dev@localhost:5432/postgres", autocommit=True
        )
        conn.execute("CREATE DATABASE arop_test")
        conn.close()
    except Exception:
        pass  # already exists or postgres unavailable — tests will fail with a clear error


@pytest_asyncio.fixture
async def db():
    """
    Per-test fixture that:
    1. Creates all tables in arop_test (idempotent).
    2. Truncates operational tables for isolation.
    3. Overrides FastAPI's get_db dependency to use the test engine.
    4. Yields an AsyncSession the test can use directly for setup/assertions.
    """
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("TRUNCATE api_keys, guardrails, traces RESTART IDENTITY CASCADE")
        )

    TestSession = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with TestSession() as session:
        yield session

    app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db):
    """HTTP test client wired to the FastAPI app with lifespan disabled."""
    with (
        patch("main._run_migrations", new_callable=AsyncMock),
        patch("main._seed_default_key", new_callable=AsyncMock),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac


@pytest_asyncio.fixture
async def valid_api_key(db: AsyncSession) -> str:
    """Insert a test API key and return the raw string for use in headers."""
    from models import ApiKey

    raw = "test-api-key-12345"
    db.add(ApiKey(name="test", key_hash=hashlib.sha256(raw.encode()).hexdigest()))
    await db.commit()
    return raw


@pytest.fixture
def mock_llm():
    """Patch llm_client.forward_request to return a canned response."""
    with patch(
        "services.llm_client.forward_request", new_callable=AsyncMock
    ) as mock:
        mock.return_value = (CANNED_RESPONSE, 142)
        yield mock


@pytest.fixture
def mock_llm_error():
    """Patch llm_client.forward_request to raise an HTTP 429 error."""
    import httpx

    error = httpx.HTTPStatusError(
        "rate limited",
        request=httpx.Request("POST", "https://api.openai.com"),
        response=httpx.Response(429, json={"error": {"message": "rate limited"}}),
    )
    with patch(
        "services.llm_client.forward_request", new_callable=AsyncMock
    ) as mock:
        mock.side_effect = error
        yield mock
