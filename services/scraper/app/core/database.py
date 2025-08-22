from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    assert client is not None, "Mongo client not initialized"
    return client


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    try:
        # Quick ping to verify connection
        await client.admin.command("ping")
        yield
    finally:
        client.close()


# Expose helpers
def get_db():
    return get_client()[settings.MONGO_DB_NAME]


def get_posts_collection():
    return get_db()[settings.POSTS_COLLECTION]
