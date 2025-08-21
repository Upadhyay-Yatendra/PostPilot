from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from shared.db.pg_db import get_db
from services.postgen.app.models.user_post import UserPost
from services.postgen.app.utils.embeddings import get_embedding, most_similar_post
from services.postgen.app.utils.prompt import build_prompt
from services.postgen.app.llm import generate_post_langchain
import httpx

router = APIRouter()

@router.post("/generate")
async def generate_post(
    request: Request,
    db: Session = Depends(get_db)
):
    body = await request.json()
    user_id = body.get("user_id")
    prompt = body.get("prompt")
    topic = body.get("topic")
    tone = body.get("tone")
    length = body.get("length")
    audience = body.get("audience")
    hashtag = body.get("hashtag")
    num_variations = min(int(body.get("num_variations", 1)), 2)

    # 1. Get user's recent posts + embeddings
    user_posts = db.query(UserPost).filter(UserPost.user_id == user_id).all()

    # 2. Generate embedding for prompt and find most similar user post style
    prompt_embedding = get_embedding(prompt)
    style_sample = most_similar_post(user_posts, prompt_embedding)
    
    # 3. Get trending post sample from Scraper service
    trending_sample = None
    if hashtag:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"http://scraper-service:8002/top-hashtag", params={"hashtag": hashtag}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    trending_sample = data.get("top_post")
        except Exception:
            trending_sample = None

    # 4. Build full prompt with LangChain prompt template
    final_prompt = build_prompt(prompt, topic, tone, length, audience, style_sample, trending_sample)

    # 5. Generate post(s) using LangChain chain
    generated_posts = generate_post_langchain(final_prompt, num_variations=num_variations)

    return {"variations": generated_posts}
