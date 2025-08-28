from sqlalchemy import Column, Integer, String
from shared.db.pg_db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    linkedin_username = Column(String, unique=True, index=True, nullable=False)  # store only username
