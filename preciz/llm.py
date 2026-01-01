"""LLM client for OpenAI/OpenRouter API."""

from dataclasses import dataclass
from dataclasses import field
from typing import Literal

from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from .config import Config


@dataclass(frozen=True)
class Message:
    """Chat message."""

    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class LLMResponse:
    """LLM response."""

    content: str
    model: str
    finish_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMClient:
    """LLM client supporting OpenAI and OpenRouter."""

    config: Config
    client: OpenAI = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize OpenAI client."""
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout,
        )

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert Message objects to API format."""
        return [{"role": m.role, "content": m.content} for m in messages]

    def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Get completion from LLM.

        Args:
            messages: List of chat messages.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with generated content.
        """
        api_messages = self._convert_messages(messages)

        response: ChatCompletion = self.client.chat.completions.create(
            model=self.config.model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            finish_reason=choice.finish_reason,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )

    def complete_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Stream completion from LLM.

        Args:
            messages: List of chat messages.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.

        Yields:
            Content chunks as they arrive.
        """
        api_messages = self._convert_messages(messages)

        stream: Stream[ChatCompletionChunk] = self.client.chat.completions.create(
            model=self.config.model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
