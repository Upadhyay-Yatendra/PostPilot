import logging
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from app.config import SCRAPER_SERVICE_URL
from app.utils.proxy import call_service
from app.utils.jwt import get_jwt_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scraper", tags=["Scraper"])

# === Profile posts ===
@router.get("/profile/posts")
async def proxy_profile_posts(
    profile_url: str = Query(...),
    n_posts: int = Query(10),
    user=Depends(get_jwt_user)
):
    logger.info(f"Profile posts request - User: {user.get('email', 'unknown')}, URL: {profile_url}, Posts: {n_posts}")
    
    try:
        return await call_service(
            "get",
            f"{SCRAPER_SERVICE_URL}/scraper/profile/posts",
            params={"profile_url": profile_url, "n_posts": n_posts},
            service_name="scraper",
            timeout=120  # Increase to 2 minutes for scraping operations
        )
    except HTTPException:
        # Re-raise HTTPExceptions from call_service (they already have proper error formatting)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in proxy_profile_posts: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": {
                    "code": "PROXY_ERROR",
                    "message": f"Unexpected error in scraper proxy: {str(e)}",
                    "status": 500,
                    "service": "scraper",
                }
            }
        )


# === Hashtag posts ===
@router.get("/hashtag/posts")
async def proxy_hashtag_posts(
    hashtag: str = Query(...),
    n_posts: int = Query(5),
    user=Depends(get_jwt_user)
):
    logger.info(f"Hashtag posts request - User: {user.get('email', 'unknown')}, Hashtag: {hashtag}, Posts: {n_posts}")
    
    try:
        return await call_service(
            "get",
            f"{SCRAPER_SERVICE_URL}/scraper/hashtag/posts",
            params={"hashtag": hashtag, "n_posts": n_posts},
            service_name="scraper", 
            timeout=120 # Increase to 2 minutes for scraping operations
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in proxy_hashtag_posts: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": {
                    "code": "PROXY_ERROR",
                    "message": f"Unexpected error in scraper proxy: {str(e)}",
                    "status": 500,
                    "service": "scraper"
                }
            }
        )