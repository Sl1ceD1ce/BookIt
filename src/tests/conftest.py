import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from server import app
from database import Base, get_db

 
engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def reset_db():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    """Yields a raw DB session for direct manipulation in tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def default_start():
    return datetime.now() + timedelta(minutes=60)

@pytest.fixture
def default_end(default_start):
    return default_start + timedelta(minutes=60)

@pytest.fixture
def register_user(client):
    """Returns a helper function to register a user and get their token."""
    def _register(
        first_name: str = "John",
        last_name: str = "Doe",
        email: str = "john@example.com",
        password: str = "Password123_",
        mobile: str = "0412345678",
        tutor: bool = True
    ) -> str:
        res = client.post(
            "/users/register",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password,
                "mobile": mobile,
                "tutor": tutor,
            },
        )
        assert res.status_code == 201, f"Registration failed: {res.json()}"
        return res.json()["token"]
    return _register

@pytest.fixture
def post_lesson(client):
    """Returns a helper function to create a lesson."""
    def _post(token: str, start: datetime, end: datetime, subject: str = "Math"):
        return client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "subject": subject,
            },
        )
    return _post

@pytest.fixture
def tutor_token(register_user):
    """A registered tutor's token."""
    return register_user(tutor=True)

@pytest.fixture
def student_token(register_user):
    """A registered student's token."""
    return register_user(tutor=False, email="student@example.com", mobile="0412345679")

@pytest.fixture
def lesson_id(post_lesson, tutor_token, default_start, default_end):
    """A created lesson's ID, owned by tutor_token."""
    res = post_lesson(tutor_token, default_start, default_end)
    assert res.status_code == 201
    return res.json()["lesson_id"]

@pytest.fixture
def booked_lesson(client, post_lesson, tutor_token, student_token, default_start, default_end):
    """A lesson created by tutor_token and booked by student_token.
    Returns (tutor_token, student_token, lesson_data dict).
    """
    res = post_lesson(tutor_token, default_start, default_end)
    assert res.status_code == 201
    lesson = res.json()
 
    book_res = client.post(
        f"/lessons/{lesson['lesson_id']}/book",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert book_res.status_code == 200
 
    return tutor_token, student_token, book_res.json()