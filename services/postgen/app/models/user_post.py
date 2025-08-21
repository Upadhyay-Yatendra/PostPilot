from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from shared.db.pg_db import Base

class UserPost(Base):
    __tablename__ = "user_posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(String, nullable=True)  # Store delimited string or JSON array for MVP
