from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import verify_api_key
from models import Trace
from schemas import TraceDetailResponse, TraceListResponse, TraceResponse

router = APIRouter(prefix="/v1/traces", tags=["Traces"])


def _to_response(trace: Trace) -> TraceResponse:
    return TraceResponse.model_validate(trace)


def _to_detail(trace: Trace) -> TraceDetailResponse:
    return TraceDetailResponse.model_validate(trace)


@router.get("", response_model=TraceListResponse)
async def list_traces(
    model: str | None = Query(None),
    user_id: str | None = Query(None),
    feature: str | None = Query(None),
    status: str | None = Query(None),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> TraceListResponse:
    q = select(Trace)
    if model:
        q = q.where(Trace.model == model)
    if user_id:
        q = q.where(Trace.user_id == user_id)
    if feature:
        q = q.where(Trace.feature == feature)
    if status:
        q = q.where(Trace.status == status)
    if from_date:
        q = q.where(Trace.created_at >= from_date)
    if to_date:
        q = q.where(Trace.created_at <= to_date)

    # total count with same filters (without pagination)
    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q) or 0

    q = q.order_by(Trace.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    traces = result.scalars().all()

    return TraceListResponse(traces=[_to_response(t) for t in traces], total=total)


@router.get("/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> TraceDetailResponse:
    result = await db.execute(select(Trace).where(Trace.trace_id == trace_id))
    trace = result.scalar_one_or_none()
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found.")
    return _to_detail(trace)
