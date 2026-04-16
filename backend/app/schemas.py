from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from .models import UserRole, ManuscriptStatus, ReviewStatus, DecisionType


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    institution: Optional[str] = None
    country: Optional[str] = None
    orcid: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    institution: Optional[str] = None
    country: Optional[str] = None
    orcid: Optional[str] = None
    bio: Optional[str] = None


class UserAdminUpdate(UserUpdate):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    role: UserRole
    is_active: bool
    created_at: datetime


# Author schemas
class ManuscriptAuthorCreate(BaseModel):
    full_name: str
    email: EmailStr
    institution: Optional[str] = None
    is_corresponding: bool = False
    order: int = 0


class ManuscriptAuthorOut(ManuscriptAuthorCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# File schemas
class ManuscriptFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime


# Manuscript schemas
class ManuscriptCreate(BaseModel):
    title: str
    abstract: str
    keywords: Optional[str] = None
    cover_letter: Optional[str] = None
    authors: List[ManuscriptAuthorCreate]


class ManuscriptUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[str] = None
    cover_letter: Optional[str] = None


class ManuscriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    abstract: str
    keywords: Optional[str]
    cover_letter: Optional[str]
    status: ManuscriptStatus
    submission_number: str
    version: int
    doi: Optional[str]
    submitted_at: datetime
    updated_at: datetime
    submitter: UserOut
    handling_editor: Optional[UserOut]
    authors: List[ManuscriptAuthorOut]
    files: List[ManuscriptFileOut]


class ManuscriptListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    status: ManuscriptStatus
    submission_number: str
    version: int
    submitted_at: datetime
    updated_at: datetime
    submitter: UserOut
    handling_editor: Optional[UserOut]


# Review schemas
class ReviewCreate(BaseModel):
    recommendation: str
    comments_to_editor: Optional[str] = None
    comments_to_author: str
    score_overall: Optional[float] = None
    score_originality: Optional[float] = None
    score_methodology: Optional[float] = None
    score_clarity: Optional[float] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    manuscript_id: uuid.UUID
    reviewer_id: uuid.UUID
    status: ReviewStatus
    recommendation: Optional[str]
    comments_to_author: Optional[str]
    comments_to_editor: Optional[str]
    score_overall: Optional[float]
    score_originality: Optional[float]
    score_methodology: Optional[float]
    score_clarity: Optional[float]
    invited_at: datetime
    responded_at: Optional[datetime]
    submitted_at: Optional[datetime]
    due_date: Optional[datetime]
    reviewer: UserOut


class ReviewInviteRequest(BaseModel):
    reviewer_id: uuid.UUID
    due_date: Optional[datetime] = None


# Decision schemas
class DecisionCreate(BaseModel):
    decision: DecisionType
    comments_to_author: str
    comments_to_editor: Optional[str] = None


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    manuscript_id: uuid.UUID
    decision: DecisionType
    comments_to_author: Optional[str]
    comments_to_editor: Optional[str]
    created_at: datetime
    editor: UserOut


# Notification schemas
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    message: str
    type: str
    read: bool
    manuscript_id: Optional[uuid.UUID]
    created_at: datetime


# Assign editor
class AssignEditorRequest(BaseModel):
    editor_id: uuid.UUID


# Stats
class DashboardStats(BaseModel):
    total_manuscripts: int
    pending_review: int
    under_review: int
    accepted: int
    rejected: int
