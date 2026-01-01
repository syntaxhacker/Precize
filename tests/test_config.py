"""Tests for config module."""

import os
from unittest.mock import patch

import pytest

from preciz.config import Config
from preciz.config import Config


@pytest.fixture
def clear_env():
    """Clear environment variables before each test."""
    original = os.environ.copy()
    os.environ.clear()
    yield
    os.environ.clear()
    os.environ.update(original)


class TestConfig:
    """Test Config dataclass."""

    def test_from_env_openrouter(self, clear_env):
        """Test config from env with OpenRouter provider."""
        os.environ["API_PROVIDER"] = "openrouter"
        os.environ["OPENROUTER_API_KEY"] = "test-key-123"
        os.environ["LLM_MODEL"] = "xiaomi/mimo-v2-flash:free"

        config = Config.from_env()

        assert config.provider == "openrouter"
        assert config.api_key == "test-key-123"
        assert config.model == "xiaomi/mimo-v2-flash:free"
        assert config.base_url == "https://openrouter.ai/api/v1"

    def test_from_env_openai(self, clear_env):
        """Test config from env with OpenAI provider."""
        os.environ["API_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "sk-test-123"
        os.environ["LLM_MODEL"] = "gpt-4o-mini"

        config = Config.from_env()

        assert config.provider == "openai"
        assert config.api_key == "sk-test-123"
        assert config.model == "gpt-4o-mini"
        assert config.base_url is None

    def test_from_env_defaults(self, clear_env):
        """Test default values when env vars are missing."""
        os.environ["OPENROUTER_API_KEY"] = "test-key"

        config = Config.from_env()

        assert config.provider == "openrouter"
        assert config.model == "xiaomi/mimo-v2-flash:free"
        assert config.max_retries == 3
        assert config.timeout == 60

    def test_from_env_missing_api_key(self, clear_env):
        """Test error when API key is missing."""
        with pytest.raises(ValueError, match="API key not found"):
            Config.from_env()

    def test_config_is_frozen(self):
        """Test that Config is frozen (immutable)."""
        config = Config(
            api_key="test",
            model="test-model",
            provider="openrouter",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            config.api_key = "new-key"
