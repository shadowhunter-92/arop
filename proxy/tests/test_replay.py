"""Tests for POST /v1/replay."""
import uuid
from datetime import datetime, timezone

import pytest

from models import Trace


def _stored_trace(trace_id: str, with_body: bool = True) -> Trace:
    body = {"model": "gpt-4o", "messages": [{"role": "user", "content": "What is 2+2?"}]}
    return Trace(
        trace_id=trace_id,
        model="gpt-4o",
        provider="openai",
        request_body=body if with_body else None,
        response_body={"choices": [{"message": {"content": "4"}}]},
        prompt_hash="abc" * 21 + "ab",
        status="success",
        prompt_tokens=10,
        completion_tokens=3,
        total_tokens=13,
        cost_usd=0.0001,
        latency_ms=300,
        guardrail_hits=[],
        created_at=datetime.now(timezone.utc),
    )


async def test_replay_success(client, valid_api_key, db, mock_llm):
    tid = str(uuid.uuid4())
    db.add(_stored_trace(tid))
    await db.commit()

    r = await client.post(
        "/v1/replay",
        json={"trace_id": tid},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["original_trace"]["trace_id"] == tid
    assert data["replay_response"]["choices"][0]["message"]["content"] == "The answer is 4."
    assert data["replay_trace_id"] != tid
    assert data["model_used"] == "gpt-4o"


async def test_replay_model_override(client, valid_api_key, db, mock_llm):
    tid = str(uuid.uuid4())
    db.add(_stored_trace(tid))
    await db.commit()

    r = await client.post(
        "/v1/replay",
        json={"trace_id": tid, "model_override": "gpt-4o-mini"},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 200
    assert r.json()["model_used"] == "gpt-4o-mini"


async def test_replay_prompt_override(client, valid_api_key, db, mock_llm):
    tid = str(uuid.uuid4())
    db.add(_stored_trace(tid))
    await db.commit()

    new_msgs = [{"role": "user", "content": "What is 3+3?"}]
    r = await client.post(
        "/v1/replay",
        json={"trace_id": tid, "prompt_override": new_msgs},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 200
    # verify the mock was called (with the overridden prompt)
    mock_llm.assert_called_once()
    call_body = mock_llm.call_args[0][0]
    assert call_body["messages"] == new_msgs


async def test_replay_hash_only_without_override_returns_422(client, valid_api_key, db, mock_llm):
    tid = str(uuid.uuid4())
    db.add(_stored_trace(tid, with_body=False))  # no stored request_body
    await db.commit()

    r = await client.post(
        "/v1/replay",
        json={"trace_id": tid},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 422
    assert "hash_payloads" in r.json()["detail"]


async def test_replay_hash_only_with_override_succeeds(client, valid_api_key, db, mock_llm):
    tid = str(uuid.uuid4())
    db.add(_stored_trace(tid, with_body=False))
    await db.commit()

    r = await client.post(
        "/v1/replay",
        json={"trace_id": tid, "prompt_override": [{"role": "user", "content": "hi"}]},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 200


async def test_replay_not_found(client, valid_api_key, db):
    r = await client.post(
        "/v1/replay",
        json={"trace_id": "no-such-trace"},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 404
