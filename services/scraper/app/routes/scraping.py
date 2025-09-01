# routes/scraping.py - Corrected version for array-based storage

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal
from datetime import datetime, timedelta, timezone
import os
import json
from pathlib import Path
from shared.db.mongo_db import get_database
from app.models.post import PostInDB, UserPosts, HashtagPosts
from app.utils.linkedin_bot import LinkedInBot



router = APIRouter()

# Directories for saving posts
BASE_DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR = BASE_DATA_DIR / "profile_posts"
HASHTAG_DATA_DIR = BASE_DATA_DIR / "hashtag_posts"

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

class HashtagPostsResponse(BaseModel):
    success: bool
    message: str
    total_posts: int
    posts: List[PostData]
    from_cache: bool
    execution_time_seconds: float

# ======== Helper Functions ========

def extract_profile_identifier(profile_url: str) -> str:
    clean_url = profile_url.rstrip('/')
    if '/in/' in clean_url:
        return clean_url.split('/in/')[-1].split('/')[0]
    elif '/company/' in clean_url:
        return clean_url.split('/company/')[-1].split('/')[0]
    else:
        return clean_url.split('/')[-1]

def convert_post_to_response_format(post_dict: dict) -> PostData:
    return PostData(
        text=post_dict.get("text", ""),
        likes=post_dict.get("likes", 0),
        comments=post_dict.get("comments", 0),
        reposts=post_dict.get("reposts", 0),
        engagement=post_dict.get("engagement", 0),
        scraped_at=post_dict.get("scraped_at", ""),
        source=post_dict.get("source", "profile"),
        profile_url=post_dict.get("profile_url"),
        hashtag=post_dict.get("hashtag")
    )

async def save_profile_posts_to_db(posts_data: List[dict], profile_url: str, db: AsyncIOMotorDatabase) -> List[dict]:
    username = extract_profile_identifier(profile_url)
    current_time = datetime.utcnow().isoformat()
    formatted_posts = []
    for post in posts_data:
        formatted_posts.append({
            "text": post.get("text", ""),
            "likes": post.get("likes", 0),
            "comments": post.get("comments", 0),
            "reposts": post.get("reposts", 0),
            "engagement": post.get("engagement", 0),
            "scraped_at": post.get("scraped_at", current_time),
            "source": "profile",
            "hashtag": None
        })
    try:
        existing_doc = await db.posts.find_one({"username": username})
        if existing_doc:
            await db.posts.update_one(
                {"username": username},
                {"$push": {"posts": {"$each": formatted_posts}},
                 "$set": {"profile_url": profile_url.rstrip("/"), "updated_at": current_time}}
            )
        else:
            new_doc = {
                "username": username,
                "profile_url": profile_url.rstrip("/"),
                "posts": formatted_posts,
                "created_at": current_time,
                "updated_at": current_time
            }
            await db.posts.insert_one(new_doc)
        return formatted_posts
    except Exception as e:
        print(f"❌ Save error: {e}")
        return []

async def save_hashtag_posts_to_db(posts_data: List[dict], hashtag: str, db: AsyncIOMotorDatabase) -> List[dict]:
    current_time = datetime.utcnow().isoformat()
    formatted_posts = []
    for post in posts_data:
        formatted_posts.append({
            "text": post.get("text", ""),
            "likes": post.get("likes", 0),
            "comments": post.get("comments", 0),
            "reposts": post.get("reposts", 0),
            "engagement": post.get("engagement", 0),
            "scraped_at": post.get("scraped_at", current_time),
            "source": "hashtag",
            "profile_url": None,
            "hashtag": hashtag
        })
    try:
        existing_doc = await db.hashtag_posts.find_one({"hashtag": hashtag})
        if existing_doc:
            await db.hashtag_posts.update_one(
                {"hashtag": hashtag},
                {"$push": {"posts": {"$each": formatted_posts}}, "$set": {"updated_at": current_time}}
            )
        else:
            new_doc = {
                "hashtag": hashtag,
                "posts": formatted_posts,
                "created_at": current_time,
                "updated_at": current_time
            }
            await db.hashtag_posts.insert_one(new_doc)
        return formatted_posts
    except Exception as e:
        print(f"❌ Save error: {e}")
        return []

async def cleanup_duplicate_posts(db: AsyncIOMotorDatabase, username: Optional[str] = None):
    try:
        if username:
            user_doc = await db.posts.find_one({"username": username})
            if user_doc and "posts" in user_doc:
                posts = user_doc["posts"]
                unique_posts, seen_texts = [], set()
                for post in posts:
                    text = post.get("text", "").lower().strip()
                    if text and text not in seen_texts:
                        unique_posts.append(post)
                        seen_texts.add(text)
                if len(unique_posts) < len(posts):
                    await db.posts.update_one({"username": username}, {"$set": {"posts": unique_posts}})
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

def save_posts_to_json(posts_data: List[dict], identifier: str, is_hashtag: bool = False) -> str:
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{'hashtag' if is_hashtag else 'profile'}_{identifier}_{timestamp}.json"
    filepath = (HASHTAG_DATA_DIR if is_hashtag else DATA_DIR) / filename
    for post in posts_data:
        for key in ["scraped_at", "created_at"]:
            if key in post and isinstance(post[key], datetime):
                post[key] = post[key].isoformat()
    json_data = {
        "identifier": identifier,
        "type": "hashtag" if is_hashtag else "profile",
        "scraped_at": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "total_posts": len(posts_data),
        "posts": posts_data
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    return str(filepath)

# ======== Routes ========

@router.get("/profile/posts", response_model=ProfilePostsResponse)
async def get_user_profile_posts(
    profile_url: str,
    n_posts: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    start_time = datetime.utcnow()
    try:
        username = extract_profile_identifier(profile_url)
        user_doc = await db.posts.find_one({"username": username})
        if user_doc and "posts" in user_doc and len(user_doc["posts"]) >= n_posts:
            posts_sorted = sorted(user_doc["posts"], key=lambda x: x.get("scraped_at", ""), reverse=True)[:n_posts]
            response_posts = [convert_post_to_response_format(post) for post in posts_sorted]
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ProfilePostsResponse(
                success=True, message="Retrieved posts from database cache",
                total_posts=len(response_posts), posts=response_posts,
                from_cache=True, execution_time_seconds=execution_time
            )
        bot = LinkedInBot(email=os.getenv("LINKEDIN_EMAIL"), password=os.getenv("LINKEDIN_PASSWORD"), headless=True)
        await bot.start()
        await bot.login()
        scraped_posts = await bot.scrape_user_posts(profile_url, n_posts)
        await bot.close()
        saved_posts = await save_profile_posts_to_db(scraped_posts, profile_url, db)
        save_posts_to_json(scraped_posts, username)
        await cleanup_duplicate_posts(db, username)
        response_posts = [convert_post_to_response_format(post) for post in saved_posts]
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return ProfilePostsResponse(
            success=True, message="Successfully scraped posts",
            total_posts=len(response_posts), posts=response_posts,
            from_cache=False, execution_time_seconds=execution_time
        )
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return ProfilePostsResponse(success=False, message=str(e), total_posts=0, posts=[], from_cache=False, execution_time_seconds=execution_time)

@router.get("/hashtag/posts", response_model=HashtagPostsResponse)
async def get_hashtag_posts(
    hashtag: str,
    n_posts: int = 5,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    start_time = datetime.utcnow()
    try:
        clean_hashtag = hashtag.lstrip('#')
        hashtag_doc = await db.hashtag_posts.find_one({"hashtag": clean_hashtag})
        
        if hashtag_doc and "posts" in hashtag_doc and len(hashtag_doc["posts"]) >= 2:
            # Get top 2 posts from cache (already filtered during storage)
            cached_posts = hashtag_doc["posts"]
            
            # Sort by engagement (highest first) - defensive programming in case order changed
            posts_sorted_by_engagement = sorted(
                cached_posts, 
                key=lambda x: x.get("engagement", 0), 
                reverse=True
            )[:2]  # Ensure we only get top 2
            
            response_posts = [convert_post_to_response_format(post) for post in posts_sorted_by_engagement]
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return HashtagPostsResponse(
                success=True, 
                message=f"Retrieved top 2 posts by engagement from database cache for #{clean_hashtag}",
                total_posts=len(response_posts), 
                posts=response_posts,
                from_cache=True, 
                execution_time_seconds=execution_time
            )
        
        # If not enough posts in cache, scrape new ones
        bot = LinkedInBot(email=os.getenv("LINKEDIN_EMAIL"), password=os.getenv("LINKEDIN_PASSWORD"), headless=True)
        await bot.start()
        await bot.login()
        
        # Scrape n_posts to get a good sample for trend analysis
        scraped_posts = await bot.scrape_hashtag_posts(clean_hashtag, n_posts)
        await bot.close()
        
        print(f"📊 Scraped {len(scraped_posts)} posts for trend analysis")
        print(f"📈 Engagement values: {[post.get('engagement', 0) for post in scraped_posts]}")
        
        # Sort by engagement and get ONLY top 2 for storage
        posts_sorted_by_engagement = sorted(
            scraped_posts, 
            key=lambda x: x.get("engagement", 0), 
            reverse=True
        )
        
        # Take only top 2 posts for database storage
        top_2_posts = posts_sorted_by_engagement[:2]
        
        print(f"💾 Storing only top 2 posts with engagement: {[post.get('engagement', 0) for post in top_2_posts]}")
        
        # Save ONLY the top 2 posts to database
        saved_posts = await save_hashtag_posts_to_db(top_2_posts, clean_hashtag, db)
        
        # Save all scraped posts to JSON file for trend analysis (optional)
        save_posts_to_json(scraped_posts, clean_hashtag, is_hashtag=True)
        
        response_posts = [convert_post_to_response_format(post) for post in saved_posts]
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return HashtagPostsResponse(
            success=True, 
            message=f"Scraped {len(scraped_posts)} posts, stored top 2 by engagement for #{clean_hashtag}",
            total_posts=len(response_posts), 
            posts=response_posts,
            from_cache=False, 
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return HashtagPostsResponse(
            success=False, 
            message=str(e), 
            total_posts=0, 
            posts=[], 
            from_cache=False, 
            execution_time_seconds=execution_time
        )
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "linkedin-scraper",
        "timestamp": datetime.utcnow().isoformat(),
        "data_directory": str(DATA_DIR)
    }