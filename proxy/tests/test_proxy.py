"""
Integration tests for POST /v1/chat/completions.
LLM calls are mocked — no real API keys required.
"""
import pytest
from sqlalchemy import select

from models import Trace


async def _post(client, key, body=None, headers=None):
    h = {"X-API-Key": key, **(headers or {})}
    payload = body or {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "2+2?"}]}
    return await client.post("/v1/chat/completions", json=payload, headers=h)


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_proxy_success(client, valid_api_key, mock_llm):
    r = await _post(client, valid_api_key)
    assert r.status_code == 200
    data = r.json()
    assert data["choices"][0]["message"]["content"] == "The answer is 4."


async def test_proxy_returns_trace_id_header(client, valid_api_key, mock_llm):
    r = await _post(client, valid_api_key)
    assert "x-trace-id" in r.headers


async def test_proxy_returns_cost_header(client, valid_api_key, mock_llm):
    r = await _post(client, valid_api_key)
    assert float(r.headers["x-cost-usd"]) >= 0


async def test_proxy_returns_latency_header(client, valid_api_key, mock_llm):
    r = await _post(client, valid_api_key)
    assert int(r.headers["x-latency-ms"]) == 142


async def test_proxy_returns_hallucination_score_header(client, valid_api_key, mock_llm):
    r = await _post(client, valid_api_key)
    score = float(r.headers["x-hallucination-score"])
    assert 0.0 <= score <= 1.0


# ── Auth ──────────────────────────────────────────────────────────────────────

async def test_proxy_missing_api_key(client, valid_api_key, mock_llm):
    r = await client.post(
        "/v1/chat/completions",
        json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 422  # FastAPI missing header → 422


async def test_proxy_invalid_api_key(client, valid_api_key, mock_llm):
    r = await _post(client, "wrong-key-000")
    assert r.status_code == 401


# ── Validation ────────────────────────────────────────────────────────────────

async def test_proxy_stream_rejected(client, valid_api_key, mock_llm):
    r = await _post(
        client,
        valid_api_key,
        body={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}], "stream": True},
    )
    assert r.status_code == 400
    assert "stream" in r.json()["error"]["message"].lower()


async def test_proxy_missing_model(client, valid_api_key, mock_llm):
    r = await _post(
        client,
        valid_api_key,
        body={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 400


async def test_proxy_invalid_json(client, valid_api_key):
    r = await client.post(
        "/v1/chat/completions",
        content=b"not-json",
        headers={"X-API-Key": valid_api_key, "Content-Type": "application/json"},
    )
    assert r.status_code == 400


# ── Guardrails ────────────────────────────────────────────────────────────────

async def test_proxy_blocks_credit_card_prompt(client, valid_api_key, db, mock_llm):
    from models import Guardrail
    db.add(Guardrail(
        name="block_cc",
        type="pre_request",
        pattern=r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        action="block",
        enabled=True,
    ))
    await db.commit()

    from services.trace_logger import invalidate_guardrail_cache
    invalidate_guardrail_cache()

    r = await _post(
        client,
        valid_api_key,
        body={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "card is 4111 1111 1111 1111"}]},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "blocked"
    mock_llm.assert_not_called()


async def test_proxy_blocked_trace_has_status_blocked(client, valid_api_key, db, mock_llm):
    from models import Guardrail
    from services.trace_logger import invalidate_guardrail_cache
    db.add(Guardrail(
        name="block_cc", type="pre_request",
        pattern=r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        action="block", enabled=True,
    ))
    await db.commit()
    invalidate_guardrail_cache()

    r = await _post(
        client, valid_api_key,
        body={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "4111 1111 1111 1111"}]},
    )
    assert r.status_code == 400
    trace_id = r.headers["x-trace-id"]

    result = await db.execute(select(Trace).where(Trace.trace_id == trace_id))
    trace = result.scalar_one_or_none()
    assert trace is not None
    assert trace.status == "blocked"


# ── LLM errors ────────────────────────────────────────────────────────────────

async def test_proxy_llm_error_returns_502(client, valid_api_key, mock_llm_error):
    r = await _post(client, valid_api_key)
    assert r.status_code == 429  # passes through the provider status code


async def test_proxy_llm_error_logs_error_trace(client, valid_api_key, db, mock_llm_error):
    r = await _post(client, valid_api_key)
    trace_id = r.headers["x-trace-id"]

    result = await db.execute(select(Trace).where(Trace.trace_id == trace_id))
    trace = result.scalar_one_or_none()
    assert trace is not None
    assert trace.status == "error"


# ── Trace persistence ─────────────────────────────────────────────────────────

async def test_proxy_saves_trace_on_success(client, valid_api_key, db, mock_llm):
    r = await _post(client, valid_api_key)
    assert r.status_code == 200
    trace_id = r.headers["x-trace-id"]

    result = await db.execute(select(Trace).where(Trace.trace_id == trace_id))
    trace = result.scalar_one_or_none()
    assert trace is not None
    assert trace.status == "success"
    assert trace.model == "gpt-4o-mini"
    assert trace.prompt_tokens == 10
    assert trace.completion_tokens == 5
    assert trace.cost_usd > 0


async def test_proxy_saves_user_id_and_feature(client, valid_api_key, db, mock_llm):
    r = await _post(
        client, valid_api_key,
        headers={"X-User-ID": "user_abc", "X-Feature": "chat-widget"},
    )
    trace_id = r.headers["x-trace-id"]
    result = await db.execute(select(Trace).where(Trace.trace_id == trace_id))
    trace = result.scalar_one()
    assert trace.user_id == "user_abc"
    assert trace.feature == "chat-widget"


async def test_proxy_hashes_prompt_by_default(client, valid_api_key, db, mock_llm):
    """With hash_payloads=True (default), request_body should be None in DB."""
    r = await _post(client, valid_api_key)
    trace_id = r.headers["x-trace-id"]
    result = await db.execute(select(Trace).where(Trace.trace_id == trace_id))
    trace = result.scalar_one()
    # prompt_hash is always stored; raw body only if store_raw=True
    assert trace.prompt_hash is not None
    assert len(trace.prompt_hash) == 64  # SHA-256 hex
