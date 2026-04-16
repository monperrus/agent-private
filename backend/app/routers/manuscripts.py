import uuid
import os
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import aiofiles
from ..database import get_db
from ..models import User, Manuscript, ManuscriptFile, ManuscriptAuthor, ManuscriptStatus, UserRole, Notification
from ..schemas import ManuscriptCreate, ManuscriptOut, ManuscriptListOut, ManuscriptUpdate, AssignEditorRequest
from ..auth import get_current_user
from ..config import settings

router = APIRouter(prefix="/api/manuscripts", tags=["manuscripts"])


def generate_submission_number(count: int) -> str:
    year = datetime.now().year
    return f"MS-{year}-{count:04d}"


async def notify_user(db: AsyncSession, user_id: uuid.UUID, title: str, message: str, notif_type: str, manuscript_id: uuid.UUID = None):
    n = Notification(user_id=user_id, title=title, message=message, type=notif_type, manuscript_id=manuscript_id)
    db.add(n)


@router.post("/", response_model=ManuscriptOut, status_code=201)
async def submit_manuscript(
    manuscript_data: str = Form(...),
    manuscript_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = ManuscriptCreate.model_validate_json(manuscript_data)

    # Count existing manuscripts for submission number
    count_result = await db.execute(select(func.count(Manuscript.id)))
    count = count_result.scalar() + 1

    manuscript = Manuscript(
        title=data.title,
        abstract=data.abstract,
        keywords=data.keywords,
        cover_letter=data.cover_letter,
        submitter_id=current_user.id,
        submission_number=generate_submission_number(count),
        status=ManuscriptStatus.submitted,
    )
    db.add(manuscript)
    await db.flush()

    # Add authors
    for author_data in data.authors:
        author = ManuscriptAuthor(
            manuscript_id=manuscript.id,
            **author_data.model_dump()
        )
        db.add(author)

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_ext = os.path.splitext(manuscript_file.filename)[1]
    stored_filename = f"{manuscript.id}_v{manuscript.version}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)
    content = await manuscript_file.read()
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    mf = ManuscriptFile(
        manuscript_id=manuscript.id,
        filename=stored_filename,
        original_filename=manuscript_file.filename,
        file_type="manuscript",
        file_size=len(content),
    )
    db.add(mf)

    # Notify editors
    editors = await db.execute(
        select(User).where(User.role.in_([UserRole.editor_in_chief, UserRole.editor]))
    )
    for editor in editors.scalars().all():
        await notify_user(db, editor.id, "New Manuscript Submitted",
                         f"A new manuscript '{data.title}' has been submitted by {current_user.full_name}.",
                         "submission", manuscript.id)

    await db.flush()
    result = await db.execute(
        select(Manuscript)
        .options(
            selectinload(Manuscript.submitter),
            selectinload(Manuscript.handling_editor),
            selectinload(Manuscript.authors),
            selectinload(Manuscript.files),
        )
        .where(Manuscript.id == manuscript.id)
    )
    return result.scalar_one()


@router.get("/", response_model=List[ManuscriptListOut])
async def list_manuscripts(
    status: Optional[ManuscriptStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = select(Manuscript).options(
        selectinload(Manuscript.submitter),
        selectinload(Manuscript.handling_editor),
    )
    if current_user.role == UserRole.author:
        q = q.where(Manuscript.submitter_id == current_user.id)
    elif current_user.role == UserRole.editor:
        q = q.where(Manuscript.handling_editor_id == current_user.id)
    elif current_user.role == UserRole.reviewer:
        from ..models import Review, ReviewStatus
        subq = select(Review.manuscript_id).where(Review.reviewer_id == current_user.id)
        q = q.where(Manuscript.id.in_(subq))

    if status:
        q = q.where(Manuscript.status == status)

    q = q.order_by(Manuscript.submitted_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{manuscript_id}", response_model=ManuscriptOut)
async def get_manuscript(
    manuscript_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Manuscript)
        .options(
            selectinload(Manuscript.submitter),
            selectinload(Manuscript.handling_editor),
            selectinload(Manuscript.authors),
            selectinload(Manuscript.files),
        )
        .where(Manuscript.id == manuscript_id)
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Access control
    if current_user.role == UserRole.author and manuscript.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return manuscript


@router.post("/{manuscript_id}/assign-editor", response_model=ManuscriptOut)
async def assign_editor(
    manuscript_id: uuid.UUID,
    req: AssignEditorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.editor_in_chief, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await db.execute(select(Manuscript).where(Manuscript.id == manuscript_id))
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    editor_result = await db.execute(select(User).where(User.id == req.editor_id))
    editor = editor_result.scalar_one_or_none()
    if not editor or editor.role not in [UserRole.editor, UserRole.editor_in_chief]:
        raise HTTPException(status_code=400, detail="Invalid editor")

    manuscript.handling_editor_id = req.editor_id
    manuscript.status = ManuscriptStatus.with_editor

    await notify_user(db, req.editor_id, "Manuscript Assigned",
                     f"Manuscript '{manuscript.title}' ({manuscript.submission_number}) has been assigned to you.",
                     "assignment", manuscript_id)

    await db.flush()
    result = await db.execute(
        select(Manuscript)
        .options(
            selectinload(Manuscript.submitter),
            selectinload(Manuscript.handling_editor),
            selectinload(Manuscript.authors),
            selectinload(Manuscript.files),
        )
        .where(Manuscript.id == manuscript_id)
    )
    return result.scalar_one()


@router.post("/{manuscript_id}/withdraw")
async def withdraw_manuscript(
    manuscript_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Manuscript).where(Manuscript.id == manuscript_id))
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    if manuscript.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if manuscript.status in [ManuscriptStatus.accepted, ManuscriptStatus.published]:
        raise HTTPException(status_code=400, detail="Cannot withdraw accepted/published manuscript")

    manuscript.status = ManuscriptStatus.withdrawn
    await db.flush()
    return {"message": "Manuscript withdrawn"}
