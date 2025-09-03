import logging
from fastapi import APIRouter, Request, Depends
from app.config import POSTGEN_SERVICE_URL
from app.utils.proxy import call_service
from app.utils.jwt import get_jwt_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate-post")
async def generate_post(request: Request, user=Depends(get_jwt_user)):
    logger.info(f"JWT Payload received: {user}")
    logger.info(f"Available keys: {list(user.keys())}")
    
    data = await request.json()
    data["username"] = user["linkedin_username"]
    
    logger.info(f"Sending username to postgen: {data['username']}")
    logger.info(f"Full data to postgen: {data}")
    
    # FIX: Correct path + timeout
    result = await call_service(
        "post", 
        f"{POSTGEN_SERVICE_URL}/postgen/generate",  # FIXED PATH
        json=data, 
        service_name="postgen",
        timeout=300  # ADDED TIMEOUT (5 minutes)
    )
    return result