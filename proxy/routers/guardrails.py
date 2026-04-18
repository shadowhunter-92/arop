import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import verify_api_key
from models import Guardrail
from schemas import GuardrailCreate, GuardrailResponse, GuardrailToggle
from services.trace_logger import invalidate_guardrail_cache

router = APIRouter(prefix="/v1/guardrails", tags=["Guardrails"])

_VALID_TYPES = {"pre_request", "post_response"}
_VALID_ACTIONS = {"block", "redact"}


def _validate(data: GuardrailCreate) -> None:
    if data.type not in _VALID_TYPES:
        raise HTTPException(400, f"type must be one of {_VALID_TYPES}")
    if data.action not in _VALID_ACTIONS:
        raise HTTPException(400, f"action must be one of {_VALID_ACTIONS}")
    try:
        re.compile(data.pattern)
    except re.error as e:
        raise HTTPException(400, f"Invalid regex pattern: {e}")


@router.get("", response_model=list[GuardrailResponse])
async def list_guardrails(
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> list[GuardrailResponse]:
    result = await db.execute(select(Guardrail).order_by(Guardrail.created_at))
    return [GuardrailResponse.model_validate(g) for g in result.scalars().all()]


@router.post("", response_model=GuardrailResponse, status_code=201)
async def create_guardrail(
    data: GuardrailCreate,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> GuardrailResponse:
    _validate(data)
    guardrail = Guardrail(
        name=data.name,
        type=data.type,
        pattern=data.pattern,
        action=data.action,
        enabled=True,
    )
    db.add(guardrail)
    await db.commit()
    await db.refresh(guardrail)
    invalidate_guardrail_cache()
    return GuardrailResponse.model_validate(guardrail)


@router.patch("/{guardrail_id}/toggle", response_model=GuardrailResponse)
async def toggle_guardrail(
    guardrail_id: uuid.UUID,
    data: GuardrailToggle,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> GuardrailResponse:
    result = await db.execute(select(Guardrail).where(Guardrail.id == guardrail_id))
    guardrail = result.scalar_one_or_none()
    if guardrail is None:
        raise HTTPException(404, f"Guardrail '{guardrail_id}' not found.")
    guardrail.enabled = data.enabled
    await db.commit()
    await db.refresh(guardrail)
    invalidate_guardrail_cache()
    return GuardrailResponse.model_validate(guardrail)


@router.delete("/{guardrail_id}", status_code=204)
async def delete_guardrail(
    guardrail_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> None:
    result = await db.execute(select(Guardrail).where(Guardrail.id == guardrail_id))
    guardrail = result.scalar_one_or_none()
    if guardrail is None:
        raise HTTPException(404, f"Guardrail '{guardrail_id}' not found.")
    await db.delete(guardrail)
    await db.commit()
    invalidate_guardrail_cache()
