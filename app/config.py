import os
from typing import Set
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    ALLOWED_TELEGRAM_USER_IDS: str = ""  # Comma-separated user IDs, e.g., "1234567,8901234"
    
    GITLAB_URL: str = "https://gitlab.com"
    GITLAB_PERSONAL_ACCESS_TOKEN: str = ""
    GITLAB_PROJECT_ID: str = ""  # Numeric ID or path-with-namespace string
    
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    WEBHOOK_SECRET_TOKEN: str = "default_secret_token"
    
    # Automatically load values from a .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @property
    def allowed_users(self) -> Set[int]:
        """Convert ALLOWED_TELEGRAM_USER_IDS string to a set of integers for quick lookup."""
        if not self.ALLOWED_TELEGRAM_USER_IDS:
            return set()
        try:
            return {int(uid.strip()) for uid in self.ALLOWED_TELEGRAM_USER_IDS.split(",") if uid.strip()}
        except ValueError:
            # Fallback if config format is invalid
            return set()

# Global settings instance
settings = Settings()
