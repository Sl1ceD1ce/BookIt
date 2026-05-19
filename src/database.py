"""Database configuration and ORM models for the Bookit application."""

import os
from typing import Optional
from sqlalchemy import create_engine, String, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://bookit:bookit_pass@db:5432/bookit_db"
)

engine = create_engine(DATABASE_URL)
# pylint: disable=invalid-name
SessionLocal = sessionmaker(bind=engine)


# pylint: disable=too-few-public-methods
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


class User(Base):  # pylint: disable=too-few-public-methods
    """User model representing a system user (tutor or student)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    mobile: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)


class Lesson(Base):  # pylint: disable=too-few-public-methods
    """Lesson model representing a tutoring lesson."""

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    start_time: Mapped[str] = mapped_column(String, nullable=False)
    end_time: Mapped[str] = mapped_column(String, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    tutor_id: Mapped[str] = mapped_column(String, nullable=False)
    assigned_student_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)


class InvalidatedToken(Base):  # pylint: disable=too-few-public-methods
    """InvalidatedToken model for tracking revoked authentication tokens."""

    __tablename__ = "invalidated_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    invalidated_at: Mapped[str] = mapped_column(String, nullable=False)


def init_db():
    """Create all database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Yield a database session for dependency injection.

    Use this with FastAPI's Depends() to inject a session into route handlers.

    Yields:
        SessionLocal: A SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
