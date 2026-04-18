import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import verify_api_key
from models import ApiKey, ModelPricing

router = APIRouter(prefix="/v1/settings", tags=["Settings"])


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    raw_key: str
    created_at: str

    class Config:
        from_attributes = True


class ApiKeyListResponse(BaseModel):
    id: str
    name: str
    created_at: str
    last_used_at: str | None

    class Config:
        from_attributes = True


class PricingResponse(BaseModel):
    id: str
    model: str
    provider: str
    prompt_cost_per_1m: float
    completion_cost_per_1m: float
    updated_at: str

    class Config:
        from_attributes = True


class PricingUpdate(BaseModel):
    prompt_cost_per_1m: float
    completion_cost_per_1m: float


@router.get("/api-keys", response_model=list[ApiKeyListResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> list[ApiKeyListResponse]:
    result = await db.execute(select(ApiKey).order_by(ApiKey.created_at))
    keys = result.scalars().all()
    return [
        ApiKeyListResponse(
            id=str(k.id),
            name=k.name,
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in keys
    ]


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> ApiKeyCreateResponse:
    if not data.name.strip():
        raise HTTPException(400, "name must not be empty")
    raw = f"arop-{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    api_key = ApiKey(name=data.name.strip(), key_hash=key_hash)
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return ApiKeyCreateResponse(
        id=str(api_key.id),
        name=api_key.name,
        raw_key=raw,
        created_at=api_key.created_at.isoformat(),
    )


@router.get("/pricing", response_model=list[PricingResponse])
async def list_pricing(
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> list[PricingResponse]:
    result = await db.execute(select(ModelPricing).order_by(ModelPricing.model))
    rows = result.scalars().all()
    return [
        PricingResponse(
            id=str(r.id),
            model=r.model,
            provider=r.provider,
            prompt_cost_per_1m=r.prompt_cost_per_1m,
            completion_cost_per_1m=r.completion_cost_per_1m,
            updated_at=r.updated_at.isoformat(),
        )
        for r in rows
    ]


@router.patch("/pricing/{model}", response_model=PricingResponse)
async def update_pricing(
    model: str,
    data: PricingUpdate,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> PricingResponse:
    result = await db.execute(select(ModelPricing).where(ModelPricing.model == model))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, f"Model '{model}' not found in pricing table")
    row.prompt_cost_per_1m = data.prompt_cost_per_1m
    row.completion_cost_per_1m = data.completion_cost_per_1m
    await db.commit()
    await db.refresh(row)
    return PricingResponse(
        id=str(row.id),
        model=row.model,
        provider=row.provider,
        prompt_cost_per_1m=row.prompt_cost_per_1m,
        completion_cost_per_1m=row.completion_cost_per_1m,
        updated_at=row.updated_at.isoformat(),
    )
