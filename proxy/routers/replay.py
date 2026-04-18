"""
POST /v1/replay — re-run a past trace against an LLM.

Works in two modes:
  1. store_raw=True  — original request_body is in the DB; replay it as-is or with overrides.
  2. store_raw=False — only hashes stored; caller must supply prompt_override to replay.

This is AROP's "wow moment" feature: engineers can reproduce a failure, swap the model,
edit the prompt, and see the side-by-side diff — all without touching production code.
"""
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import verify_api_key
from models import Trace
from schemas import ReplayRequest, ReplayResponse, TraceDetailResponse
from services import llm_client
from services.cost_calculator import calculate_cost
from services.trace_logger import (
    build_trace_data,
    get_cached_pricing,
    save_trace,
)

router = APIRouter(prefix="/v1", tags=["Replay"])


@router.post("/replay", response_model=ReplayResponse)
async def replay_trace(
    data: ReplayRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> ReplayResponse:
    # ── Fetch original trace ──────────────────────────────────────────────────
    result = await db.execute(select(Trace).where(Trace.trace_id == data.trace_id))
    trace = result.scalar_one_or_none()
    if trace is None:
        raise HTTPException(404, f"Trace '{data.trace_id}' not found.")

    original = TraceDetailResponse.model_validate(trace)

    # ── Resolve the messages to replay ───────────────────────────────────────
    if data.prompt_override:
        messages = data.prompt_override
    elif trace.request_body:
        messages = trace.request_body.get("messages", [])
    else:
        raise HTTPException(
            422,
            detail=(
                "Cannot replay: this trace was recorded with hash_payloads=True and "
                "store_raw=False so the original prompt was not stored. "
                "Provide 'prompt_override' in the request body to replay with a custom prompt, "
                "or enable store_raw=True in your AROP proxy config."
            ),
        )

    model = data.model_override or trace.model

    # Preserve non-messages fields from the original request if available
    base_body: dict[str, Any] = dict(trace.request_body or {})
    base_body["model"] = model
    base_body["messages"] = messages
    base_body.pop("stream", None)  # streaming not supported

    # ── Call LLM ─────────────────────────────────────────────────────────────
    try:
        response_body, latency_ms = await llm_client.forward_request(base_body)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider error during replay: {exc.response.text}",
        )

    # ── Cost ─────────────────────────────────────────────────────────────────
    db_rates = await get_cached_pricing(db)
    usage = response_body.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    cost_usd = calculate_cost(model, prompt_tokens, completion_tokens, db_rates=db_rates)

    # ── Log replay as a new trace (parent_trace_id links it to the original) ─
    replay_trace_id = str(uuid.uuid4())
    replay_trace_data = build_trace_data(
        trace_id=replay_trace_id,
        user_id=trace.user_id,
        feature=trace.feature,
        model=model,
        provider=llm_client.detect_provider(model),
        request_body=base_body,
        response_body=response_body,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
        status="success",
        guardrail_hits=[],
        parent_trace_id=data.trace_id,
    )
    background_tasks.add_task(save_trace, replay_trace_data)

    return ReplayResponse(
        original_trace=original,
        replay_response=response_body,
        replay_trace_id=replay_trace_id,
        model_used=model,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
    )
