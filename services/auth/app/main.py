from fastapi import FastAPI
from app.routes.auth import router as auth_router
from shared.db.pg_db import engine, Base
from app.models.user import User

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
# refactored the url so as to maintain consistency with other services

@app.get("/")
def healthcheck():
    return {"msg": "Auth service running in Docker"}

# Create tables automatically at startup
Base.metadata.create_all(bind=engine)
@app.on_event("startup")
def startup_event():
    # This is where you can add any startup tasks, like initializing caches or connections
    print("Auth service is starting up...")
@app.on_event("shutdown")
def shutdown_event():
    # This is where you can add any cleanup tasks, like closing connections or saving state
    print("Auth service is shutting down...")
# This is a simple FastAPI application for the authentication service.
# It includes a health check endpoint and initializes the database tables at startup.
# The application uses SQLAlchemy for ORM and includes routes for user authentication.
# The `auth_router` handles user signup and login functionality.
# The application is designed to run in a Docker container, as indicated by the health check endpoint message.
# The `startup_event` and `shutdown_event` functions can be used for additional initialization and cleanup tasks.