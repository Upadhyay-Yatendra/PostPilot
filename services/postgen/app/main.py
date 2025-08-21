from fastapi import FastAPI
from services.postgen.app.routes.generate import router as generate_router
from shared.db.pg_db import engine, Base
from services.postgen.app.models.user_post import UserPost

app = FastAPI()
app.include_router(generate_router)

@app.get("/")
def healthcheck():
    return {"msg": "PostGen service running"}

# Create table on startup
Base.metadata.create_all(bind=engine)
