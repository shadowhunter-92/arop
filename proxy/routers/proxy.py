"""
POST /v1/chat/completions — the core proxy endpoint.

Request flow:
  1. Authenticate via X-API-Key
  2. Load guardrail rules (30-second cache)
  3. Check pre-request guardrails — block if matched
  4. Forward to LLM provider, measure latency
  5. Redact PII in response text
  6. Compute hallucination heuristic (returned in response header)
  7. Calculate cost from DB pricing table (5-minute cache)
  8. Write trace to DB via BackgroundTask (non-blocking)
  9. Return original response + X-Trace-ID header
"""
import json
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import verify_api_key
from services import guardrail_engine, llm_client
from services.cost_calculator import calculate_cost
from services.guardrail_engine import (
    check_pre_request,
    compute_hallucination_heuristic,
    redact_post_response,
)
from services.trace_logger import (
    build_trace_data,
    get_cached_guardrails,
    get_cached_pricing,
    save_trace,
)

router = APIRouter()


def _messages_to_text(messages: list[dict[str, Any]]) -> str:
    """Flatten messages list to a single string for guardrail pattern matching."""
    return "\n".join(
        m.get("content", "")
        for m in messages
        if isinstance(m.get("content"), str)
    )


def _extract_usage(response_body: dict[str, Any]) -> tuple[int, int]:
    """Return (prompt_tokens, completion_tokens) from an OpenAI-format response."""
    usage = response_body.get("usage") or {}
    return usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _extract_response_text(response_body: dict[str, Any]) -> str:
    try:
        return response_body["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def _error_response(message: str, code: str, http_status: int) -> JSONResponse:
    """OpenAI-compatible error envelope."""
    return JSONResponse(
        status_code=http_status,
        content={"error": {"message": message, "type": "arop_error", "code": code}},
    )


@router.post("/v1/chat/completions")
async def proxy_completions(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_feature: str | None = Header(None, alias="X-Feature"),
    x_provider_base_url: str | None = Header(None, alias="X-Provider-Base-URL"),
) -> JSONResponse:
    # ── Parse request body ────────────────────────────────────────────────────
    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        return _error_response("Invalid JSON body.", "invalid_request", 400)

    if body.get("stream"):
        return _error_response(
            "Streaming is not supported in this version of AROP.", "streaming_unsupported", 400
        )

    model: str = body.get("model", "")
    if not model:
        return _error_response("'model' field is required.", "missing_model", 400)

    trace_id = str(uuid.uuid4())
    messages: list[dict[str, Any]] = body.get("messages", [])
    prompt_text = _messages_to_text(messages)

    # ── Load cached guardrails and pricing ────────────────────────────────────
    rules = await get_cached_guardrails(db)
    db_rates = await get_cached_pricing(db)

    # ── Pre-request guardrail check ───────────────────────────────────────────
    blocked, hits = check_pre_request(prompt_text, rules)
    if blocked:
        trace = build_trace_data(
            trace_id=trace_id,
            user_id=x_user_id,
            feature=x_feature,
            model=model,
            provider=llm_client.detect_provider(model),
            request_body=body,
            response_body=None,
            latency_ms=0,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            status="blocked",
            guardrail_hits=hits,
        )
        background_tasks.add_task(save_trace, trace)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "message": f"Request blocked by guardrail(s): {', '.join(hits)}",
                    "type": "guardrail_block",
                    "code": "blocked",
                    "guardrail_hits": hits,
                }
            },
            headers={"X-Trace-ID": trace_id},
        )

    # ── Forward to LLM ────────────────────────────────────────────────────────
    try:
        response_body, latency_ms = await llm_client.forward_request(
            body, provider_base_url=x_provider_base_url
        )
    except httpx.HTTPStatusError as exc:
        # Provider returned a 4xx/5xx — pass it through to the caller intact
        error_body: Any
        try:
            error_body = exc.response.json()
        except Exception:
            error_body = {"error": {"message": exc.response.text, "type": "provider_error"}}

        trace = build_trace_data(
            trace_id=trace_id,
            user_id=x_user_id,
            feature=x_feature,
            model=model,
            provider=llm_client.detect_provider(model),
            request_body=body,
            response_body=error_body,
            latency_ms=0,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            status="error",
            guardrail_hits=[],
        )
        background_tasks.add_task(save_trace, trace)
        return JSONResponse(
            status_code=exc.response.status_code,
            content=error_body,
            headers={"X-Trace-ID": trace_id},
        )
    except Exception as exc:
        trace = build_trace_data(
            trace_id=trace_id,
            user_id=x_user_id,
            feature=x_feature,
            model=model,
            provider=llm_client.detect_provider(model),
            request_body=body,
            response_body=None,
            latency_ms=0,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            status="error",
            guardrail_hits=[],
        )
        background_tasks.add_task(save_trace, trace)
        return JSONResponse(
            status_code=502,
            content={"error": {"message": f"LLM provider unreachable: {exc}", "type": "gateway_error"}},
            headers={"X-Trace-ID": trace_id},
        )

    # ── Post-response guardrail: PII redaction ────────────────────────────────
    response_text = _extract_response_text(response_body)
    redacted_text = redact_post_response(response_text, rules)

    if redacted_text != response_text:
        # Patch the redacted text back into the response dict (mutate a copy)
        response_body = json.loads(json.dumps(response_body))  # deep copy
        try:
            response_body["choices"][0]["message"]["content"] = redacted_text
        except (KeyError, IndexError):
            pass

    # ── Metrics ───────────────────────────────────────────────────────────────
    prompt_tokens, completion_tokens = _extract_usage(response_body)
    cost_usd = calculate_cost(model, prompt_tokens, completion_tokens, db_rates=db_rates)
    hallucination_score = compute_hallucination_heuristic(redacted_text)

    # ── Log trace asynchronously ──────────────────────────────────────────────
    trace = build_trace_data(
        trace_id=trace_id,
        user_id=x_user_id,
        feature=x_feature,
        model=model,
        provider=llm_client.detect_provider(model),
        request_body=body,
        response_body=response_body,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
        status="success",
        guardrail_hits=[],
    )
    background_tasks.add_task(save_trace, trace)

    # ── Return response ───────────────────────────────────────────────────────
    return JSONResponse(
        content=response_body,
        headers={
            "X-Trace-ID": trace_id,
            "X-Latency-Ms": str(latency_ms),
            "X-Cost-USD": str(cost_usd),
            "X-Hallucination-Score": str(hallucination_score),
        },
    )
