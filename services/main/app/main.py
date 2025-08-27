from fastapi import FastAPI
from app.routes import auth, postgen, metrics, scraper

app = FastAPI(
    title="PostPilot Main API Gateway",
    version="0.1.0"
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