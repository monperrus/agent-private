import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import User, Manuscript, Decision, ManuscriptStatus, UserRole, Notification, DecisionType
from ..schemas import DecisionCreate, DecisionOut
from ..auth import get_current_user

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.post("/manuscript/{manuscript_id}", response_model=DecisionOut, status_code=201)
async def make_decision(
    manuscript_id: uuid.UUID,
    decision_data: DecisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.editor, UserRole.editor_in_chief, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    ms_result = await db.execute(select(Manuscript).where(Manuscript.id == manuscript_id))
    manuscript = ms_result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Map decision to status
    status_map = {
        DecisionType.accept: ManuscriptStatus.accepted,
        DecisionType.minor_revision: ManuscriptStatus.revisions_requested,
        DecisionType.major_revision: ManuscriptStatus.revisions_requested,
        DecisionType.reject: ManuscriptStatus.rejected,
    }
    manuscript.status = status_map[decision_data.decision]

    decision = Decision(
        manuscript_id=manuscript_id,
        editor_id=current_user.id,
        decision=decision_data.decision,
        comments_to_author=decision_data.comments_to_author,
        comments_to_editor=decision_data.comments_to_editor,
    )
    db.add(decision)

    # Notify author
    n = Notification(
        user_id=manuscript.submitter_id,
        title="Decision on Your Manuscript",
        message=f"A decision has been made on your manuscript '{manuscript.title}': {decision_data.decision.value.replace('_', ' ').title()}",
        type="decision",
        manuscript_id=manuscript_id
    )
    db.add(n)

    await db.flush()
    result = await db.execute(
        select(Decision).options(selectinload(Decision.editor)).where(Decision.id == decision.id)
    )
    return result.scalar_one()


@router.get("/manuscript/{manuscript_id}", response_model=List[DecisionOut])
async def get_manuscript_decisions(
    manuscript_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ms_result = await db.execute(select(Manuscript).where(Manuscript.id == manuscript_id))
    manuscript = ms_result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Authors can only see their own manuscripts
    if current_user.role == UserRole.author and manuscript.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(Decision).options(selectinload(Decision.editor))
        .where(Decision.manuscript_id == manuscript_id)
        .order_by(Decision.created_at.desc())
    )
    return result.scalars().all()
