"""
Async LLM forwarding client.

Supports OpenAI natively and Anthropic via format translation.
Adding a new provider = add an entry to _PROVIDERS and optionally a translator pair.

Risk mitigation: equal treatment of all providers prevents AROP from becoming
a single-provider tool. Cross-provider replay (e.g. re-run a GPT-4o trace on
Claude) is the key differentiator vs. OpenAI's native observability.
"""
import time
from typing import Any

import httpx

from config import settings

# httpx client is module-level for connection pooling across requests
_client = httpx.AsyncClient(timeout=120.0)


# Provider routing table
_PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com",
        "chat_path": "/v1/chat/completions",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "chat_path": "/v1/messages",
        "auth_header": "x-api-key",
        "auth_prefix": "",
    },
}


def detect_provider(model: str) -> str:
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("gemini"):
        # Google uses an OpenAI-compat endpoint via the generativelanguage API.
        # Full Gemini native support is planned for v1.1; for MVP we pass through
        # as OpenAI-format and expect the caller to set a custom base_url header.
        return "openai"
    return "openai"


def _get_api_key(provider: str) -> str:
    if provider == "anthropic":
        return settings.anthropic_api_key
    return settings.openai_api_key


# ── Request / response translators ───────────────────────────────────────────

def _to_anthropic_request(body: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAI-format chat request to Anthropic Messages API format."""
    messages = body.get("messages", [])
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    user_messages = [m for m in messages if m["role"] != "system"]

    anthropic_body: dict[str, Any] = {
        "model": body["model"],
        "messages": [{"role": m["role"], "content": m["content"]} for m in user_messages],
        "max_tokens": body.get("max_tokens") or 1024,
    }
    if system_parts:
        anthropic_body["system"] = "\n".join(system_parts)
    if "temperature" in body and body["temperature"] is not None:
        anthropic_body["temperature"] = body["temperature"]
    return anthropic_body


def _from_anthropic_response(anthropic_resp: dict[str, Any], original_model: str) -> dict[str, Any]:
    """Translate an Anthropic Messages API response to OpenAI chat completion format."""
    content_blocks = anthropic_resp.get("content", [])
    text = " ".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
    usage = anthropic_resp.get("usage", {})

    return {
        "id": anthropic_resp.get("id", ""),
        "object": "chat.completion",
        "model": original_model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": anthropic_resp.get("stop_reason", "stop"),
            }
        ],
        "usage": {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        },
    }


# ── Main forwarding function ──────────────────────────────────────────────────

async def forward_request(
    body: dict[str, Any],
    provider_base_url: str | None = None,
) -> tuple[dict[str, Any], int]:
    """
    Forward a chat completion request to the appropriate LLM provider.

    Returns (openai_format_response_dict, latency_ms).
    The response is always normalised to OpenAI format regardless of provider,
    so the rest of the proxy pipeline never needs to know which backend was used.

    provider_base_url: optional override — lets enterprise customers point AROP
    at a local model server (Ollama, vLLM) without changing any other code.
    """
    model = body.get("model", "")
    provider = detect_provider(model)
    config = _PROVIDERS[provider]
    api_key = _get_api_key(provider)

    # Translate request body if needed
    send_body = _to_anthropic_request(body) if provider == "anthropic" else body

    base = provider_base_url or config["base_url"]
    url = base.rstrip("/") + config["chat_path"]
    headers = {
        config["auth_header"]: config["auth_prefix"] + api_key,
        "Content-Type": "application/json",
    }
    if provider == "anthropic":
        headers["anthropic-version"] = "2023-06-01"

    start = time.monotonic()
    response = await _client.post(url, json=send_body, headers=headers)
    latency_ms = int((time.monotonic() - start) * 1000)

    response.raise_for_status()
    resp_json: dict[str, Any] = response.json()

    # Normalise Anthropic response to OpenAI format
    if provider == "anthropic":
        resp_json = _from_anthropic_response(resp_json, model)

    return resp_json, latency_ms


async def close() -> None:
    """Call on app shutdown to cleanly close the connection pool."""
    await _client.aclose()
