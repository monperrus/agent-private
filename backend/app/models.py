import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, DateTime, Boolean, Integer, Float,
    ForeignKey, Enum as SAEnum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    editor_in_chief = "editor_in_chief"
    editor = "editor"
    reviewer = "reviewer"
    author = "author"


class ManuscriptStatus(str, enum.Enum):
    submitted = "submitted"
    with_editor = "with_editor"
    under_review = "under_review"
    revisions_requested = "revisions_requested"
    resubmitted = "resubmitted"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"
    published = "published"


class ReviewStatus(str, enum.Enum):
    invited = "invited"
    accepted = "accepted"
    declined = "declined"
    submitted = "submitted"


class DecisionType(str, enum.Enum):
    accept = "accept"
    minor_revision = "minor_revision"
    major_revision = "major_revision"
    reject = "reject"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    orcid: Mapped[Optional[str]] = mapped_column(String(50))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.author)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    submitted_manuscripts: Mapped[list["Manuscript"]] = relationship("Manuscript", back_populates="submitter", foreign_keys="Manuscript.submitter_id")
    assigned_manuscripts: Mapped[list["Manuscript"]] = relationship("Manuscript", back_populates="handling_editor", foreign_keys="Manuscript.handling_editor_id")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="reviewer")
    decisions: Mapped[list["Decision"]] = relationship("Decision", back_populates="editor")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="user")


class Manuscript(Base):
    __tablename__ = "manuscripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[Optional[str]] = mapped_column(String(500))
    cover_letter: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ManuscriptStatus] = mapped_column(SAEnum(ManuscriptStatus), default=ManuscriptStatus.submitted)
    submission_number: Mapped[str] = mapped_column(String(50), unique=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    doi: Mapped[Optional[str]] = mapped_column(String(200))

    submitter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    handling_editor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    submitter: Mapped["User"] = relationship("User", back_populates="submitted_manuscripts", foreign_keys=[submitter_id])
    handling_editor: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_manuscripts", foreign_keys=[handling_editor_id])
    files: Mapped[list["ManuscriptFile"]] = relationship("ManuscriptFile", back_populates="manuscript", cascade="all, delete-orphan")
    authors: Mapped[list["ManuscriptAuthor"]] = relationship("ManuscriptAuthor", back_populates="manuscript", cascade="all, delete-orphan", order_by="ManuscriptAuthor.order")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="manuscript")
    decisions: Mapped[list["Decision"]] = relationship("Decision", back_populates="manuscript", order_by="Decision.created_at")


class ManuscriptAuthor(Base):
    __tablename__ = "manuscript_authors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manuscript_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("manuscripts.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[Optional[str]] = mapped_column(String(255))
    is_corresponding: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    manuscript: Mapped["Manuscript"] = relationship("Manuscript", back_populates="authors")


class ManuscriptFile(Base):
    __tablename__ = "manuscript_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manuscript_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("manuscripts.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50))  # manuscript, supplementary, cover_letter, revision
    file_size: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    manuscript: Mapped["Manuscript"] = relationship("Manuscript", back_populates="files")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manuscript_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("manuscripts.id"), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(SAEnum(ReviewStatus), default=ReviewStatus.invited)

    # Review content
    recommendation: Mapped[Optional[str]] = mapped_column(String(50))  # accept/minor/major/reject
    comments_to_editor: Mapped[Optional[str]] = mapped_column(Text)
    comments_to_author: Mapped[Optional[str]] = mapped_column(Text)
    score_overall: Mapped[Optional[float]] = mapped_column(Float)
    score_originality: Mapped[Optional[float]] = mapped_column(Float)
    score_methodology: Mapped[Optional[float]] = mapped_column(Float)
    score_clarity: Mapped[Optional[float]] = mapped_column(Float)

    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    manuscript: Mapped["Manuscript"] = relationship("Manuscript", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User", back_populates="reviews")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manuscript_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("manuscripts.id"), nullable=False)
    editor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision: Mapped[DecisionType] = mapped_column(SAEnum(DecisionType), nullable=False)
    comments_to_author: Mapped[Optional[str]] = mapped_column(Text)
    comments_to_editor: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    manuscript: Mapped["Manuscript"] = relationship("Manuscript", back_populates="decisions")
    editor: Mapped["User"] = relationship("User", back_populates="decisions")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50))  # submission, review, decision, revision
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    manuscript_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("manuscripts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")
