from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import dataStore as ds
import auth
import lessons
from schemas import (
    UserRegister,
    UserResponse,
    UserLogin,
    UserLoginResponse,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
)
from contextlib import asynccontextmanager
from typing import List

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@asynccontextmanager
async def startup_event():
    ds.load_data()
    yield  # makes all code before it execute at startup and everything after at shutdown


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/users/register", response_model=UserResponse, status_code=201)
async def register_user_route(user_data: UserRegister):
    """Register a new user (student or tutor)."""
    try:
        response = auth.register_user(user_data)
        ds.save_data()

        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/login", response_model=UserLoginResponse, status_code=200)
async def login_user_route(login_data: UserLogin):
    """Login an existing user (student or tutor)."""
    try:
        return auth.login_user(login_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/logout", status_code=200)
async def logout_user_route(token: str = Depends(oauth2_scheme)):
    """Logout an user"""
    try:
        res = auth.logout_user(token)
        ds.save_data()

        return res
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@app.delete("/users", status_code=200)
async def logout_user_route(token: str = Depends(oauth2_scheme)):
    """Delete a user"""
    try:
        res = auth.delete_user(token)
        ds.save_data()

        return res
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/users", status_code=200)
async def get_user_route(token: str = Depends(oauth2_scheme)):
    try:
        return auth.get_users(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/lessons/{lesson_id}/book", response_model=LessonResponse, status_code=200)
async def lesson_book(lesson_id: str, token: str = Depends(oauth2_scheme)):
    res = lessons.book_lesson(token, lesson_id)
    ds.save_data()
    return res


@app.post("/lessons", response_model=LessonResponse, status_code=201)
async def lesson_create(lesson_data: LessonCreate, token: str = Depends(oauth2_scheme)):
    try:
        res = lessons.create_lesson(token, lesson_data)
        ds.save_data()

        return res
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/lessons", response_model=List[LessonResponse], status_code=200)
async def lesson_get(token: str = Depends(oauth2_scheme)):
    try:
        res = lessons.get_user_lessons(token)
        return res
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.patch("/lessons/{lesson_id}", status_code=200)
async def lesson_update(
    update_data: LessonUpdate, lesson_id: str, token: str = Depends(oauth2_scheme)
):
    try:
        res = lessons.update_lesson(token, lesson_id, update_data)
        ds.save_data()

        return res
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    

@app.delete("/lessons/{lesson_id}", status_code=200)
async def lesson_update(
    lesson_id: str, token: str = Depends(oauth2_scheme)
):
    try:
        res = lessons.delete_lesson(token, lesson_id)
        ds.save_data()

        return res
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
