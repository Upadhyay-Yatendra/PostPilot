from fastapi import APIRouter, Request, HTTPException
from app.config import AUTH_SERVICE_URL
from app.utils.proxy import call_service

router = APIRouter()

@router.post("/login")
async def login(request: Request):
    data = await request.json()
    result = await call_service("post", f"{AUTH_SERVICE_URL}/login", json=data , service_name="auth")
    return result

@router.post("/signup")
async def signup(request: Request):
    data = await request.json()
    result = await call_service("post", f"{AUTH_SERVICE_URL}/signup", json=data , service_name="auth")
    return result

@router.post("/logout")
async def logout(request: Request):
    data = await request.json()
    result = await call_service("post", f"{AUTH_SERVICE_URL}/logout", json=data , service_name="auth")
    return result