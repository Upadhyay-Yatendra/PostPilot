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

@router.get("/me")
async def me(request: Request):
    headers = dict(request.headers)
    result = await call_service(
        "get",
        f"{AUTH_SERVICE_URL}/me",
        headers=headers,
        service_name="auth"
    )
    return result
