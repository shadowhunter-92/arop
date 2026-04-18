"""
Background trace writer.

Runs as a FastAPI BackgroundTask so the LLM response is returned to the client
immediately — DB latency never adds to the user-visible round-trip time.

Uses its own DB session (not the request-scoped one) because BackgroundTasks
execute after the response is sent and the request session is already closed.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import AsyncSessionLocal
from models import Guardrail, ModelPricing, Trace
from services.cost_calculator import get_cached_db_rates, update_rate_cache
from services.hasher import hash_content

logger = logging.getLogger(__name__)

# 30-second in-process guardrail cache (shared with proxy router)
# Avoids a DB round-trip on every proxied request.
_guardrail_cache: dict[str, Any] = {"rules": [], "expires_at": 0.0}
_GUARDRAIL_TTL = 30.0

import time  # noqa: E402 — after dataclass import to keep grouping clear


@dataclass
class TraceData:
    trace_id: str
    user_id: str | None
    feature: str | None
    model: str
    provider: str
    request_body: dict[str, Any] | None  # None when hash_payloads=True, store_raw=False
    response_body: dict[str, Any] | None
    prompt_hash: str | None
    response_hash: str | None
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    status: str                           # success | blocked | error
    guardrail_hits: list[str]
    parent_trace_id: str | None = None
    raw_storage_url: str | None = None


async def save_trace(data: TraceData) -> None:
    """Persist a TraceData record. Called via FastAPI BackgroundTasks."""
    try:
        async with AsyncSessionLocal() as db:
            trace = Trace(
                trace_id=data.trace_id,
                user_id=data.user_id,
                feature=data.feature,
                model=data.model,
                provider=data.provider,
                request_body=data.request_body,
                response_body=data.response_body,
                prompt_hash=data.prompt_hash,
                response_hash=data.response_hash,
                latency_ms=data.latency_ms,
                prompt_tokens=data.prompt_tokens,
                completion_tokens=data.completion_tokens,
                total_tokens=data.total_tokens,
                cost_usd=data.cost_usd,
                status=data.status,
                guardrail_hits=data.guardrail_hits or [],
                parent_trace_id=data.parent_trace_id,
                raw_storage_url=data.raw_storage_url,
            )
            db.add(trace)
            await db.commit()
    except Exception:
        logger.exception("Failed to persist trace %s", data.trace_id)


def build_trace_data(
    *,
    trace_id: str,
    user_id: str | None,
    feature: str | None,
    model: str,
    provider: str,
    request_body: dict[str, Any],
    response_body: dict[str, Any] | None,
    latency_ms: int,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    status: str,
    guardrail_hits: list[str],
    parent_trace_id: str | None = None,
) -> TraceData:
    """
    Apply hash_payloads / store_raw settings and return a TraceData ready to persist.

    When hash_payloads=True (default):
      - request_body and response_body are set to None (never stored as plaintext).
      - prompt_hash and response_hash are always populated for deduplication / replay matching.

    When store_raw=True (opt-in):
      - request_body and response_body are stored in the DB alongside the hashes.
    """
    prompt_hash = hash_content(request_body.get("messages", request_body))
    response_text = ""
    if response_body:
        try:
            response_text = response_body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            response_text = str(response_body)
    response_hash = hash_content(response_text) if response_text else None

    store_request = response_body is not None  # only store if we have a real response
    if settings.hash_payloads and not settings.store_raw:
        stored_request = None
        stored_response = None
    else:
        stored_request = request_body
        stored_response = response_body

    return TraceData(
        trace_id=trace_id,
        user_id=user_id,
        feature=feature,
        model=model,
        provider=provider,
        request_body=stored_request,
        response_body=stored_response,
        prompt_hash=prompt_hash,
        response_hash=response_hash,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        cost_usd=cost_usd,
        status=status,
        guardrail_hits=guardrail_hits,
        parent_trace_id=parent_trace_id,
    )


async def get_cached_guardrails(db: AsyncSession) -> list[dict[str, Any]]:
    """
    Return enabled guardrail rules, refreshing from DB every 30 seconds.
    Shared by the proxy router and replay router to avoid per-request DB hits.
    """
    now = time.monotonic()
    if now < _guardrail_cache["expires_at"]:
        return _guardrail_cache["rules"]

    result = await db.execute(select(Guardrail).where(Guardrail.enabled.is_(True)))
    rows = result.scalars().all()
    rules = [
        {"name": r.name, "type": r.type, "pattern": r.pattern,
         "action": r.action, "enabled": r.enabled}
        for r in rows
    ]
    _guardrail_cache["rules"] = rules
    _guardrail_cache["expires_at"] = now + _GUARDRAIL_TTL
    return rules


async def get_cached_pricing(db: AsyncSession) -> dict[str, dict[str, float]]:
    """Return DB-sourced pricing rates, refreshing every 5 minutes."""
    cached = get_cached_db_rates()
    if cached:
        return cached

    result = await db.execute(select(ModelPricing))
    rows = result.scalars().all()
    update_rate_cache(rows)
    return get_cached_db_rates()


def invalidate_guardrail_cache() -> None:
    """Call after creating/toggling a guardrail so the proxy picks up changes immediately."""
    _guardrail_cache["expires_at"] = 0.0
