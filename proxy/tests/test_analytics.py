"""Tests for GET /v1/analytics/cost."""
import uuid
from datetime import datetime, timezone

import pytest

from models import Trace


def _trace(model="gpt-4o", feature=None, cost=0.001, status="success") -> Trace:
    return Trace(
        trace_id=str(uuid.uuid4()),
        model=model,
        provider="openai",
        feature=feature,
        status=status,
        cost_usd=cost,
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        latency_ms=100,
        guardrail_hits=[],
        created_at=datetime.now(timezone.utc),
    )


async def test_cost_analytics_empty(client, valid_api_key):
    r = await client.get("/v1/analytics/cost", headers={"X-API-Key": valid_api_key})
    assert r.status_code == 200
    data = r.json()
    assert data["total_cost_usd"] == 0.0
    assert data["total_calls"] == 0
    assert data["over_time"] == []
    assert data["by_model"] == []


async def test_cost_analytics_total(client, valid_api_key, db):
    db.add(_trace(cost=0.001))
    db.add(_trace(cost=0.002))
    db.add(_trace(cost=0.003))
    await db.commit()

    r = await client.get("/v1/analytics/cost", headers={"X-API-Key": valid_api_key})
    data = r.json()
    assert data["total_calls"] == 3
    assert abs(data["total_cost_usd"] - 0.006) < 1e-6


async def test_cost_analytics_by_model(client, valid_api_key, db):
    db.add(_trace(model="gpt-4o", cost=0.005))
    db.add(_trace(model="gpt-4o", cost=0.005))
    db.add(_trace(model="gpt-4o-mini", cost=0.001))
    await db.commit()

    r = await client.get("/v1/analytics/cost", headers={"X-API-Key": valid_api_key})
    by_model = {row["model"]: row for row in r.json()["by_model"]}
    assert by_model["gpt-4o"]["call_count"] == 2
    assert abs(by_model["gpt-4o"]["cost_usd"] - 0.010) < 1e-6
    assert by_model["gpt-4o-mini"]["call_count"] == 1


async def test_cost_analytics_by_feature(client, valid_api_key, db):
    db.add(_trace(feature="chatbot", cost=0.002))
    db.add(_trace(feature="search", cost=0.003))
    db.add(_trace(feature=None, cost=0.001))
    await db.commit()

    r = await client.get("/v1/analytics/cost", headers={"X-API-Key": valid_api_key})
    by_feat = {row["feature"]: row for row in r.json()["by_feature"]}
    assert "chatbot" in by_feat
    assert "(untagged)" in by_feat


async def test_cost_analytics_excludes_blocked(client, valid_api_key, db):
    db.add(_trace(cost=0.005, status="success"))
    db.add(_trace(cost=0.999, status="blocked"))  # should not count
    await db.commit()

    r = await client.get("/v1/analytics/cost", headers={"X-API-Key": valid_api_key})
    data = r.json()
    assert data["total_calls"] == 1
    assert abs(data["total_cost_usd"] - 0.005) < 1e-6


async def test_cost_analytics_over_time_grouped(client, valid_api_key, db):
    for _ in range(3):
        db.add(_trace(cost=0.001))
    await db.commit()

    r = await client.get("/v1/analytics/cost", headers={"X-API-Key": valid_api_key})
    over_time = r.json()["over_time"]
    # All inserted with today's timestamp, so should be one bucket
    assert len(over_time) == 1
    assert over_time[0]["call_count"] == 3
