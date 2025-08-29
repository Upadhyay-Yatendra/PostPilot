from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
import uuid

class GeneratedPostItem(BaseModel):
    """Individual generated post item that goes into the posts array"""
    post_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique ID for each post
    original_prompt: str
    generated_text: str
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Store topic, tone, length, etc.
    style_sample_used: Optional[str] = None
    trending_sample_used: Optional[str] = None
    similarity_score: Optional[float] = None  # Similarity score with style sample
    variation_number: int = 1  # Which variation this is (1, 2, 3, etc.)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GeneratedPostsDocument(BaseModel):
    """Document structure that matches your existing posts collection pattern"""
    id: Optional[str] = None
    username: str  # LinkedIn username from URL
    user_id: Optional[int] = None  # From auth service if available
    generated_posts: List[GeneratedPostItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        # Allow ObjectId to be used
        arbitrary_types_allowed = True
    
    @classmethod
    def from_mongo(cls, data: dict):
        """Convert MongoDB document to Pydantic model"""
        if data and "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return cls(**data)
    
    def to_mongo(self) -> dict:
        """Convert Pydantic model to MongoDB document"""
        data = self.dict(exclude={"id"})
        # Ensure updated_at is current
        data["updated_at"] = datetime.utcnow()
        return data
    
    def add_generated_post(self, post_item: GeneratedPostItem):
        """Add a new generated post to the array"""
        self.generated_posts.append(post_item)
        self.updated_at = datetime.utcnow()
    
    def get_recent_posts(self, limit: int = 10) -> List[GeneratedPostItem]:
        """Get most recent posts"""
        return sorted(self.generated_posts, key=lambda x: x.created_at, reverse=True)[:limit]