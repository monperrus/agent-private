import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import User, Manuscript, Review, ManuscriptStatus, ReviewStatus, UserRole, Notification
from ..schemas import ReviewCreate, ReviewOut, ReviewInviteRequest
from ..auth import get_current_user

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


async def notify_user(db, user_id, title, message, notif_type, manuscript_id=None):
    n = Notification(user_id=user_id, title=title, message=message, type=notif_type, manuscript_id=manuscript_id)
    db.add(n)


@router.post("/invite", response_model=ReviewOut, status_code=201)
async def invite_reviewer(
    req: ReviewInviteRequest,
    manuscript_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.editor, UserRole.editor_in_chief, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    ms_result = await db.execute(select(Manuscript).where(Manuscript.id == manuscript_id))
    manuscript = ms_result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    reviewer_result = await db.execute(select(User).where(User.id == req.reviewer_id))
    reviewer = reviewer_result.scalar_one_or_none()
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer not found")

    # Check no existing review
    existing = await db.execute(
        select(Review).where(
            Review.manuscript_id == manuscript_id,
            Review.reviewer_id == req.reviewer_id,
            Review.status != ReviewStatus.declined
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Reviewer already invited")

    review = Review(
        manuscript_id=manuscript_id,
        reviewer_id=req.reviewer_id,
        status=ReviewStatus.invited,
        due_date=req.due_date,
    )
    db.add(review)

    manuscript.status = ManuscriptStatus.under_review

    await notify_user(db, req.reviewer_id, "Review Invitation",
                     f"You have been invited to review manuscript '{manuscript.title}'. Please respond.",
                     "review_invite", manuscript_id)

    await db.flush()
    result = await db.execute(
        select(Review).options(selectinload(Review.reviewer)).where(Review.id == review.id)
    )
    return result.scalar_one()


@router.post("/{review_id}/accept")
async def accept_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review or review.reviewer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != ReviewStatus.invited:
        raise HTTPException(status_code=400, detail="Review is not in invited state")

    review.status = ReviewStatus.accepted
    review.responded_at = datetime.now(timezone.utc)
    await db.flush()
    return {"message": "Review accepted"}


@router.post("/{review_id}/decline")
async def decline_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review or review.reviewer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != ReviewStatus.invited:
        raise HTTPException(status_code=400, detail="Review is not in invited state")

    review.status = ReviewStatus.declined
    review.responded_at = datetime.now(timezone.utc)
    await db.flush()
    return {"message": "Review declined"}


@router.post("/{review_id}/submit", response_model=ReviewOut)
async def submit_review(
    review_id: uuid.UUID,
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review or review.reviewer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status not in [ReviewStatus.accepted, ReviewStatus.invited]:
        raise HTTPException(status_code=400, detail="Cannot submit review in current state")

    review.recommendation = review_data.recommendation
    review.comments_to_editor = review_data.comments_to_editor
    review.comments_to_author = review_data.comments_to_author
    review.score_overall = review_data.score_overall
    review.score_originality = review_data.score_originality
    review.score_methodology = review_data.score_methodology
    review.score_clarity = review_data.score_clarity
    review.status = ReviewStatus.submitted
    review.submitted_at = datetime.now(timezone.utc)

    # Notify editor
    ms_result = await db.execute(select(Manuscript).where(Manuscript.id == review.manuscript_id))
    manuscript = ms_result.scalar_one()
    if manuscript.handling_editor_id:
        n = Notification(
            user_id=manuscript.handling_editor_id,
            title="Review Submitted",
            message=f"A review has been submitted for manuscript '{manuscript.title}'.",
            type="review_submitted",
            manuscript_id=review.manuscript_id
        )
        db.add(n)

    await db.flush()
    result = await db.execute(
        select(Review).options(selectinload(Review.reviewer)).where(Review.id == review_id)
    )
    return result.scalar_one()


@router.get("/manuscript/{manuscript_id}", response_model=List[ReviewOut])
async def get_manuscript_reviews(
    manuscript_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.editor, UserRole.editor_in_chief, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await db.execute(
        select(Review).options(selectinload(Review.reviewer)).where(Review.manuscript_id == manuscript_id)
    )
    return result.scalars().all()


@router.get("/my", response_model=List[ReviewOut])
async def get_my_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.reviewer))
        .where(Review.reviewer_id == current_user.id)
        .order_by(Review.invited_at.desc())
    )
    return result.scalars().all()
