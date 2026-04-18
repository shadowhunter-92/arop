"""Tests for GET/POST /v1/guardrails and PATCH /{id}/toggle."""
import pytest


async def _create(client, key, **kwargs):
    payload = {"name": "test_rule", "type": "pre_request", "pattern": r"\bfoo\b", "action": "block"}
    payload.update(kwargs)
    return await client.post("/v1/guardrails", json=payload, headers={"X-API-Key": key})


async def test_list_guardrails_empty(client, valid_api_key):
    r = await client.get("/v1/guardrails", headers={"X-API-Key": valid_api_key})
    assert r.status_code == 200
    assert r.json() == []


async def test_create_guardrail(client, valid_api_key):
    r = await _create(client, valid_api_key)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "test_rule"
    assert data["enabled"] is True
    assert "id" in data


async def test_list_guardrails_after_create(client, valid_api_key):
    await _create(client, valid_api_key, name="rule_a")
    await _create(client, valid_api_key, name="rule_b")
    r = await client.get("/v1/guardrails", headers={"X-API-Key": valid_api_key})
    assert len(r.json()) == 2


async def test_create_invalid_type(client, valid_api_key):
    r = await _create(client, valid_api_key, type="bad_type")
    assert r.status_code == 400


async def test_create_invalid_action(client, valid_api_key):
    r = await _create(client, valid_api_key, action="explode")
    assert r.status_code == 400


async def test_create_invalid_regex(client, valid_api_key):
    r = await _create(client, valid_api_key, pattern="[invalid")
    assert r.status_code == 400


async def test_toggle_guardrail_disable(client, valid_api_key):
    created = (await _create(client, valid_api_key)).json()
    gid = created["id"]

    r = await client.patch(
        f"/v1/guardrails/{gid}/toggle",
        json={"enabled": False},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 200
    assert r.json()["enabled"] is False


async def test_toggle_guardrail_not_found(client, valid_api_key):
    r = await client.patch(
        "/v1/guardrails/00000000-0000-0000-0000-000000000000/toggle",
        json={"enabled": False},
        headers={"X-API-Key": valid_api_key},
    )
    assert r.status_code == 404


async def test_delete_guardrail(client, valid_api_key):
    gid = (await _create(client, valid_api_key)).json()["id"]
    r = await client.delete(f"/v1/guardrails/{gid}", headers={"X-API-Key": valid_api_key})
    assert r.status_code == 204

    listed = await client.get("/v1/guardrails", headers={"X-API-Key": valid_api_key})
    assert listed.json() == []
