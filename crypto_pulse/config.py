from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    coingecko_demo_api_key: str = os.getenv("COINGECKO_DEMO_API_KEY", "")
    default_query: str = os.getenv("DEFAULT_QUERY", "crypto")
    default_days: int = int(os.getenv("DEFAULT_DAYS", "30"))
    max_items_per_source: int = int(os.getenv("MAX_ITEMS_PER_SOURCE", "20"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "8"))


def get_settings() -> Settings:
    return Settings()
