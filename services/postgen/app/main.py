from fastapi import FastAPI
from app.routes.generate import router as generate_router
from shared.db.mongo_db import connect_to_mongo, close_mongo_connection
from app.models.user_post import UserPost

app = FastAPI()
app.include_router(generate_router, prefix="/postgen", tags=["Post Generation"])



@app.get("/")
def healthcheck():
    return {"msg": "PostGen service running"}


# 🔹 Initialize DB connection when app starts
@app.on_event("startup")
async def startup_db():
    await connect_to_mongo()


# 🔹 Close DB connection when app shuts down
@app.on_event("shutdown")
async def shutdown_db():
    await close_mongo_connection()
