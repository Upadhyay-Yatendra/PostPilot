from fastapi import APIRouter, Request, Depends
from app.config import SCRAPER_SERVICE_URL
from app.utils.proxy import call_service
from app.utils.jwt import get_jwt_user

router = APIRouter()

@router.get("/scrape")
async def trigger_scrape(request: Request, user=Depends(get_jwt_user)):
    params = dict(request.query_params)
    result = await call_service("get", f"{SCRAPER_SERVICE_URL}/scrape", params=params)
    return result
