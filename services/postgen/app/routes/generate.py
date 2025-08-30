from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from shared.db.mongo_db import get_database, POSTS_COLLECTION_NAME
from app.utils.embeddings import get_embedding
from app.utils.prompt import build_prompt
from app.llm import generate_post_langchain
from app.config import  GENERATED_POSTS_COLLECTION_NAME
from app.utils.pinecone import pinecone_service
from app.models.generated_post import GeneratedPostItem
from datetime import datetime
import httpx

router = APIRouter()

# Request body model
class GeneratePostRequest(BaseModel):
    prompt: str = Field(..., description="The main prompt for post generation")
    topic: Optional[str] = Field(None, description="Topic for the post")
    tone: Optional[str] = Field(None, description="Tone of the post (e.g., professional, casual, motivational)")
    length: Optional[str] = Field(None, description="Desired length of the post (e.g., short, medium, long)")
    audience: Optional[str] = Field(None, description="Target audience")
    hashtag: Optional[str] = Field(None, description="Hashtag to get trending samples")
    num_variations: Optional[int] = Field(1, ge=1, le=3, description="Number of variations to generate (1-3)")

async def ensure_user_posts_in_pinecone(username: str, db):
    """
    Ensure user's posts are stored in Pinecone vector database
    Flow: Check Pinecone -> If not found, get from MongoDB -> Embed to Pinecone
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
        
        # 2. Get posts from MongoDB (assuming they're already stored by another service)
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
            print(f"User {username} not found in MongoDB - posts should be pre-stored by another service")
            return False
            
    except Exception as e:
        print(f"Error ensuring user posts in Pinecone: {e}")
        return False

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
async def generate_post(req: GeneratePostRequest, db = Depends(get_database)):
    """Enhanced post generation with better user handling"""
    try:
        # Extract parameters
        prompt = req.prompt
        topic = req.topic
        tone = req.tone
        length = req.length
        audience = req.audience
        hashtag = req.hashtag
        num_variations = min(req.num_variations or 1, 3)
        username = req.username  # Get username from JWT via main service middleware
        
        # Extract username from LinkedIn URL if needed
        if 'linkedin.com' in username:
            if '/in/' in username:
                username = username.split('/in/')[-1].rstrip('/')
        
        print(f"Processing request for user: {username}")
        
        # 1. Ensure user posts are in Pinecone (check Pinecone -> MongoDB -> Embed if needed)
        posts_available = await ensure_user_posts_in_pinecone(username, db)
        
        # 2. Find similar style post (only if posts are available)
        style_sample = None
        if posts_available:
            style_sample = pinecone_service.find_similar_post(username, prompt)
            print(f"Style sample found: {'Yes' if style_sample else 'No'}")
        else:
            print("No posts available - skipping style sample search")
        
        # 3. Get trending post sample
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

        # 4. Build prompt
        final_prompt = build_prompt(prompt, topic, tone, length, audience, style_sample, trending_sample)
        print("Final prompt built")    

        # 5. Generate posts
        generated_posts = generate_post_langchain(final_prompt, num_variations=num_variations)
        
        # 6. Prepare post items for saving
        post_items = []
        for i, post_text in enumerate(generated_posts):
            post_item = GeneratedPostItem(
                text=post_text,
                prompt=prompt,
                topic=topic,
                tone=tone,
                length=length,
                audience=audience,
                hashtag=hashtag,
                variation_number=i + 1,
                created_at=datetime.utcnow()
            )
            post_items.append(post_item)
        
        # 7. Save to MongoDB
        doc_id = await save_generated_posts(db, username, post_items)
        
        # Return response
        return {
            "success": True,
            "variations": generated_posts,
            "username_used": username,
            "style_sample_found": style_sample is not None,
            "trending_sample_found": trending_sample is not None,
            "saved_to_db": True,
            "document_id": doc_id
        }
        
    except Exception as e:
        print(f"Error in generate_post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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