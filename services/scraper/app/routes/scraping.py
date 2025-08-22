# routes/scraping.py - Corrected version for array-based storage

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal
from datetime import datetime, timedelta, timezone
import os
import json
from pathlib import Path
from services.scraper.app.db.mongo_db import get_database
from services.scraper.app.models.post import PostInDB, UserPosts, HashtagPosts
from services.scraper.app.utils.linkedin_bot import LinkedInBot
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# Directories for saving posts
BASE_DATA_DIR = Path(__file__).parent.parent / "test" / "data"
DATA_DIR = BASE_DATA_DIR / "profile_posts"
HASHTAG_DATA_DIR = BASE_DATA_DIR / "hashtag_posts"

# Create directories if they don't exist
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
    """Extract username from LinkedIn profile URL"""
    clean_url = profile_url.rstrip('/')
    if '/in/' in clean_url:
        return clean_url.split('/in/')[-1].split('/')[0]
    elif '/company/' in clean_url:
        return clean_url.split('/company/')[-1].split('/')[0]
    else:
        return clean_url.split('/')[-1]

def convert_post_to_response_format(post_dict: dict) -> PostData:
    """Convert post dictionary to PostData for API response"""
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

# Removed freshness check function since not needed

async def save_profile_posts_to_db(posts_data: List[dict], profile_url: str, db: AsyncIOMotorDatabase) -> List[dict]:
    """Save profile posts to database with proper array structure"""
    username = extract_profile_identifier(profile_url)
    current_time = datetime.utcnow().isoformat()
    
    # Format posts for database storage
    formatted_posts = []
    for post in posts_data:
        formatted_post = {
            "text": post.get("text", ""),
            "likes": post.get("likes", 0),
            "comments": post.get("comments", 0),
            "reposts": post.get("reposts", 0),
            "engagement": post.get("engagement", 0),
            "scraped_at": post.get("scraped_at", current_time),
            "source": "profile",
            "profile_url": profile_url.rstrip("/"),
            "hashtag": None
        }
        formatted_posts.append(formatted_post)
    
    try:
        # Check if user document exists
        existing_doc = await db.posts.find_one({"username": username})
        
        if existing_doc:
            # Update existing document - append new posts to the posts array
            await db.posts.update_one(
                {"username": username},
                {
                    "$push": {"posts": {"$each": formatted_posts}},
                    "$set": {
                        "profile_url": profile_url.rstrip("/"),
                        "updated_at": current_time
                    }
                }
            )
            print(f"✅ Updated existing document for user: {username} with {len(formatted_posts)} new posts")
        else:
            # Create new document with posts array
            new_doc = {
                "username": username,
                "profile_url": profile_url.rstrip("/"),
                "posts": formatted_posts,
                "created_at": current_time,
                "updated_at": current_time
            }
            await db.posts.insert_one(new_doc)
            print(f"✅ Created new document for user: {username} with {len(formatted_posts)} posts")
        
        return formatted_posts
        
    except Exception as e:
        print(f"❌ Failed to save profile posts for {username}: {e}")
        return []

async def save_hashtag_posts_to_db(posts_data: List[dict], hashtag: str, db: AsyncIOMotorDatabase) -> List[dict]:
    """Save hashtag posts to database with proper array structure"""
    current_time = datetime.utcnow().isoformat()
    
    # Format posts for database storage
    formatted_posts = []
    for post in posts_data:
        formatted_post = {
            "text": post.get("text", ""),
            "likes": post.get("likes", 0),
            "comments": post.get("comments", 0),
            "reposts": post.get("reposts", 0),
            "engagement": post.get("engagement", 0),
            "scraped_at": post.get("scraped_at", current_time),
            "source": "hashtag",
            "profile_url": None,
            "hashtag": hashtag
        }
        formatted_posts.append(formatted_post)
    
    try:
        # Check if hashtag document exists
        existing_doc = await db.hashtag_posts.find_one({"hashtag": hashtag})
        
        if existing_doc:
            # Update existing document - append new posts to the posts array
            await db.hashtag_posts.update_one(
                {"hashtag": hashtag},
                {
                    "$push": {"posts": {"$each": formatted_posts}},
                    "$set": {"updated_at": current_time}
                }
            )
            print(f"✅ Updated existing hashtag document for: #{hashtag} with {len(formatted_posts)} new posts")
        else:
            # Create new document with posts array
            new_doc = {
                "hashtag": hashtag,
                "posts": formatted_posts,
                "created_at": current_time,
                "updated_at": current_time
            }
            await db.hashtag_posts.insert_one(new_doc)
            print(f"✅ Created new hashtag document for: #{hashtag} with {len(formatted_posts)} posts")
        
        return formatted_posts
        
    except Exception as e:
        print(f"❌ Failed to save hashtag posts for #{hashtag}: {e}")
        return []

async def cleanup_duplicate_posts(db: AsyncIOMotorDatabase, username: Optional[str] = None):
    """Clean up duplicate posts based on text content"""
    try:
        if username:
            # Clean duplicates for specific user
            user_doc = await db.posts.find_one({"username": username})
            
            if user_doc and "posts" in user_doc:
                posts = user_doc["posts"]
                unique_posts = []
                seen_texts = set()
                
                # Keep posts with unique text content (case-insensitive)
                for post in posts:
                    post_text = post.get("text", "").lower().strip()
                    if post_text and post_text not in seen_texts:
                        unique_posts.append(post)
                        seen_texts.add(post_text)
                
                if len(unique_posts) < len(posts):
                    await db.posts.update_one(
                        {"username": username},
                        {"$set": {"posts": unique_posts}}
                    )
                    print(f"✅ Removed {len(posts) - len(unique_posts)} duplicate posts for {username}")
        else:
            print("⚠️ Username required for cleanup")
            
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

def save_posts_to_json(posts_data: List[dict], identifier: str, is_hashtag: bool = False) -> str:
    """Save posts to JSON file"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{'hashtag' if is_hashtag else 'profile'}_{identifier}_{timestamp}.json"
    filepath = (HASHTAG_DATA_DIR if is_hashtag else DATA_DIR) / filename

    # Convert any datetime objects to strings for JSON serialization
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

    print(f"💾 Saved posts to JSON file: {filepath}")
    return str(filepath)

# ======== Routes ========

@router.get("/scrape/profile/posts", response_model=ProfilePostsResponse)
async def get_user_profile_posts(
    profile_url: str,
    n_posts: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user profile posts - from cache if exists, otherwise scrape new ones"""
    start_time = datetime.utcnow()
    
    try:
        username = extract_profile_identifier(profile_url)
        print(f"🔍 Looking for posts for username: {username}")
        
        # Fetch user document from database
        user_doc = await db.posts.find_one({"username": username})
        
        if user_doc and "posts" in user_doc and len(user_doc["posts"]) > 0:
            posts = user_doc["posts"]
            print(f"📋 Found existing document with {len(posts)} posts")
            
            # Check if we have enough posts
            if len(posts) >= n_posts:
                # Sort by scraped_at DESC and limit to n_posts
                posts_sorted = sorted(
                    posts,
                    key=lambda x: x.get("scraped_at", ""),
                    reverse=True
                )[:n_posts]
                
                # Convert to response format
                response_posts = [convert_post_to_response_format(post) for post in posts_sorted]
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                return ProfilePostsResponse(
                    success=True,
                    message=f"Retrieved {len(response_posts)} posts from database cache",
                    total_posts=len(response_posts),
                    posts=response_posts,
                    from_cache=True,
                    execution_time_seconds=execution_time
                )
            else:
                print(f"📊 Need {n_posts} posts but only have {len(posts)}. Will scrape new posts.")
        else:
            print(f"📭 No existing posts found for username: {username}")
        
        # Scrape new posts if cache miss or insufficient posts
        print(f"🔄 Scraping new posts for profile: {profile_url}")
        
        bot = LinkedInBot(
            email=os.getenv("LINKEDIN_EMAIL"),
            password=os.getenv("LINKEDIN_PASSWORD"),
            headless=True
        )
        
        bot.login()
        scraped_posts = bot.scrape_user_posts(profile_url, n_posts)
        bot.close()
        
        # Save to database
        saved_posts = await save_profile_posts_to_db(scraped_posts, profile_url, db)
        
        # Save to JSON file
        save_posts_to_json(scraped_posts, username)
        
        # Clean up duplicates
        await cleanup_duplicate_posts(db, username)
        
        # Convert to response format
        response_posts = [convert_post_to_response_format(post) for post in saved_posts]
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return ProfilePostsResponse(
            success=True,
            message=f"Successfully scraped and saved {len(saved_posts)} new posts",
            total_posts=len(response_posts),
            posts=response_posts,
            from_cache=False,
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        print(f"❌ Error in get_user_profile_posts: {e}")
        return ProfilePostsResponse(
            success=False,
            message=str(e),
            total_posts=0,
            posts=[],
            from_cache=False,
            execution_time_seconds=execution_time
        )

@router.get("/scrape/hashtag/posts", response_model=HashtagPostsResponse)
async def get_hashtag_posts(
    hashtag: str,
    n_posts: int = 5,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get hashtag posts - from cache if exists, otherwise scrape new ones"""
    start_time = datetime.utcnow()
    
    try:
        # Clean hashtag input (remove # if present)
        clean_hashtag = hashtag.lstrip('#')
        print(f"🔍 Looking for posts for hashtag: #{clean_hashtag}")
        
        # Fetch hashtag document from database
        hashtag_doc = await db.hashtag_posts.find_one({"hashtag": clean_hashtag})
        
        if hashtag_doc and "posts" in hashtag_doc and len(hashtag_doc["posts"]) > 0:
            posts = hashtag_doc["posts"]
            print(f"📋 Found existing hashtag document with {len(posts)} posts")
            
            # Check if we have enough posts
            if len(posts) >= n_posts:
                # Sort by scraped_at DESC and limit to n_posts
                posts_sorted = sorted(
                    posts,
                    key=lambda x: x.get("scraped_at", ""),
                    reverse=True
                )[:n_posts]
                
                # Convert to response format
                response_posts = [convert_post_to_response_format(post) for post in posts_sorted]
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                return HashtagPostsResponse(
                    success=True,
                    message=f"Retrieved {len(response_posts)} posts from database cache for #{clean_hashtag}",
                    total_posts=len(response_posts),
                    posts=response_posts,
                    from_cache=True,
                    execution_time_seconds=execution_time
                )
            else:
                print(f"📊 Need {n_posts} posts but only have {len(posts)} for #{clean_hashtag}. Will scrape new posts.")
        else:
            print(f"📭 No existing posts found for hashtag: #{clean_hashtag}")
        
        # Scrape new posts if cache miss or insufficient posts
        print(f"🔄 Scraping new posts for hashtag: #{clean_hashtag}")
        
        bot = LinkedInBot(
            email=os.getenv("LINKEDIN_EMAIL"),
            password=os.getenv("LINKEDIN_PASSWORD"),
            headless=True
        )
        
        bot.login()
        scraped_posts = bot.scrape_hashtag_posts(clean_hashtag, n_posts)
        bot.close()
        
        # Save to database
        saved_posts = await save_hashtag_posts_to_db(scraped_posts, clean_hashtag, db)
        
        # Save to JSON file
        save_posts_to_json(scraped_posts, clean_hashtag, is_hashtag=True)
        
        # Convert to response format
        response_posts = [convert_post_to_response_format(post) for post in saved_posts]
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return HashtagPostsResponse(
            success=True,
            message=f"Successfully scraped and saved {len(saved_posts)} new posts for #{clean_hashtag}",
            total_posts=len(response_posts),
            posts=response_posts,
            from_cache=False,
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        print(f"❌ Error in get_hashtag_posts: {e}")
        return HashtagPostsResponse(
            success=False,
            message=str(e),
            total_posts=0,
            posts=[],
            from_cache=False,
            execution_time_seconds=execution_time
        )

# ======== Utility Routes ========

@router.post("/debug/cleanup-duplicates")
async def cleanup_duplicate_posts_endpoint(
    username: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Clean up duplicate posts for a specific user or all users"""
    if username:
        await cleanup_duplicate_posts(db, username)
        return {"message": f"Cleanup completed for username: {username}"}
    else:
        return {"error": "Username parameter is required"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "linkedin-scraper",
        "timestamp": datetime.utcnow().isoformat(),
        "data_directory": str(DATA_DIR),
        "storage_structure": "array-based (username -> posts[])"
    }