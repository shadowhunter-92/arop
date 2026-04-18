"""
POST /v1/evaluate — post a quality score for a trace.

Risk mitigation: most observability tools are "glorified uptime checkers" with no
sense of whether the AI output was actually good. This endpoint lets teams push
their own ground-truth signal back into AROP — a thumbs-up/down from the end user,
an automated ROUGE score, a human review rating — so cost and quality can be
correlated in the analytics dashboard.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import verify_api_key
from models import Trace
from schemas import EvaluateRequest, EvaluateResponse

router = APIRouter(prefix="/v1", tags=["Evaluate"])


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_trace(
    data: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> EvaluateResponse:
    if not 0.0 <= data.score <= 1.0:
        raise HTTPException(422, "score must be between 0.0 and 1.0 inclusive.")

    result = await db.execute(select(Trace).where(Trace.trace_id == data.trace_id))
    trace = result.scalar_one_or_none()
    if trace is None:
        raise HTTPException(404, f"Trace '{data.trace_id}' not found.")

    trace.custom_score = data.score
    await db.commit()

    return EvaluateResponse(
        trace_id=data.trace_id,
        custom_score=data.score,
        label=data.label,
    )
