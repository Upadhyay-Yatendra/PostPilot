from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


    # Mongo
    MONGODB_URI: str = Field(..., description="Mongo connection URI")
    MONGO_DB_NAME: str = Field("linkedin_scraper")
    POSTS_COLLECTION: str = Field("posts")


    # LinkedIn credentials
    LINKEDIN_EMAIL: str | None = None
    LINKEDIN_PASSWORD: str | None = None


    # Selenium
    SELENIUM_HEADLESS: bool = Field(False)


settings = Settings()