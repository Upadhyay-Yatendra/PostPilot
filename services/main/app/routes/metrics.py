from fastapi import APIRouter, Request, Depends, Query
from app.config import SCRAPER_SERVICE_URL
from app.utils.proxy import call_service
from app.utils.jwt import get_jwt_user

router = APIRouter()

@router.get("/engagement")
async def user_engagement(
    request: Request,
    profile_url: str = Query(...),
    n_posts: int = Query(10),
    user=Depends(get_jwt_user)
):
    # Get the user's top posts from Scraper service
    params = {"profile_url": profile_url, "n_posts": n_posts}
    posts_data = await call_service("get", f"{SCRAPER_SERVICE_URL}/api/v1/scrape/profile/posts", params=params)
    # Do further analytics/aggregation here, or just return
    return posts_data
