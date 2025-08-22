import sys
import os
from fastapi import FastAPI


from services.scraper.app.routes.scraping import router as scraping_router
from services.scraper.app.db.mongo_db import connect_to_mongo, close_mongo_connection



app = FastAPI(
    title="LinkedIn Scraper Service",
    description="Service for scraping LinkedIn posts from profiles and hashtags",
    version="1.0.0"
)

# Include scraping routes
app.include_router(scraping_router, prefix="/api/v1", tags=["scraping"])

@app.get("/")
def healthcheck():
    return {"msg": "Scraper service running in Docker"}

@app.on_event("startup")
async def startup_event():
    print("🚀 Scraper service is starting up...")
    try:
        await connect_to_mongo()
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    print("🔄 Scraper service is shutting down...")
    try:
        await close_mongo_connection()
        print("✅ MongoDB connection closed")
    except Exception as e:
        print(f"❌ Error during shutdown: {e}")
