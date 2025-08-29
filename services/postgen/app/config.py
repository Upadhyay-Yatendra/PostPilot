import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env.docker"
if env_path.exists():
    load_dotenv(env_path)

SCRAPER_SERVICE_URL = os.getenv(
    "SCRAPER_SERVICE_URL",
    "http://scraper-service:8000"  # default for docker-compose network
)

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")  # Default environment
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "user-posts")

# MongoDB Collections
GENERATED_POSTS_COLLECTION_NAME = "generated_posts"