import uuid, datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

def uid(): return str(uuid.uuid4())
def now(): return datetime.datetime.now(datetime.timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # null for Google-only
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=now)
    identities: Mapped[list["Identity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped["Preference"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    reviews: Mapped[list["Review"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Identity(Base):
    """OAuth identity (google/github). Tokens encrypted at rest, never serialized to API."""
    __tablename__ = "identities"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)  # google | github
    provider_user_id: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(320), default="")
    username: Mapped[str] = mapped_column(String(120), default="")
    encrypted_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=now)
    user: Mapped[User] = relationship(back_populates="identities")

class Preference(Base):
    __tablename__ = "preferences"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    theme: Mapped[str] = mapped_column(String(10), default="system")  # light|dark|system
    default_language: Mapped[str] = mapped_column(String(20), default="python")
    llm_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    include_info_findings: Mapped[bool] = mapped_column(Boolean, default=True)
    user: Mapped[User] = relationship(back_populates="preferences")

class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300), default="Code review")
    source_type: Mapped[str] = mapped_column(String(20), default="paste")  # paste|upload|github_pr
    language: Mapped[str] = mapped_column(String(20), default="python")
    status: Mapped[str] = mapped_column(String(20), default="completed")  # completed|partial|failed
    source_label: Mapped[str] = mapped_column(String(300), default="")
    github_url: Mapped[str] = mapped_column(String(500), default="")
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    head_sha: Mapped[str] = mapped_column(String(64), default="")
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    user: Mapped[User] = relationship(back_populates="reviews")
    findings: Mapped[list["Finding"]] = relationship(back_populates="review", cascade="all, delete-orphan")
    files: Mapped[list["ReviewFile"]] = relationship(back_populates="review", cascade="all, delete-orphan")

class ReviewFile(Base):
    __tablename__ = "review_files"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, default="")
    review: Mapped[Review] = relationship(back_populates="files")

class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(40), default="maintainability", index=True)
    severity: Mapped[str] = mapped_column(String(20), default="low", index=True)
    confidence: Mapped[str] = mapped_column(String(10), default="medium")
    file_path: Mapped[str] = mapped_column(String(500), default="")
    start_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    remediation: Mapped[str] = mapped_column(Text, default="")
    suggested_patch: Mapped[str] = mapped_column(Text, default="")
    suggested_tests: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20), default="ast")  # ast|ruff|bandit|semgrep|llm
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified")
    rule_id: Mapped[str] = mapped_column(String(80), default="")
    review: Mapped[Review] = relationship(back_populates="findings")
