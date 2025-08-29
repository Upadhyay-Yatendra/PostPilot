from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from shared.db.mongo_db import get_database, POSTS_COLLECTION_NAME
from app.utils.embeddings import get_embedding
from app.utils.prompt import build_prompt
from app.llm import generate_post_langchain
from app.config import SCRAPER_SERVICE_URL, GENERATED_POSTS_COLLECTION_NAME
from app.utils.pinecone import pinecone_service
from app.models.generated_post import GeneratedPostItem
from datetime import datetime
import httpx

router = APIRouter()

# Request body model
class GeneratePostRequest(BaseModel):
    prompt: str = Field(..., description="The main prompt for post generation")
    username: str = Field(..., description="LinkedIn username or full LinkedIn URL")
    topic: Optional[str] = Field(None, description="Topic for the post")
    tone: Optional[str] = Field(None, description="Tone of the post (e.g., professional, casual, motivational)")
    length: Optional[str] = Field(None, description="Desired length of the post (e.g., short, medium, long)")
    audience: Optional[str] = Field(None, description="Target audience")
    hashtag: Optional[str] = Field(None, description="Hashtag to get trending samples")
    num_variations: Optional[int] = Field(1, ge=1, le=3, description="Number of variations to generate (1-3)")

def extract_username_from_linkedin_url(url: str) -> str:
    """
    Extract username from LinkedIn URL
    Example: https://linkedin.com/in/john-doe -> john-doe
    """
    if '/in/' in url:
        return url.split('/in/')[-1].rstrip('/')
    # Handle other LinkedIn URL formats if needed
    return url

async def save_generated_posts(db, username: str, post_items: List[GeneratedPostItem]) -> str:
    """
    Save generated posts to MongoDB (adds to existing array or creates new document)
    """
    try:
        collection = db[GENERATED_POSTS_COLLECTION_NAME]
        
        existing_doc = await collection.find_one({"username": username})
        
        if existing_doc:
            await collection.update_one(
                {"username": username},
                {
                    "$push": {"generated_posts": {"$each": [item.dict() for item in post_items]}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            print(f"Added {len(post_items)} posts to existing user document: {username}")
            return str(existing_doc["_id"])
        else:
            new_doc = {
                "username": username,
                "user_id": None,
                "generated_posts": [item.dict() for item in post_items],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await collection.insert_one(new_doc)
            print(f"Created new document for user {username} with {len(post_items)} posts")
            return str(result.inserted_id)
            
    except Exception as e:
        print(f"Error saving generated posts: {e}")
        raise

@router.post("/generate")
async def generate_post(
    request_data: GeneratePostRequest,
    db = Depends(get_database)
):
    """Enhanced post generation with better user handling"""
    try:
        # Extract parameters
        prompt = request_data.prompt
        topic = request_data.topic
        tone = request_data.tone
        length = request_data.length
        audience = request_data.audience
        hashtag = request_data.hashtag
        num_variations = min(request_data.num_variations or 1, 3)
        username = request_data.username
        
        if 'linkedin.com' in username:
            username = extract_username_from_linkedin_url(username)
        
        print(f"Processing request for user: {username}")
        
        # 1. Ensure Pinecone has user posts (enhanced version)
        posts_available = await ensure_user_posts_in_pinecone(username, db)
        
        # 2. Find similar style post (only if posts are available)
        style_sample = None
        if posts_available:
            style_sample = pinecone_service.find_similar_post(username, prompt)
            print(f"Style sample found: {'Yes' if style_sample else 'No'}")
        else:
            print("No posts available - skipping style sample search")
        
        # 3. Get trending post sample (unchanged)
        trending_sample = None
        if hashtag:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{SCRAPER_SERVICE_URL}/scraper/scrape/hashtag/posts",
                        params={"hashtag": hashtag, "n_posts": 5}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        trending_sample = data.get("top_post")
                        print(f"Trending sample found: {trending_sample[:100]}..." if trending_sample else "No trending sample")
            except Exception as e:
                print(f"Error fetching trending sample: {e}")
                trending_sample = None

        # 4. Build prompt (works even without style sample)
        final_prompt = build_prompt(prompt, topic, tone, length, audience, style_sample, trending_sample)
        print("Final prompt built")    

        # 5. Generate posts (unchanged)
        generated_posts = generate_post_langchain(final_prompt, num_variations=num_variations)
        
        # ... rest of the function remains the same ...
        
        # Return response with additional user status info
        return {
            "success": True,
            "variations": generated_posts,
            # ... other fields ...
            "user_status": {
                "has_previous_posts": posts_available,
                "style_sample_found": style_sample is not None,
                "trending_sample_found": trending_sample is not None,
                "is_new_user": not posts_available
            }
        }
        
    except Exception as e:
        print(f"Error in generate_post: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
async def ensure_user_posts_in_pinecone(username: str, db):
    """
    Ensure user's posts are stored in Pinecone vector database
    Flow: Pinecone -> MongoDB -> Scrape -> MongoDB -> Embed to Pinecone
    """
    try:
        # 1. Check if user posts already exist in Pinecone
        query_response = pinecone_service.index.query(
            vector=[0.0] * 1536,
            filter={"username": username},
            top_k=1,
            include_metadata=True
        )
        
        if query_response.matches:
            print(f"User {username} posts found in Pinecone")
            return True
        
        print(f"User {username} posts not found in Pinecone, checking MongoDB...")
        
        # 2. Try to find posts in MongoDB
        user_posts_cursor = db[POSTS_COLLECTION_NAME].find({"username": username})
        user_document = await user_posts_cursor.to_list(length=1)
        
        if user_document:
            # User exists in MongoDB - embed their posts to Pinecone
            all_posts = user_document[0].get("posts", [])
            recent_posts = sorted(all_posts, key=lambda x: x.get("scraped_at", ""), reverse=True)[:10]
            
            if recent_posts:
                success = pinecone_service.store_user_posts(username, recent_posts)
                if success:
                    print(f"Embedded {len(recent_posts)} MongoDB posts to Pinecone for {username}")
                    return True
                else:
                    print(f"Failed to embed posts to Pinecone for {username}")
                    return False
            else:
                print(f"User {username} exists in MongoDB but has no posts")
                return False
        else:
            # 3. User doesn't exist in MongoDB - trigger scraping
            print(f"User {username} not found in MongoDB, triggering scraping...")
            
            # Call scraper service
            profile_url = f"https://linkedin.com/in/{username}"
            async with httpx.AsyncClient(timeout=90.0) as client:
                scrape_response = await client.get(
                    f"{SCRAPER_SERVICE_URL}/scraper/profile/posts",
                    params={"profile_url": profile_url, "n_posts": 10}
                )
                
                if scrape_response.status_code == 200:
                    scraped_data = scrape_response.json()
                    
                    if scraped_data.get("success", False):
                        print(f"Scraping successful for {username}, posts saved to MongoDB")
                        
                        # 4. Now fetch the scraped posts from MongoDB
                        user_posts_cursor = db[POSTS_COLLECTION_NAME].find({"username": username})
                        user_document = await user_posts_cursor.to_list(length=1)
                        
                        if user_document:
                            all_posts = user_document[0].get("posts", [])
                            recent_posts = sorted(all_posts, key=lambda x: x.get("scraped_at", ""), reverse=True)[:10]
                            
                            if recent_posts:
                                # 5. Embed the freshly scraped posts to Pinecone
                                success = pinecone_service.store_user_posts(username, recent_posts)
                                if success:
                                    print(f"Successfully scraped and embedded {len(recent_posts)} posts for {username}")
                                    return True
                                else:
                                    print(f"Scraped posts but failed to embed to Pinecone for {username}")
                                    return False
                            else:
                                print(f"Scraped posts but found none in MongoDB for {username}")
                                return False
                        else:
                            print(f"Scraping claimed success but no posts found in MongoDB for {username}")
                            return False
                    else:
                        print(f"Scraping failed for {username}: {scraped_data.get('message', 'Unknown error')}")
                        return False
                else:
                    print(f"Scraper service error for {username}: {scrape_response.status_code}")
                    return False
            
    except Exception as e:
        print(f"Error ensuring user posts in Pinecone: {e}")
        return False



async def handle_new_user(username: str, db) -> bool:
    """
    Handle completely new users not in MongoDB
    """
    print(f"New user {username} detected - attempting to scrape their posts")
    
    # Try to scrape the user's posts immediately
    scraping_success = await trigger_user_scraping(username, db)
    
    if scraping_success:
        print(f"Successfully scraped and stored posts for new user {username}")
        return True
    else:
        print(f"Failed to scrape posts for {username}, proceeding without style samples")
        # Still return True to continue post generation without style samples
        return True


async def trigger_user_scraping(username: str, db) -> bool:
    """
    Trigger immediate scraping for a user who doesn't have posts
    """
    try:
        # Construct LinkedIn profile URL from username
        profile_url = f"https://linkedin.com/in/{username}"
        
        # Call your scraper service to get this user's posts
        async with httpx.AsyncClient(timeout=60.0) as client:
            scrape_response = await client.get(
                f"{SCRAPER_SERVICE_URL}/scraper/profile/posts",
                params={"profile_url": profile_url, "n_posts": 10}
            )
            
            if scrape_response.status_code == 200:
                scraped_data = scrape_response.json()
                
                if scraped_data.get("success", False):
                    posts = scraped_data.get("posts", [])
                    
                    if posts:
                        # Convert response format to your expected format
                        formatted_posts = []
                        for post in posts:
                            formatted_posts.append({
                                "text": post.get("text", ""),
                                "content": post.get("text", ""),  # Add content field for compatibility
                                "likes": post.get("likes", 0),
                                "comments": post.get("comments", 0),
                                "reposts": post.get("reposts", 0),
                                "engagement": post.get("engagement", 0),
                                "scraped_at": post.get("scraped_at", datetime.utcnow().isoformat()),
                                "source": post.get("source", "profile"),
                                "post_id": f"{username}_{len(formatted_posts)}"  # Generate post ID
                            })
                        
                        # Posts are already stored in MongoDB by your scraper service
                        # Just need to store in Pinecone
                        success = pinecone_service.store_user_posts(username, formatted_posts)
                        if success:
                            print(f"Successfully scraped and stored {len(posts)} posts for {username}")
                            return True
                        else:
                            print(f"Scraped posts but failed to store in Pinecone for {username}")
                            return False
                    else:
                        print(f"Scraping returned no posts for {username}")
                        return False
                else:
                    print(f"Scraping failed for {username}: {scraped_data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"Scraping service error for {username}: {scrape_response.status_code}")
                return False
                
    except Exception as e:
        print(f"Error triggering scraping for {username}: {e}")
        return False

async def create_placeholder_user(username: str, db) -> bool:
    """
    Create a placeholder user document in MongoDB for tracking
    """
    try:
        collection = db[POSTS_COLLECTION_NAME]
        placeholder_doc = {
            "username": username,
            "posts": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "placeholder",
            "needs_scraping": True
        }
        await collection.insert_one(placeholder_doc)
        print(f"Created placeholder document for {username}")
        return True
    except Exception as e:
        print(f"Error creating placeholder for {username}: {e}")
        return False
    
    
@router.get("/history/{username}")
async def get_user_history(username: str, limit: int = 20, db = Depends(get_database)):
    """Get generation history for a user"""
    try:
        collection = db[GENERATED_POSTS_COLLECTION_NAME]
        user_doc = await collection.find_one({"username": username})
        
        if not user_doc:
            return {"success": True, "posts": [], "total_posts": 0}
        
        all_posts = user_doc.get("generated_posts", [])
        sorted_posts = sorted(all_posts, key=lambda x: x.get("created_at"), reverse=True)
        limited_posts = sorted_posts[:limit]
        
        return {
            "success": True,
            "posts": limited_posts,
            "total_posts": len(all_posts),
            "returned": len(limited_posts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
    
    
    


    
