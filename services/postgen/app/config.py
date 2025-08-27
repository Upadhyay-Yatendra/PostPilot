import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env.docker"
if env_path.exists():
    load_dotenv(env_path)

SCRAPER_SERVICE_URL = os.getenv("SCRAPER_SERVICE_URL", "http://scraper-service:8000")
