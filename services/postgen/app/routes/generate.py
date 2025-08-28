from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from shared.db.mongo_db import get_database, POSTS_COLLECTION_NAME, HASHTAG_POSTS_COLLECTION_NAME
from app.utils.embeddings import get_embedding, most_similar_post
from app.utils.prompt import build_prompt
from app.llm import generate_post_langchain

router = APIRouter()

class GeneratePostRequest(BaseModel):
    username: str
    prompt: str
    topic: str | None = None
    tone: str | None = None
    length: str | None = None
    audience: str | None = None
    hashtag: str | None = None
    num_variations: int = 1


@router.post("/generate")
async def generate_post(req: GeneratePostRequest, db=Depends(get_database)):
    # 1. Get user's recent posts (from MongoDB posts collection)
    user_posts_cursor = db[POSTS_COLLECTION_NAME].find({"username": req.username})
    user_document = await user_posts_cursor.to_list(length=1)

    user_posts = []
    if user_document:
        all_posts = user_document[0].get("posts", [])
        user_posts = sorted(all_posts, key=lambda x: x.get("scraped_at", ""), reverse=True)[:10]
        print(f"Using {len(user_posts)} most recent posts for style analysis")
    else:
        print(f"No posts found for username {req.username}")

    # 2. Find most similar user post style
    style_sample = None
    if user_posts:
        prompt_embedding = get_embedding(req.prompt)
        style_sample = most_similar_post(user_posts, prompt_embedding)

    # 3. Get trending post sample from hashtag_posts collection
    trending_sample = None
    if req.hashtag:
        try:
            hashtag_doc = await db[HASHTAG_POSTS_COLLECTION_NAME].find_one({"hashtag": req.hashtag.lower()})
            if hashtag_doc and hashtag_doc.get("posts"):
                trending_posts = hashtag_doc["posts"]
                trending_sample = max(trending_posts, key=lambda x: x.get("engagement", 0))["text"]
        except Exception as e:
            print(f"Error fetching trending sample: {e}")

    # 4. Build final prompt
    final_prompt = build_prompt(
        req.prompt,
        req.topic,
        req.tone,
        req.length,
        req.audience,
        style_sample,
        trending_sample,
    )

    # 5. Generate post(s)
    generated_posts = generate_post_langchain(final_prompt, num_variations=min(req.num_variations, 2))

    return {
        "variations": generated_posts,
        "user_posts_count": len(user_posts),
        "username_used": req.username,
        "style_sample_found": style_sample is not None,
        "trending_sample_found": trending_sample is not None,
    }
