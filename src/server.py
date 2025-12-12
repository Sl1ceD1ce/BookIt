from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import dataStore as ds
import auth
from schemas import UserRegister, UserResponse

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    ds.load_data()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/users/register", response_model=UserResponse, status_code=201)
async def register_user_route(user_data: UserRegister):
    """Register a new user (student or tutor)."""
    try:
        response = auth.register_user(user_data.model_dump())
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))