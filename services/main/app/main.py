from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, postgen, metrics, scraper
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()  # Console output
    ]
)

# Set specific logger levels
logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce httpx noise
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # Reduce uvicorn noise

app = FastAPI(
    title="PostPilot Main API Gateway",
    version="0.1.0"
)

# CORS Configuration - Updated for proper preflight handling in dev environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(postgen.router, prefix="/api/v1/postgen", tags=["Post Generation"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Engagement Metrics"])
app.include_router(scraper.router, prefix="/api/v1/scraper", tags=["Scraper"])

@app.get("/health")
def healthcheck():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Welcome to PostPilot Main API Gateway"}