import os
from sqlalchemy import create_engine, Column, String, Boolean, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://bookit:bookit_pass@localhost:5432/bookit_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    mobile = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "tutor" or "student"


class Lesson(Base):
    __tablename__ = "lessons"

    lesson_id = Column(String, primary_key=True)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    tutor_id = Column(String, nullable=False)
    assigned_student_id = Column(String, nullable=True)
    available = Column(Boolean, default=True)


class InvalidatedToken(Base):
    __tablename__ = "invalidated_tokens"

    token = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    invalidated_at = Column(String, nullable=False)


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