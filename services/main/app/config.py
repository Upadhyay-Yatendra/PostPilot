import os
from pathlib import Path
from dotenv import load_dotenv

# Figure out whether we're inside Docker or running locally
# Docker-compose mounts `.env.docker`, local runs with `.env.local`
env_dir = Path(__file__).resolve().parent.parent  # points to services/main/
docker_env = env_dir / ".env.docker"
local_env = env_dir / ".env.local"

if docker_env.exists():
    load_dotenv(docker_env)
elif local_env.exists():
    load_dotenv(local_env)

# Now pull vars
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
# POSTGEN_SERVICE_URL = os.getenv("POSTGEN_SERVICE_URL", "http://postgen-service:8000")
POSTGEN_SERVICE_URL = os.getenv("POSTGEN_SERVICE_URL", "http://postpilot-postgen-service-1:8000")
SCRAPER_SERVICE_URL = os.getenv("SCRAPER_SERVICE_URL", "http://scraper-service:8000")

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
