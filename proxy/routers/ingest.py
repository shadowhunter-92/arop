"""
POST /v1/ingest/trace — internal trace ingestion endpoint.

Used when the proxy and the backend are split into separate services, or when a
client-side SDK sends traces directly (e.g. from a mobile app or edge function).
In the single-service MVP deployment the proxy router calls trace_logger.save_trace()
directly via BackgroundTasks and this endpoint is not used — but it's included so
the API contract is complete and external integrations can be built against it.
"""
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import verify_api_key
from models import Trace

router = APIRouter(prefix="/v1", tags=["Ingest"])


@router.post("/ingest/trace", status_code=status.HTTP_204_NO_CONTENT)
async def ingest_trace(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> None:
    trace = Trace(
        trace_id=payload["trace_id"],
        user_id=payload.get("user_id"),
        feature=payload.get("feature"),
        model=payload["model"],
        provider=payload.get("provider", "openai"),
        request_body=payload.get("request_body"),
        response_body=payload.get("response_body"),
        prompt_hash=payload.get("prompt_hash"),
        response_hash=payload.get("response_hash"),
        latency_ms=payload.get("latency_ms"),
        prompt_tokens=payload.get("prompt_tokens"),
        completion_tokens=payload.get("completion_tokens"),
        total_tokens=payload.get("total_tokens"),
        cost_usd=payload.get("cost_usd"),
        status=payload.get("status", "success"),
        guardrail_hits=payload.get("guardrail_hits", []),
        parent_trace_id=payload.get("parent_trace_id"),
    )
    db.add(trace)
    await db.commit()
