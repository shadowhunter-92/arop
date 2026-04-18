"""Tests for POST /v1/evaluate."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from models import Trace


def _trace() -> Trace:
    return Trace(
        trace_id=str(uuid.uuid4()),
        model="gpt-4o-mini",
        provider="openai",
        status="success",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        cost_usd=0.0001,
        latency_ms=200,
        guardrail_hits=[],
        created_at=datetime.now(timezone.utc),
    )


async def test_evaluate_sets_score(client, valid_api_key, db):
    t = _trace()
    db.add(t)
    await db.commit()

    r = await client.post(
        "/v1/evaluate",
        json={"trace_id": t.trace_id, "score": 0.9, "label": "thumbs_up"},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["custom_score"] == 0.9
    assert data["label"] == "thumbs_up"

    await db.refresh(t)
    assert t.custom_score == 0.9


async def test_evaluate_zero_score(client, valid_api_key, db):
    t = _trace()
    db.add(t)
    await db.commit()
    r = await client.post(
        "/v1/evaluate",
        json={"trace_id": t.trace_id, "score": 0.0},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 200
    assert r.json()["custom_score"] == 0.0


async def test_evaluate_invalid_score_above_one(client, valid_api_key, db):
    t = _trace()
    db.add(t)
    await db.commit()
    r = await client.post(
        "/v1/evaluate",
        json={"trace_id": t.trace_id, "score": 1.5},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 422


async def test_evaluate_invalid_score_below_zero(client, valid_api_key, db):
    t = _trace()
    db.add(t)
    await db.commit()
    r = await client.post(
        "/v1/evaluate",
        json={"trace_id": t.trace_id, "score": -0.1},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 422


async def test_evaluate_trace_not_found(client, valid_api_key):
    r = await client.post(
        "/v1/evaluate",
        json={"trace_id": "ghost-trace", "score": 0.5},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 404
