import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import User, UserRole
from ..schemas import UserOut, UserUpdate, UserAdminUpdate
from ..auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=List[UserOut])
async def list_users(
    role: UserRole = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    q = select(User)
    if role:
        q = q.where(User.role == role)
    result = await db.execute(q.order_by(User.full_name))
    return result.scalars().all()


@router.get("/reviewers", response_model=List[UserOut])
async def list_reviewers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.editor, UserRole.editor_in_chief, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    result = await db.execute(select(User).where(User.role == UserRole.reviewer).order_by(User.full_name))
    return result.scalars().all()


@router.get("/editors", response_model=List[UserOut])
async def list_editors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.editor_in_chief, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    result = await db.execute(
        select(User).where(User.role.in_([UserRole.editor, UserRole.editor_in_chief])).order_by(User.full_name)
    )
    return result.scalars().all()


@router.put("/me", response_model=UserOut)
async def update_me(
    updates: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    updates: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user
