"""
Async model interfaces for MAVEN.

This module provides asynchronous versions of model integrations
for use with AsyncConsensusOrchestrator.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class AsyncModelInterface(ABC):
    """Abstract interface for async AI model integration."""

    def __init__(self, model_id: str):
        """Initialize async model interface.

        Args:
            model_id: Identifier for the specific model.
        """
        self.model_id = model_id

    @abstractmethod
    async def generate(self, prompt: str, role: str) -> str:
        """Generate a response asynchronously.

        Args:
            prompt: The formatted prompt.
            role: The role this model is playing.

        Returns:
            The model's response text.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model_id={self.model_id!r})"


class AsyncClaudeModel(AsyncModelInterface):
    """Async Anthropic Claude model integration."""

    def __init__(self, model_id: str = "claude-sonnet-4"):
        super().__init__(model_id)
        self._client: Optional[object] = None

    @property
    def client(self):
        """Lazy initialization of async Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self._client = anthropic.AsyncAnthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic package not installed")
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, role: str) -> str:
        """Generate response using async Claude API."""
        logger.debug(f"Async generating with Claude ({self.model_id}) as {role}")

        message = await self.client.messages.create(
            model=self.model_id,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text


class AsyncGPTModel(AsyncModelInterface):
    """Async OpenAI GPT model integration."""

    def __init__(self, model_id: str = "gpt-4"):
        super().__init__(model_id)
        self._client: Optional[object] = None

    @property
    def client(self):
        """Lazy initialization of async OpenAI client."""
        if self._client is None:
            try:
                import openai
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self._client = openai.AsyncOpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openai package not installed")
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, role: str) -> str:
        """Generate response using async OpenAI API."""
        logger.debug(f"Async generating with GPT ({self.model_id}) as {role}")

        response = await self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )

        return response.choices[0].message.content


class AsyncGeminiModel(AsyncModelInterface):
    """Async Google Gemini model integration."""

    def __init__(self, model_id: str = "gemini-pro"):
        super().__init__(model_id)
        self._model: Optional[object] = None

    @property
    def model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            try:
                import google.generativeai as genai
                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not set")
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel(self.model_id)
            except ImportError:
                raise ImportError("google-generativeai package not installed")
        return self._model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, role: str) -> str:
        """Generate response using Gemini API.

        Note: google-generativeai doesn't have native async support,
        so we run in executor.
        """
        import asyncio
        logger.debug(f"Async generating with Gemini ({self.model_id}) as {role}")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(prompt)
        )

        return response.text


class AsyncTogetherModel(AsyncModelInterface):
    """Async Together AI model integration.

    Together AI provides access to various open-source models through
    an OpenAI-compatible API.
    """

    def __init__(self, model_id: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"):
        """Initialize async Together AI model.

        Args:
            model_id: Together AI model identifier.
        """
        super().__init__(model_id)
        self._client: Optional[object] = None

    @property
    def client(self):
        """Lazy initialization of async Together AI client."""
        if self._client is None:
            try:
                import openai
                api_key = os.environ.get("TOGETHER_API_KEY")
                if not api_key:
                    raise ValueError("TOGETHER_API_KEY not set")
                self._client = openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.together.xyz/v1",
                )
            except ImportError:
                raise ImportError("openai package not installed (required for Together AI)")
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, role: str) -> str:
        """Generate response using async Together AI API."""
        logger.debug(f"Async generating with Together AI ({self.model_id}) as {role}")

        response = await self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )

        return response.choices[0].message.content


class AsyncMockModel(AsyncModelInterface):
    """Async mock model for testing."""

    def __init__(self, model_id: str = "mock-model", responses: Optional[dict] = None):
        super().__init__(model_id)
        self.responses = responses or {}
        self.call_count = 0

    async def generate(self, prompt: str, role: str) -> str:
        """Return mock response."""
        self.call_count += 1

        if role in self.responses:
            return self.responses[role]

        return f"Async mock response from {self.model_id} as {role}"


# Import aliases from models module
from maven.models import TOGETHER_MODEL_ALIASES, resolve_model_alias


def create_async_model(model_id: str) -> AsyncModelInterface:
    """Factory function to create appropriate async model instance.

    Args:
        model_id: Model identifier string. Supports:
            - Claude models: "claude-sonnet-4", "claude-opus-4", etc.
            - GPT models: "gpt-4", "gpt-4-turbo", etc.
            - Gemini models: "gemini-pro", "gemini-ultra", etc.
            - Together AI models: "together/llama-3.3-70b" or full model paths
            - Mock models: "mock-model" (for testing)

    Returns:
        Appropriate AsyncModelInterface implementation.
    """
    model_id_lower = model_id.lower()

    # Check for Together AI models (prefix or known patterns)
    if model_id_lower.startswith("together/"):
        together_model = model_id[9:]  # Remove "together/"
        resolved = resolve_model_alias(together_model)
        return AsyncTogetherModel(resolved)
    elif "/" in model_id and any(
        org in model_id_lower for org in ["meta-llama", "mistralai", "qwen", "deepseek"]
    ):
        return AsyncTogetherModel(model_id)
    elif model_id_lower in TOGETHER_MODEL_ALIASES:
        resolved = resolve_model_alias(model_id)
        return AsyncTogetherModel(resolved)

    # Standard providers
    if "claude" in model_id_lower:
        return AsyncClaudeModel(model_id)
    elif "gpt" in model_id_lower:
        return AsyncGPTModel(model_id)
    elif "gemini" in model_id_lower:
        return AsyncGeminiModel(model_id)
    elif "mock" in model_id_lower:
        return AsyncMockModel(model_id)
    else:
        raise ValueError(
            f"Unknown model type: {model_id}. "
            f"Supported: claude-*, gpt-*, gemini-*, together/*, or Together AI model paths"
        )
