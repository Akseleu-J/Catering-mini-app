"""
config/settings.py
Loads all environment variables via pydantic-settings.
Single source of truth for all configuration.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Bot ──────────────────────────────────────────────────
    bot_token: str = Field(..., env="BOT_TOKEN")
    admin_id: int = Field(..., env="ADMIN_ID")
    admin_phone: str = Field("77001234567", env="ADMIN_PHONE")
    admin_whatsapp: str = Field("77001234567", env="ADMIN_WHATSAPP")

    # ── Database ─────────────────────────────────────────────
    database_url: str = Field(..., env="DATABASE_URL")

    # ── AI ───────────────────────────────────────────────────
    gemini_key: str = Field(..., env="GEMINI_KEY")
    gemini_model: str = "gemini-1.5-flash"

    # ── Business ─────────────────────────────────────────────
    min_lead_hours: int = 24       # Minimum hours before event
    items_per_page: int = 5        # Pagination size

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()
