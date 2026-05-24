import os
from pydantic_settings import BaseSettings
from pydantic import Field

# Get absolute path to the .env file in the backend directory
base_dir = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(base_dir, ".env")

class Settings(BaseSettings):
    # Defaulting to local postgres or sqlite fallback for development flexibility
    DATABASE_URL: str = Field(
        default="sqlite:///./noorinvest.db",
        validation_alias="DATABASE_URL"
    )
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        validation_alias="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    class Config:
        env_file = env_file_path
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Fix for Supabase/render database URL to route to pg8000 dialect
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
elif settings.DATABASE_URL.startswith("postgresql://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
