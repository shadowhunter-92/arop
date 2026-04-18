"""
AROP proxy server entry point.

Startup sequence:
  1. Run DB migrations (idempotent — safe to re-run)
  2. Seed a default API key from AROP_MASTER_KEY if no keys exist yet
  3. Mount all routers

Shutdown:
  - Close the shared httpx LLM client connection pool cleanly
"""
import asyncio
import hashlib
import logging
import sys
from contextlib import asynccontextmanager

# psycopg3 async requires SelectorEventLoop on Windows (ProactorEventLoop incompatible)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from config import settings
from database import AsyncSessionLocal, Base, engine
from models import ApiKey
from routers import analytics, evaluate, guardrails, ingest, proxy, replay, traces
from routers import settings as settings_router
from services import llm_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("arop")


async def _run_migrations() -> None:
    """Create all ORM tables. The SQL seed file is handled by run_migrations.py."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")


async def _seed_default_key() -> None:
    """
    On first boot, create a default API key whose raw value equals AROP_MASTER_KEY.
    Prints the key to stdout so the operator knows what to use immediately.
    This avoids needing a separate seed script or manual DB insert before the
    proxy is usable.
    """
    async with AsyncSessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(ApiKey))
        if count and count > 0:
            return  # keys already exist — skip

        raw_key = settings.arop_master_key
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        db.add(ApiKey(name="default", key_hash=key_hash))
        await db.commit()

    logger.info("=" * 60)
    logger.info("Default API key created. Use this in X-API-Key header:")
    logger.info("  %s", settings.arop_master_key)
    logger.info("Change AROP_MASTER_KEY in .env to set a custom key.")
    logger.info("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _run_migrations()
    await _seed_default_key()
    yield
    await llm_client.close()
    await engine.dispose()


app = FastAPI(
    title="AROP — AI Reliability & Observability Platform",
    version="0.1.0",
    description="Universal proxy that logs, guardrails, and analyzes every AI API call.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to dashboard origin in production
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-ID", "X-Latency-Ms", "X-Cost-USD", "X-Hallucination-Score"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(proxy.router)
app.include_router(traces.router)
app.include_router(guardrails.router)
app.include_router(replay.router)
app.include_router(analytics.router)
app.include_router(evaluate.router)
app.include_router(ingest.router)
app.include_router(settings_router.router)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": app.version}
