from fastapi import APIRouter, Request, Depends, Query, HTTPException
from app.config import SCRAPER_SERVICE_URL
from app.utils.proxy import call_service
from app.utils.jwt import get_jwt_user

router = APIRouter(prefix="/scraper", tags=["Scraper"])

# === Profile posts ===
@router.get("/profile/posts")
async def proxy_profile_posts(
    profile_url: str = Query(...),
    n_posts: int = Query(10),
    user=Depends(get_jwt_user)
):
    try:
        return await call_service(
            "get",
            f"{SCRAPER_SERVICE_URL}/scraper/profile/posts",
            params={"profile_url": profile_url, "n_posts": n_posts}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper service error: {e}")


# === Hashtag posts ===
@router.get("/hashtag/posts")
async def proxy_hashtag_posts(
    hashtag: str = Query(...),
    n_posts: int = Query(5),
    user=Depends(get_jwt_user)
):
    try:
        return await call_service(
            "get",
            f"{SCRAPER_SERVICE_URL}/scraper/scrape/hashtag/posts",
            params={"hashtag": hashtag, "n_posts": n_posts}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper service error: {e}")
