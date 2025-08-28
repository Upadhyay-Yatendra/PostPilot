from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class UserPost(BaseModel):
    id: Optional[str] = None
    user_id: int  # Keep as int to match your auth service
    text: str
    embedding: Optional[List[float]] = None  # Store as array instead of delimited string
    created_at: datetime = datetime.utcnow()
    @classmethod
    def from_mongo(cls, data: dict):
        """Convert MongoDB document to Pydantic model"""
        if data and "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return cls(**data)