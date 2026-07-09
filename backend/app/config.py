import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@db:5432/tao_db"
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Gemini settings (new SDK)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"  # or gemini-1.5-pro, gemini-2.5-flash, gemini-2.0-flash
    PROVIDER: str = "openai"  # "openai" or "gemini"

    KOBO_API_TOKEN: str = ""
    KOBO_ASSET_ID: str = ""

    class Config:
        env_file = ".env"

settings = Settings()