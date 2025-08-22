from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal, List
from datetime import datetime

Source = Literal["profile", "hashtag"]

class PostInDB(BaseModel):
    text: str
    likes: int
    comments: int
    reposts: int
    engagement: int
    scraped_at: str  # stored as ISO string
    source: Source
    profile_url: Optional[HttpUrl] = None
    hashtag: Optional[str] = None


class UserPosts(BaseModel):
    username: str
    profile_url: HttpUrl
    posts: List[PostInDB]


class HashtagPosts(BaseModel):
    hashtag: str
    posts: List[PostInDB]
