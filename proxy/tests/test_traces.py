"""Tests for GET /v1/traces and GET /v1/traces/{trace_id}."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from models import Trace


def _make_trace(**kwargs) -> Trace:
    defaults = dict(
        trace_id=str(uuid.uuid4()),
        model="gpt-4o",
        provider="openai",
        status="success",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        cost_usd=0.00005,
        latency_ms=200,
        guardrail_hits=[],
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Trace(**defaults)


async def test_list_traces_empty(client, valid_api_key):
    r = await client.get("/v1/traces", headers={"X-API-Key": valid_api_key})
    assert r.status_code == 200
    data = r.json()
    assert data["traces"] == []
    assert data["total"] == 0


async def test_list_traces_returns_inserted(client, valid_api_key, db):
    db.add(_make_trace(user_id="alice"))
    db.add(_make_trace(user_id="bob"))
    await db.commit()

    r = await client.get("/v1/traces", headers={"X-API-Key": valid_api_key})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["traces"]) == 2


async def test_list_traces_filter_by_model(client, valid_api_key, db):
    db.add(_make_trace(model="gpt-4o"))
    db.add(_make_trace(model="gpt-4o-mini"))
    await db.commit()

    r = await client.get("/v1/traces?model=gpt-4o", headers={"X-API-Key": valid_api_key})
    data = r.json()
    assert data["total"] == 1
    assert data["traces"][0]["model"] == "gpt-4o"


async def test_list_traces_filter_by_status(client, valid_api_key, db):
    db.add(_make_trace(status="success"))
    db.add(_make_trace(status="blocked"))
    db.add(_make_trace(status="error"))
    await db.commit()

    r = await client.get("/v1/traces?status=blocked", headers={"X-API-Key": valid_api_key})
    data = r.json()
    assert data["total"] == 1
    assert data["traces"][0]["status"] == "blocked"


async def test_list_traces_filter_by_user_id(client, valid_api_key, db):
    db.add(_make_trace(user_id="alice"))
    db.add(_make_trace(user_id="alice"))
    db.add(_make_trace(user_id="bob"))
    await db.commit()

    r = await client.get("/v1/traces?user_id=alice", headers={"X-API-Key": valid_api_key})
    assert r.json()["total"] == 2


async def test_list_traces_pagination(client, valid_api_key, db):
    for _ in range(5):
        db.add(_make_trace())
    await db.commit()

    r = await client.get("/v1/traces?limit=2&offset=0", headers={"X-API-Key": valid_api_key})
    data = r.json()
    assert data["total"] == 5
    assert len(data["traces"]) == 2

    r2 = await client.get("/v1/traces?limit=2&offset=2", headers={"X-API-Key": valid_api_key})
    assert len(r2.json()["traces"]) == 2


async def test_get_trace_detail(client, valid_api_key, db):
    tid = str(uuid.uuid4())
    db.add(_make_trace(
        trace_id=tid,
        request_body={"messages": [{"role": "user", "content": "hello"}]},
        response_body={"choices": [{"message": {"content": "hi"}}]},
        prompt_hash="abc123",
    ))
    await db.commit()

    r = await client.get(f"/v1/traces/{tid}", headers={"X-API-Key": valid_api_key})
    assert r.status_code == 200
    data = r.json()
    assert data["trace_id"] == tid
    assert data["prompt_hash"] == "abc123"


async def test_get_trace_not_found(client, valid_api_key):
    r = await client.get("/v1/traces/nonexistent-id", headers={"X-API-Key": valid_api_key})
    assert r.status_code == 404


async def test_list_traces_requires_auth(client, valid_api_key):
    r = await client.get("/v1/traces")
    assert r.status_code == 422
