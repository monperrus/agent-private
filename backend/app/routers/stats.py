from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..database import get_db
from ..models import User, Manuscript, ManuscriptStatus, UserRole
from ..schemas import DashboardStats
from ..auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    base_q = select(func.count(Manuscript.id))

    if current_user.role == UserRole.author:
        base_q = base_q.where(Manuscript.submitter_id == current_user.id)
    elif current_user.role == UserRole.editor:
        base_q = base_q.where(Manuscript.handling_editor_id == current_user.id)

    total = (await db.execute(base_q)).scalar()

    def status_q(status):
        q = select(func.count(Manuscript.id)).where(Manuscript.status == status)
        if current_user.role == UserRole.author:
            q = q.where(Manuscript.submitter_id == current_user.id)
        elif current_user.role == UserRole.editor:
            q = q.where(Manuscript.handling_editor_id == current_user.id)
        return q

    pending = (await db.execute(status_q(ManuscriptStatus.submitted))).scalar()
    under_review = (await db.execute(status_q(ManuscriptStatus.under_review))).scalar()
    accepted = (await db.execute(status_q(ManuscriptStatus.accepted))).scalar()
    rejected = (await db.execute(status_q(ManuscriptStatus.rejected))).scalar()

    return DashboardStats(
        total_manuscripts=total,
        pending_review=pending,
        under_review=under_review,
        accepted=accepted,
        rejected=rejected,
    )
