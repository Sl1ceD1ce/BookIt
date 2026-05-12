import os
from typing import Optional
from sqlalchemy import create_engine, Column, String, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://bookit:bookit_pass@db:5432/bookit_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    mobile: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)


class Lesson(Base):
    __tablename__ = "lessons"

    lesson_id: Mapped[str] = mapped_column(String, primary_key=True)
    start_time: Mapped[str] = mapped_column(String, nullable=False)
    end_time: Mapped[str] = mapped_column(String, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    tutor_id: Mapped[str] = mapped_column(String, nullable=False)
    assigned_student_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)


class InvalidatedToken(Base):
    __tablename__ = "invalidated_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    invalidated_at: Mapped[str] = mapped_column(String, nullable=False)


def init_db():
    """Creates all tables if they don't exist"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yields a database session - use this with FastAPI's Depends()"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()