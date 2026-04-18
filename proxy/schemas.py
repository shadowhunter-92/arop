import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ── Traces ────────────────────────────────────────────────────────────────────

class TraceResponse(BaseModel):
    id: uuid.UUID
    trace_id: str
    user_id: str | None
    feature: str | None
    model: str
    provider: str
    latency_ms: int | None
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    cost_usd: float | None
    status: str
    guardrail_hits: list[str] | None
    parent_trace_id: str | None
    # custom_score reflects a user-posted quality signal (0.0–1.0).
    # Null until a POST /v1/evaluate updates it.
    custom_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TraceDetailResponse(TraceResponse):
    request_body: dict[str, Any] | None   # None when hash_payloads=True, store_raw=False
    response_body: dict[str, Any] | None
    prompt_hash: str | None
    response_hash: str | None


class TraceListResponse(BaseModel):
    traces: list[TraceResponse]
    total: int


# ── Guardrails ────────────────────────────────────────────────────────────────

class GuardrailCreate(BaseModel):
    name: str
    type: str       # pre_request | post_response
    pattern: str
    action: str = "block"   # block | redact


class GuardrailResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    pattern: str
    action: str
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class GuardrailToggle(BaseModel):
    enabled: bool


# ── Replay ────────────────────────────────────────────────────────────────────

class ReplayRequest(BaseModel):
    trace_id: str
    model_override: str | None = None
    prompt_override: list[dict[str, Any]] | None = None  # full messages array


class ReplayResponse(BaseModel):
    original_trace: TraceDetailResponse
    replay_response: dict[str, Any]
    replay_trace_id: str
    model_used: str
    latency_ms: int
    cost_usd: float


# ── Analytics ─────────────────────────────────────────────────────────────────

class CostDataPoint(BaseModel):
    date: str
    cost_usd: float
    total_tokens: int
    call_count: int


class CostByModel(BaseModel):
    model: str
    cost_usd: float
    call_count: int


class CostByFeature(BaseModel):
    feature: str
    cost_usd: float
    call_count: int


class CostAnalyticsResponse(BaseModel):
    over_time: list[CostDataPoint]
    by_model: list[CostByModel]
    by_feature: list[CostByFeature]
    total_cost_usd: float
    total_calls: int


# ── Chat completions (proxy endpoint mirrors OpenAI format) ───────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    user: str | None = None

    model_config = {"extra": "allow"}   # pass unknown fields through to provider


# ── Evaluate (custom quality signal) ─────────────────────────────────────────

class EvaluateRequest(BaseModel):
    trace_id: str
    score: float        # 0.0 (failure) to 1.0 (success)
    label: str | None = None   # optional human-readable label, e.g. "thumbs_up"


class EvaluateResponse(BaseModel):
    trace_id: str
    custom_score: float
    label: str | None


# ── Pricing ───────────────────────────────────────────────────────────────────

class ModelPricingResponse(BaseModel):
    model: str
    provider: str
    prompt_cost_per_1m: float
    completion_cost_per_1m: float
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── API Keys ──────────────────────────────────────────────────────────────────

class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}
