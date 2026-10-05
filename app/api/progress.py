from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.progress import ProgressResponse, ProgressSnapshotResponse
from app.models.progress_snapshot import ProgressSnapshot

router = APIRouter()


@router.get("", response_model=ProgressResponse)
async def get_progress(
    period: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get player progress snapshots over a time period."""
    query = select(ProgressSnapshot).where(
        ProgressSnapshot.user_id == current_user.id
    ).order_by(ProgressSnapshot.snapshot_date.asc())

    if period != "all":
        days = {"7d": 7, "30d": 30, "90d": 90}[period]
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.where(ProgressSnapshot.snapshot_date >= cutoff)

    result = await db.execute(query)
    snapshots = result.scalars().all()

    return ProgressResponse(
        period=period,
        snapshots=[
            ProgressSnapshotResponse(
                date=s.snapshot_date.isoformat() if s.snapshot_date else "",
                overall_score=s.overall_score,
                technique_score=s.technique_score,
                movement_score=s.movement_score,
                serve_score=s.serve_score,
                consistency_score=s.consistency_score,
            )
            for s in snapshots
        ],
    )
