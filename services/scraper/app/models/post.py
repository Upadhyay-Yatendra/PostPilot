from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal

Source = Literal["profile", "hashtag"]

class PostInDB(BaseModel):
    text: str
    likes: int
    comments: int
    reposts: int
    engagement: int
    scraped_at: str
    source: Source
    profile_url: Optional[HttpUrl] = None
    hashtag: Optional[str] = None
