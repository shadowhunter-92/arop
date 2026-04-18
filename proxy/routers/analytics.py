"""
GET /v1/analytics/cost — aggregated cost and usage metrics.

Returns three views over the same dataset:
  - over_time   : daily cost + token + call-count timeseries (line chart data)
  - by_model    : cost breakdown per model (pie chart data)
  - by_feature  : cost breakdown per feature tag (bar chart data)

Uses raw SQL via SQLAlchemy text() for the GROUP BY aggregations — the ORM
adds no value here and raw SQL is clearer and easier to tune.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import verify_api_key
from schemas import (
    CostAnalyticsResponse,
    CostByFeature,
    CostByModel,
    CostDataPoint,
)

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get("/cost", response_model=CostAnalyticsResponse)
async def get_cost_analytics(
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
    _key_id: str = Depends(verify_api_key),
) -> CostAnalyticsResponse:
    now = datetime.now(timezone.utc)
    start = from_date or (now - timedelta(days=30))
    end = to_date or now

    params = {"start": start, "end": end}

    # ── Daily timeseries ──────────────────────────────────────────────────────
    rows = await db.execute(
        text("""
            SELECT
                DATE_TRUNC('day', created_at)::date::text  AS day,
                COALESCE(SUM(cost_usd), 0)                 AS cost_usd,
                COALESCE(SUM(total_tokens), 0)             AS total_tokens,
                COUNT(*)                                   AS call_count
            FROM traces
            WHERE created_at >= :start
              AND created_at <= :end
              AND status != 'blocked'
            GROUP BY 1
            ORDER BY 1
        """),
        params,
    )
    over_time = [
        CostDataPoint(
            date=r.day,
            cost_usd=float(r.cost_usd),
            total_tokens=int(r.total_tokens),
            call_count=int(r.call_count),
        )
        for r in rows
    ]

    # ── By model ──────────────────────────────────────────────────────────────
    rows = await db.execute(
        text("""
            SELECT
                model,
                COALESCE(SUM(cost_usd), 0) AS cost_usd,
                COUNT(*)                   AS call_count
            FROM traces
            WHERE created_at >= :start
              AND created_at <= :end
              AND status != 'blocked'
            GROUP BY model
            ORDER BY cost_usd DESC
        """),
        params,
    )
    by_model = [
        CostByModel(model=r.model, cost_usd=float(r.cost_usd), call_count=int(r.call_count))
        for r in rows
    ]

    # ── By feature ────────────────────────────────────────────────────────────
    rows = await db.execute(
        text("""
            SELECT
                COALESCE(feature, '(untagged)')  AS feature,
                COALESCE(SUM(cost_usd), 0)       AS cost_usd,
                COUNT(*)                          AS call_count
            FROM traces
            WHERE created_at >= :start
              AND created_at <= :end
              AND status != 'blocked'
            GROUP BY feature
            ORDER BY cost_usd DESC
        """),
        params,
    )
    by_feature = [
        CostByFeature(feature=r.feature, cost_usd=float(r.cost_usd), call_count=int(r.call_count))
        for r in rows
    ]

    # ── Totals ────────────────────────────────────────────────────────────────
    total_row = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(cost_usd), 0) AS cost_usd,
                COUNT(*)                   AS call_count
            FROM traces
            WHERE created_at >= :start
              AND created_at <= :end
              AND status != 'blocked'
        """),
        params,
    )
    totals = total_row.one()

    return CostAnalyticsResponse(
        over_time=over_time,
        by_model=by_model,
        by_feature=by_feature,
        total_cost_usd=float(totals.cost_usd),
        total_calls=int(totals.call_count),
    )
