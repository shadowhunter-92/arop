"""
Token-to-cost calculation.

Pricing is fetched from the pricing_table DB on first use, then cached in-process
with a 5-minute TTL so a single stale row never requires a server restart.
A hardcoded fallback table ensures cost calculation works even before the DB is
seeded or during tests that don't connect to a real database.

Risk mitigation: unlike LangSmith's known hardcoded-and-stale pricing, rates here
are live-updatable via a simple DB row update — no redeploy required.
"""
import time
from typing import Any

# Hardcoded fallback (USD per 1M tokens). Used when a model isn't in the DB.
_FALLBACK_RATES: dict[str, dict[str, float]] = {
    "gpt-4o":                       {"prompt": 2.50,   "completion": 10.00},
    "gpt-4o-mini":                  {"prompt": 0.15,   "completion": 0.60},
    "gpt-4-turbo":                  {"prompt": 10.00,  "completion": 30.00},
    "gpt-3.5-turbo":                {"prompt": 0.50,   "completion": 1.50},
    "claude-3-5-sonnet-20241022":   {"prompt": 3.00,   "completion": 15.00},
    "claude-3-5-haiku-20241022":    {"prompt": 0.80,   "completion": 4.00},
    "claude-3-opus-20240229":       {"prompt": 15.00,  "completion": 75.00},
    "claude-sonnet-4-6":            {"prompt": 3.00,   "completion": 15.00},
    "gemini-1.5-pro":               {"prompt": 1.25,   "completion": 5.00},
    "gemini-1.5-flash":             {"prompt": 0.075,  "completion": 0.30},
    "gemini-2.0-flash":             {"prompt": 0.10,   "completion": 0.40},
}

# In-process cache populated from DB at runtime
_cache: dict[str, Any] = {"rates": {}, "expires_at": 0.0}
_CACHE_TTL = 300  # 5 minutes


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    *,
    db_rates: dict[str, dict[str, float]] | None = None,
) -> float:
    """
    Return cost in USD.

    db_rates (optional): dict of {model: {prompt: float, completion: float}} fetched
    from the pricing_table by the caller. Falls back to _FALLBACK_RATES if the model
    isn't present in either source.
    """
    rates = (db_rates or {}).get(model) or _FALLBACK_RATES.get(model)
    if rates is None:
        # Unknown model — charge at gpt-4o rates as a conservative estimate
        rates = _FALLBACK_RATES["gpt-4o"]

    cost = (
        prompt_tokens * rates["prompt"] + completion_tokens * rates["completion"]
    ) / 1_000_000
    return round(cost, 8)


def get_cached_db_rates() -> dict[str, dict[str, float]]:
    """Return in-process cached rates. Empty dict if cache is cold (pre-first DB fetch)."""
    if time.monotonic() < _cache["expires_at"]:
        return _cache["rates"]
    return {}


def update_rate_cache(rows: list[Any]) -> None:
    """
    Populate the in-process cache from ModelPricing ORM rows fetched by the proxy router.
    Called once per cache TTL period — not on every request.
    """
    _cache["rates"] = {
        row.model: {"prompt": row.prompt_cost_per_1m, "completion": row.completion_cost_per_1m}
        for row in rows
    }
    _cache["expires_at"] = time.monotonic() + _CACHE_TTL
