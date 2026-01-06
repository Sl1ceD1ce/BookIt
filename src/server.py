from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import dataStore as ds
import auth
import lessons
from schemas import UserRegister, UserResponse, UserLogin, UserLoginResponse, LessonCreate, LessonCreateResponse
from contextlib import asynccontextmanager

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def startup_event():
    ds.load_data()
    yield # makes all code before it execute at startup and everything after at shutdown

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/users/register", response_model=UserResponse, status_code=201)
async def register_user_route(user_data: UserRegister):
    """Register a new user (student or tutor)."""
    try:
        # Pass Pydantic model directly
        response = auth.register_user(user_data)

        # Save once at the endpoint
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
async def logout_user_route(token: str  = Depends(oauth2_scheme)):
    """Logout an user"""
    try:
        return auth.logout_user(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    

@app.get("/users", status_code=200)
async def get_user_route(token: str = Depends(oauth2_scheme)):
    try: 
        return auth.get_users(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/lessons", response_model=LessonCreateResponse, status_code=201)
async def lesson_create(lesson_data: LessonCreate, token: str = Depends(oauth2_scheme)):
    try:
        return lessons.create_lesson(token, lesson_data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))