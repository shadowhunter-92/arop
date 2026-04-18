import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Trace(Base):
    __tablename__ = "traces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    feature: Mapped[str | None] = mapped_column(String, nullable=True)
    model: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    # request_body/response_body are NULL when hash_payloads=True and store_raw=False.
    # This is the privacy-safe default: no plaintext ever touches the AROP database.
    request_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    response_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # success | blocked | error
    guardrail_hits: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    parent_trace_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # custom_score: user-defined success metric (0.0–1.0) posted via POST /v1/evaluate.
    # Enables teams to push their own ground-truth signal (thumbs up/down, ROUGE, etc.)
    # back into AROP so the platform goes beyond latency/cost into actual quality tracking.
    custom_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_storage_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Guardrail(Base):
    __tablename__ = "guardrails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)    # pre_request | post_response
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False, default="block")  # block | redact
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModelPricing(Base):
    """
    Risk mitigation: accurate cost estimation.
    Storing pricing in the DB (not hardcoded) means we can update costs without a deploy
    when providers change their pricing. LangSmith's known cost inaccuracy stems from
    stale hardcoded tables — this design lets any admin update pricing live.
    """
    __tablename__ = "pricing_table"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    # Cost per 1 million tokens in USD
    prompt_cost_per_1m: Mapped[float] = mapped_column(Float, nullable=False)
    completion_cost_per_1m: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
