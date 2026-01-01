"""Tests for LLM client."""

from unittest.mock import MagicMock, patch

import pytest

from preciz.config import Config
from preciz.llm import LLMClient, Message, LLMResponse


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    return Config(
        api_key="test-key",
        model="test-model",
        provider="openrouter",
        base_url="https://test.api/v1",
    )


@pytest.fixture
def mock_completion():
    """Create a mock completion response."""
    mock = MagicMock()
    mock.model = "test-model"
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = "Test response"
    mock.choices[0].finish_reason = "stop"
    mock.usage.prompt_tokens = 10
    mock.usage.completion_tokens = 20
    return mock


class TestMessage:
    """Test Message dataclass."""

    def test_create_message(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_is_frozen(self):
        """Test that Message is frozen."""
        msg = Message(role="user", content="Hello")
        with pytest.raises(Exception):
            msg.content = "World"


class TestLLMClient:
    """Test LLMClient class."""

    def test_init_client(self, mock_config):
        """Test initializing the client."""
        client = LLMClient(mock_config)
        assert client.config == mock_config
        assert client.client is not None

    @patch("preciz.llm.OpenAI")
    def test_complete(self, mock_openai, mock_config, mock_completion):
        """Test getting a completion."""
        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        client = LLMClient(mock_config)
        messages = [
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hello"),
        ]

        response = client.complete(messages)

        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.input_tokens == 10
        assert response.output_tokens == 20

    @patch("preciz.llm.OpenAI")
    def test_complete_with_temperature(self, mock_openai, mock_config, mock_completion):
        """Test completion with custom temperature."""
        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        client = LLMClient(mock_config)
        messages = [Message(role="user", content="Hello")]

        client.complete(messages, temperature=0.5, max_tokens=1000)

        # Verify the call was made with correct params
        call_args = mock_openai.return_value.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.5
        assert call_args.kwargs["max_tokens"] == 1000

    def test_convert_messages(self, mock_config):
        """Test converting Message objects to API format."""
        client = LLMClient(mock_config)
        messages = [
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hello"),
        ]

        api_messages = client._convert_messages(messages)

        assert api_messages == [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]


class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_create_response(self):
        """Test creating a response."""
        response = LLMResponse(
            content="Hello",
            model="gpt-4",
            finish_reason="stop",
            input_tokens=10,
            output_tokens=5,
        )
        assert response.content == "Hello"
        assert response.model == "gpt-4"
        assert response.finish_reason == "stop"
        assert response.input_tokens == 10
        assert response.output_tokens == 5

    def test_response_defaults(self):
        """Test response with default values."""
        response = LLMResponse(content="Hello", model="gpt-4")
        assert response.finish_reason is None
        assert response.input_tokens == 0
        assert response.output_tokens == 0
