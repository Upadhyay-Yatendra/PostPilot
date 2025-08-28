from fastapi import APIRouter, Depends, HTTPException, Request
from shared.db.mongo_db import get_database, POSTS_COLLECTION_NAME, HASHTAG_POSTS_COLLECTION_NAME
from app.utils.embeddings import get_embedding, most_similar_post
from app.utils.prompt import build_prompt
from app.llm import generate_post_langchain
from app.config import SCRAPER_SERVICE_URL
import httpx

router = APIRouter()

@router.post("/generate")
async def generate_post(
    db = Depends(get_database)  # <- this is AsyncIOMotorDatabase now
):
    # HARDCODED REQUEST BODY FOR TESTING - replace with actual request.json() later
    body = {
        "prompt": "Write a funny tweet about the growing use of agentic AI in medical science",
        "topic": "technology",
        "tone": "professional", 
        "length": "medium",
        "audience": "professionals",
        "hashtag": "AI",
        "num_variations": 1
    }
        
    # Hardcoded username based on your MongoDB data
    username = "kajal-jagga-663a26169"  # You can change this to any username from your DB
        
    prompt = body.get("prompt")
    topic = body.get("topic")
    tone = body.get("tone")
    length = body.get("length")
    audience = body.get("audience")
    hashtag = body.get("hashtag")
    num_variations = 2

    # 1. Get user's recent posts (MongoDB query using correct collection name)
    # ✅ Fixed: Using POSTS_COLLECTION_NAME and limiting to 10 most recent posts
    user_posts_cursor = db[POSTS_COLLECTION_NAME].find({"username": username})
    user_document = await user_posts_cursor.to_list(length=1)  # Get the user document
    
    user_posts = []
    if user_document:
        all_posts = user_document[0].get("posts", [])
        # ✅ Get last 10 posts (most recent)
        user_posts = sorted(all_posts, key=lambda x: x.get("scraped_at", ""), reverse=True)[:10]
        print(f"Using {len(user_posts)} most recent posts for style analysis")

    # 2. Generate embedding for prompt and find most similar user post style
    # ✅ On-the-fly embedding generation
    if user_posts:
        prompt_embedding = get_embedding(prompt)
        style_sample = most_similar_post(user_posts, prompt_embedding)
        print(f"Found style sample: {style_sample[:100]}..." if style_sample else "No style sample found")
    else:
        style_sample = None
        print("No user posts found for style analysis")

    # 3. Get trending post sample from hashtag_posts collection
    trending_sample = None
    if hashtag:
        try:
            # ✅ Query your own hashtag_posts collection instead of scraper service
            hashtag_doc = await db[HASHTAG_POSTS_COLLECTION_NAME].find_one({"hashtag": hashtag.lower()})
            if hashtag_doc and hashtag_doc.get("posts"):
                # Get the post with highest engagement
                trending_posts = hashtag_doc["posts"]
                trending_sample = max(trending_posts, key=lambda x: x.get("engagement", 0))["text"]
                print(f"Found trending sample: {trending_sample[:100]}..." if trending_sample else "No trending sample")
        except Exception as e:
            print(f"Error fetching trending sample: {e}")
            trending_sample = None

    # 4. Build full prompt
    final_prompt = build_prompt(prompt, topic, tone, length, audience, style_sample, trending_sample)
    print(f"Final prompt built: {final_prompt[:200]}...")

    # 5. Generate post(s)
    generated_posts = generate_post_langchain(final_prompt, num_variations=num_variations)

    return {
        "variations": generated_posts,
        "user_posts_count": len(user_posts),  # Added for debugging
        "username_used": username,  # Added for debugging
        "style_sample_found": style_sample is not None,
        "trending_sample_found": trending_sample is not None,
        "hardcoded_params": body  # Show what parameters were used
    }   
    # HARDCODED REQUEST BODY FOR TESTING - replace with actual request.json() later
    body = {
        "prompt": "Write a professional post about AI and technology trends",
        "topic": "technology",
        "tone": "professional", 
        "length": "medium",
        "audience": "professionals",
        "hashtag": "AI",
        "num_variations": 1
    }
        
    # Hardcoded username based on your MongoDB data
    username = "arshgoyal"  # You can change this to any username from your DB
        
    prompt = body.get("prompt")
    topic = body.get("topic")
    tone = body.get("tone")
    length = body.get("length")
    audience = body.get("audience")
    hashtag = body.get("hashtag")
    num_variations = min(int(body.get("num_variations", 1)), 2)

    # 1. Get user's recent posts (MongoDB query using correct collection name)
    # ✅ Fixed: Using "posts" collection and limiting to 10 most recent posts
    user_posts_cursor = db["posts"].find({"username": username})
    user_document = await user_posts_cursor.to_list(length=1)  # Get the user document
    print(f"Found user document: {user_document}")
    
    user_posts = []
    if user_document:
        all_posts = user_document[0].get("posts", [])
        # ✅ Get last 10 posts (most recent)
        user_posts = sorted(all_posts, key=lambda x: x.get("scraped_at", ""), reverse=True)[:10]
        print(f"Using {len(user_posts)} most recent posts for style analysis")

    # 2. Generate embedding for prompt and find most similar user post style
    # ✅ On-the-fly embedding generation
    if user_posts:
        prompt_embedding = get_embedding(prompt)
        style_sample = most_similar_post(user_posts, prompt_embedding)
        print(f"Found style sample: {style_sample[:100]}..." if style_sample else "No style sample found")
    else:
        style_sample = None
        print("No user posts found for style analysis")

    # 3. Get trending post sample from hashtag_posts collection
    trending_sample = None
    if hashtag:
        try:
            # ✅ Query your own hashtag_posts collection instead of scraper service
            hashtag_doc = await db["hashtag_posts"].find_one({"hashtag": hashtag.lower()})
            if hashtag_doc and hashtag_doc.get("posts"):
                # Get the post with highest engagement
                trending_posts = hashtag_doc["posts"]
                trending_sample = max(trending_posts, key=lambda x: x.get("engagement", 0))["text"]
                print(f"Found trending sample: {trending_sample[:100]}..." if trending_sample else "No trending sample")
        except Exception as e:
            print(f"Error fetching trending sample: {e}")
            trending_sample = None

    # 4. Build full prompt
    final_prompt = build_prompt(prompt, topic, tone, length, audience, style_sample, trending_sample)
    print(f"Final prompt built: {final_prompt[:200]}...")

    # 5. Generate post(s)
    generated_posts = generate_post_langchain(final_prompt, num_variations=num_variations)

    return {
        "variations": generated_posts,
        "user_posts_count": len(user_posts),  # Added for debugging
        "username_used": username,  # Added for debugging
        "style_sample_found": style_sample is not None,
        "trending_sample_found": trending_sample is not None,
        "hardcoded_params": body  # Show what parameters were used
    }