from fastapi import APIRouter, Request, Depends
from app.config import POSTGEN_SERVICE_URL
from app.utils.proxy import call_service
from app.utils.jwt import get_jwt_user

router = APIRouter()

@router.post("/generate-post")
async def generate_post(request: Request, user=Depends(get_jwt_user)):
    data = await request.json()
    data["user_id"] = user["user_id"]  # Assuming JWT includes user_id
    result = await call_service("post", f"{POSTGEN_SERVICE_URL}/generate", json=data)
    return result
