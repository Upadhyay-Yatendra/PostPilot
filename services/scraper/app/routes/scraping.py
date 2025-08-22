# routes/scraping.py
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal
from datetime import datetime, timedelta, timezone
import os
import json
from pathlib import Path
from services.scraper.app.db.mongo_db import get_database
from services.scraper.app.models.post import PostInDB
from services.scraper.app.services.linkedin_bot import LinkedInBot
from dotenv import load_dotenv


load_dotenv()
router = APIRouter()

# Directories for saving posts
DATA_DIR = "data/profile_posts"
HASHTAG_DATA_DIR = "data/hashtag_posts"
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(HASHTAG_DATA_DIR).mkdir(parents=True, exist_ok=True)

# ======== Schemas ========
Source = Literal["profile", "hashtag"]

class PostData(BaseModel):
    text: str = ""
    likes: int = 0
    comments: int = 0
    reposts: int = 0
    engagement: int = 0
    scraped_at: str
    source: Source
    profile_url: Optional[str] = None
    hashtag: Optional[str] = None


class ProfilePostsResponse(BaseModel):
    success: bool
    message: str
    total_posts: int
    posts: List[PostData]
    from_cache: bool
    execution_time_seconds: float

# ======== Helper Functions ========
async def cleanup_duplicate_posts(db: AsyncIOMotorDatabase, profile_url: Optional[str] = None):
    try:
        collection = db.posts
        match_condition = {"profile_url": profile_url.rstrip('/')} if profile_url else {}
        pipeline = [
            {"$match": match_condition} if match_condition else {"$match": {}},
            {"$group": {"_id": {"text": "$text", "source": "$source"}, "docs": {"$push": "$ROOT"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = await collection.aggregate(pipeline).to_list(length=None)
        for dup_group in duplicates:
            docs = sorted(dup_group["docs"], key=lambda x: x.get("created_at", datetime.min), reverse=True)
            keep_doc = docs[0]
            for doc in docs[1:]:
                await collection.delete_one({"_id": doc["_id"]})
        print(f"✅ Duplicate cleanup completed")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

def extract_profile_identifier(profile_url: str) -> str:
    clean_url = profile_url.rstrip('/')
    if '/in/' in clean_url:
        return clean_url.split('/in/')[-1].split('/')[0]
    elif '/company/' in clean_url:
        return clean_url.split('/company/')[-1].split('/')[0]
    else:
        return clean_url.split('/')[-1]

async def get_existing_posts_from_db(profile_url: str, n_posts: int, db: AsyncIOMotorDatabase) -> List[PostData]:
    normalized_url = profile_url.rstrip('/')
    query = {"profile_url": normalized_url, "source": "profile"}
    cursor = db.posts.find(query).sort("scraped_at", -1).limit(n_posts)
    existing_posts = await cursor.to_list(length=n_posts)
    result = []
    for p in existing_posts:
        # Ensure scraped_at is string
        scraped_at_str = p.get("scraped_at")
        if isinstance(scraped_at_str, datetime):
            scraped_at_str = scraped_at_str.isoformat()
        result.append(PostData(
            text=p.get("text", ""),
            likes=p.get("likes", 0),
            comments=p.get("comments", 0),
            reposts=p.get("reposts", 0),
            engagement=p.get("engagement", 0),
            scraped_at=scraped_at_str if scraped_at_str else datetime.utcnow().isoformat(),
            source=p.get("source", "profile"),
            profile_url=p.get("profile_url"),
            hashtag=p.get("hashtag")
        ))
    return result


async def save_hashtag_posts_to_db(posts_data: List[dict], db: AsyncIOMotorDatabase) -> List[PostData]:
    saved_posts = []
    allowed_keys = {"text", "likes", "comments", "reposts", "engagement", "scraped_at", "source", "profile_url", "hashtag"}
    for post_data in posts_data:
        post_data["created_at"] = datetime.utcnow()
        post_data["updated_at"] = None
        try:
            await db.hashtag_posts.insert_one(post_data.copy())  # Save to new collection
            # Filter only fields defined in PostData
            filtered_post = {k: v for k, v in post_data.items() if k in allowed_keys}
            saved_posts.append(PostData(**filtered_post))
        except Exception as e:
            print(f"❌ Failed to save hashtag post: {e}")
    return saved_posts

async def save_profile_posts_to_db(posts_data: List[dict], db: AsyncIOMotorDatabase) -> List[PostData]:
    saved_posts = []
    allowed_keys = {"text", "likes", "comments", "reposts", "engagement", "scraped_at", "source", "profile_url", "hashtag"}
    for post_data in posts_data:
        post_data["created_at"] = datetime.utcnow()
        post_data["updated_at"] = None
        # Convert scraped_at to string if it's datetime
        if isinstance(post_data.get("scraped_at"), datetime):
            post_data["scraped_at"] = post_data["scraped_at"].isoformat()
        try:
            await db.posts.insert_one(post_data.copy())
            # Keep only allowed keys for Pydantic PostData
            filtered_post = {k: v for k, v in post_data.items() if k in allowed_keys}
            saved_posts.append(PostData(**filtered_post))
        except Exception as e:
            print(f"❌ Failed to save post: {e}")
    return saved_posts

def save_posts_to_json(posts_data: List[dict], profile_url: str, is_hashtag: bool = False) -> str:
    identifier = extract_profile_identifier(profile_url if not is_hashtag else profile_url.replace("#", ""))
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{'hashtag' if is_hashtag else 'profile'}_{identifier}_{timestamp}.json"
    filepath = os.path.join(HASHTAG_DATA_DIR if is_hashtag else DATA_DIR, filename)
    # Convert any datetime in posts_data to string for JSON
    for post in posts_data:
        for key in ["scraped_at", "created_at"]:
            if key in post and isinstance(post[key], datetime):
                post[key] = post[key].isoformat()
    json_data = {
        "profile_url": profile_url,
        "scraped_at": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "total_posts": len(posts_data),
        "posts": posts_data
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved posts to JSON file: {filepath}")
    return filepath

# ======== Routes ========
@router.get("/profile/posts")
async def get_user_profile_posts(profile_url: str, n_posts: int = 10, db: AsyncIOMotorDatabase = Depends(get_database)):
    start_time = datetime.utcnow()
    try:
        existing_posts = await get_existing_posts_from_db(profile_url, n_posts, db)
        if existing_posts and len(existing_posts) >= n_posts:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ProfilePostsResponse(
                success=True,
                message="Posts retrieved from database cache",
                total_posts=len(existing_posts),
                posts=existing_posts,
                from_cache=True,
                execution_time_seconds=execution_time
            )

        bot = LinkedInBot(email=os.getenv("LINKEDIN_EMAIL"), password=os.getenv("LINKEDIN_PASSWORD"), headless=True)
        bot.login()
        scraped_posts = bot.scrape_user_posts(profile_url, n_posts)
        bot.close()

        posts_for_db = [
            {
                **post,
                "profile_url": profile_url.rstrip('/'),
                "source": "profile",
                "scraped_at": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat()
            }
            for post in scraped_posts
        ]

        saved_posts = await save_profile_posts_to_db(posts_for_db, db)
        save_posts_to_json(posts_for_db, profile_url)

        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return ProfilePostsResponse(
            success=True,
            message=f"Successfully scraped and saved {len(saved_posts)} posts",
            total_posts=len(saved_posts),
            posts=saved_posts,
            from_cache=False,
            execution_time_seconds=execution_time
        )
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return ProfilePostsResponse(success=False, message=str(e), total_posts=0, posts=[], from_cache=False, execution_time_seconds=execution_time)

@router.get("/hashtag/posts")
async def get_hashtag_posts(
    hashtag: str,
    n_posts: int = 5,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    start_time = datetime.utcnow()
    try:
        # 1️⃣ Check cache (MongoDB)
        cursor = db.hashtag_posts.find(
            {"hashtag": hashtag, "source": "hashtag"}
        ).sort("scraped_at", -1).limit(n_posts)
        existing_posts = await cursor.to_list(length=n_posts)

        posts_out = []
        for post in existing_posts:
            post.pop("_id", None)  # remove ObjectId
            if isinstance(post.get("scraped_at"), datetime):
                post["scraped_at"] = post["scraped_at"].isoformat()
            posts_out.append(PostInDB(**post))

        if posts_out and len(posts_out) >= n_posts:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return {
                "success": True,
                "message": f"Posts retrieved from DB cache for #{hashtag}",
                "total_posts": len(posts_out),
                "posts": posts_out,
                "from_cache": True,
                "execution_time_seconds": execution_time
            }

        # 2️⃣ If cache miss, scrape new posts
        bot = LinkedInBot(
            email=os.getenv("LINKEDIN_EMAIL"),
            password=os.getenv("LINKEDIN_PASSWORD"),
            headless=True
        )
        bot.login()
        scraped_posts = bot.scrape_hashtag_posts(hashtag, n_posts)
        bot.close()

        # Add metadata for DB & API
        posts_for_db = [
            {
                **post,
                "hashtag": hashtag,
                "source": "hashtag",
                "scraped_at": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat()
            }
            for post in scraped_posts
        ]

        # Save to DB
        saved_posts = []
        for post_data in posts_for_db:
            post_data["created_at"] = datetime.utcnow()
            post_data["updated_at"] = None
            await db.hashtag_posts.insert_one(post_data.copy())
            saved_posts.append(PostInDB(**post_data))

        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return {
            "success": True,
            "message": f"Scraped and saved {len(saved_posts)} posts for #{hashtag}",
            "total_posts": len(saved_posts),
            "posts": saved_posts,
            "from_cache": False,
            "execution_time_seconds": execution_time
        }

    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return {
            "success": False,
            "message": str(e),
            "total_posts": 0,
            "posts": [],
            "from_cache": False,
            "execution_time_seconds": execution_time
        }

@router.post("/debug/cleanup-duplicates")
async def cleanup_duplicate_posts_endpoint(profile_url: Optional[str] = None, db: AsyncIOMotorDatabase = Depends(get_database)):
    await cleanup_duplicate_posts(db, profile_url)
    return {"message": f"Cleanup completed for: {profile_url or 'all profiles'}"}

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "linkedin-scraper",
        "timestamp": datetime.utcnow().isoformat(),
        "data_directory": DATA_DIR
    }
