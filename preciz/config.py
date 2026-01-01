"""Configuration management for Preciz."""

import os
from dataclasses import dataclass
from typing import Literal
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Application configuration."""

    api_key: str
    model: str
    provider: Literal["openrouter", "openai"]
    base_url: str | None = None
    max_retries: int = 3
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        provider = os.getenv("API_PROVIDER", "openrouter")

        if provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY", "")
            base_url = "https://openrouter.ai/api/v1"
            model = os.getenv("LLM_MODEL", "xiaomi/mimo-v2-flash:free")
        else:
            api_key = os.getenv("OPENAI_API_KEY", "")
            base_url = None
            model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        if not api_key:
            raise ValueError(
                f"API key not found. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
            )

        return cls(
            api_key=api_key,
            model=model,
            provider=provider,
            base_url=base_url,
        )
