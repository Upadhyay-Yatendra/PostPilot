from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from shared.db.pg_db import get_db
from app.models.user_post import UserPost
from app.utils.embeddings import get_embedding, most_similar_post
from app.utils.prompt import build_prompt
from app.llm import generate_post_langchain
from app.config import SCRAPER_SERVICE_URL
import httpx

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
async def generate_post(
    req: GeneratePostRequest,
    db: Session = Depends(get_db)
):

   # Fetch posts for this linkedin username
    user_posts = db.query(UserPost).filter(UserPost.username == req.username).all()

    # 2. Generate embedding for prompt and find most similar user post style
    prompt_embedding = get_embedding(req.prompt)
    style_sample = most_similar_post(user_posts, prompt_embedding)
    
    # 3. Get trending post sample from Scraper service
    trending_sample = None
    if req.hashtag:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{SCRAPER_SERVICE_URL}/scrape/top-hashtag", params={"hashtag": hashtag}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    trending_sample = data.get("top_post")
        except Exception:
            trending_sample = None

    # 4. Build full prompt with LangChain prompt template
    # Build final prompt
    final_prompt = build_prompt(
        req.prompt,
        req.topic,
        req.tone,
        req.length,
        req.audience,
        style_sample,
        trending_sample,
    )

    # 5. Generate post(s) using LangChain chain
    # Generate with LLM
    generated_posts = generate_post_langchain(
        final_prompt, num_variations=min(req.num_variations, 2)
    )

    return {"variations": generated_posts}
