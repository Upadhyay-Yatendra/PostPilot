from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from dotenv import load_dotenv
from pathlib import Path

# Absolute path to your .env
# ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"  # app/db -> app -> scraper/.env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"  # db -> shared -> .env

load_dotenv(dotenv_path=ENV_PATH)

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_NAME")
POSTS_COLLECTION_NAME = os.getenv("POSTS_COLLECTION", "posts")
HASHTAG_POSTS_COLLECTION_NAME = os.getenv("HASHTAG_POSTS_COLLECTION", "hashtag_posts")
GENERATED_POSTS_COLLECTION_NAME = os.getenv("GENERATED_POSTS_COLLECTION", "generated_posts")
client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None

async def connect_to_mongo():
    global client, database
    print(f"Connecting to MongoDB: {MONGO_URI}, DB: {DB_NAME}")
    client = AsyncIOMotorClient(MONGO_URI)
    database = client[DB_NAME]


async def close_mongo_connection():
    """Close the database connection."""
    global client
    if client:
        client.close()
        client = None
        print("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database


