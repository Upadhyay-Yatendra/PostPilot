from fastapi import FastAPI
from app.routes.generate import router as generate_router
from shared.db.pg_db import engine, Base
from app.models.user_post import UserPost

app = FastAPI()
app.include_router(generate_router, prefix="/postgen", tags=["Post Generation"])


@app.get("/")
def healthcheck():
    return {"msg": "PostGen service running"}

# Create table on startup
Base.metadata.create_all(bind=engine)
