"""
Model interface abstractions for MAVEN.

This module provides abstract base classes and concrete implementations
for integrating various AI model providers.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ModelInterface(ABC):
    """Abstract interface for AI model integration.

    All model implementations must inherit from this class and
    implement the generate() method.
    """

    def __init__(self, model_id: str):
        """Initialize model interface.

        Args:
            model_id: Identifier for the specific model.
        """
        self.model_id = model_id

    @abstractmethod
    def generate(self, prompt: str, role: str) -> str:
        """Generate a response for the given prompt and role.

        Args:
            prompt: The formatted prompt including system instructions.
            role: The role this model is playing (architect/skeptic/mediator).

        Returns:
            The model's response text.

        Raises:
            ModelError: If generation fails.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model_id={self.model_id!r})"


class ClaudeModel(ModelInterface):
    """Anthropic Claude model integration."""

    def __init__(self, model_id: str = "claude-sonnet-4"):
        """Initialize Claude model.

        Args:
            model_id: Claude model identifier.
        """
        super().__init__(model_id)
        self._client: Optional[object] = None

    @property
    def client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic package not installed")
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, role: str) -> str:
        """Generate response using Claude API."""
        logger.debug(f"Generating with Claude ({self.model_id}) as {role}")

        message = self.client.messages.create(
            model=self.model_id,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text


class GPTModel(ModelInterface):
    """OpenAI GPT model integration."""

    def __init__(self, model_id: str = "gpt-4"):
        """Initialize GPT model.

        Args:
            model_id: GPT model identifier.
        """
        super().__init__(model_id)
        self._client: Optional[object] = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")
                self._client = openai.OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openai package not installed")
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, role: str) -> str:
        """Generate response using OpenAI API."""
        logger.debug(f"Generating with GPT ({self.model_id}) as {role}")

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )

        return response.choices[0].message.content


class GeminiModel(ModelInterface):
    """Google Gemini model integration."""

    def __init__(self, model_id: str = "gemini-pro"):
        """Initialize Gemini model.

        Args:
            model_id: Gemini model identifier.
        """
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
                    raise ValueError("GOOGLE_API_KEY environment variable not set")
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel(self.model_id)
            except ImportError:
                raise ImportError("google-generativeai package not installed")
        return self._model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, role: str) -> str:
        """Generate response using Gemini API."""
        logger.debug(f"Generating with Gemini ({self.model_id}) as {role}")

        response = self.model.generate_content(prompt)

        return response.text


class TogetherModel(ModelInterface):
    """Together AI model integration.

    Together AI provides access to various open-source models like
    Llama, Mistral, Qwen, and others through an OpenAI-compatible API.

    Supported models include:
        - meta-llama/Llama-3.3-70B-Instruct-Turbo
        - meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo
        - mistralai/Mixtral-8x22B-Instruct-v0.1
        - Qwen/Qwen2.5-72B-Instruct-Turbo
        - deepseek-ai/DeepSeek-R1-Distill-Llama-70B
        - And many more at https://docs.together.ai/docs/chat-models
    """

    def __init__(self, model_id: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"):
        """Initialize Together AI model.

        Args:
            model_id: Together AI model identifier (e.g., "meta-llama/Llama-3.3-70B-Instruct-Turbo").
        """
        super().__init__(model_id)
        self._client: Optional[object] = None

    @property
    def client(self):
        """Lazy initialization of Together AI client (OpenAI-compatible)."""
        if self._client is None:
            try:
                import openai
                api_key = os.environ.get("TOGETHER_API_KEY")
                if not api_key:
                    raise ValueError("TOGETHER_API_KEY environment variable not set")
                self._client = openai.OpenAI(
                    api_key=api_key,
                    base_url="https://api.together.xyz/v1",
                )
            except ImportError:
                raise ImportError("openai package not installed (required for Together AI)")
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, role: str) -> str:
        """Generate response using Together AI API."""
        logger.debug(f"Generating with Together AI ({self.model_id}) as {role}")

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )

        return response.choices[0].message.content


class MockModel(ModelInterface):
    """Mock model for testing purposes."""

    def __init__(self, model_id: str = "mock-model", responses: Optional[dict] = None):
        """Initialize mock model.

        Args:
            model_id: Mock model identifier.
            responses: Optional dict mapping roles to responses.
        """
        super().__init__(model_id)
        self.responses = responses or {}
        self.call_count = 0

    def generate(self, prompt: str, role: str) -> str:
        """Return mock response."""
        self.call_count += 1

        if role in self.responses:
            return self.responses[role]

        return f"Mock response from {self.model_id} as {role}"


# Common Together AI model aliases for convenience
TOGETHER_MODEL_ALIASES = {
    "llama-3.3-70b": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "llama-3.1-405b": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "llama-3.1-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "llama-3.1-8b": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "mixtral-8x22b": "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "qwen-2.5-72b": "Qwen/Qwen2.5-72B-Instruct-Turbo",
    "qwen-2.5-7b": "Qwen/Qwen2.5-7B-Instruct-Turbo",
    "deepseek-r1-70b": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
}


def resolve_model_alias(model_id: str) -> str:
    """Resolve model aliases to full model IDs.

    Args:
        model_id: Model identifier or alias.

    Returns:
        Full model identifier.
    """
    return TOGETHER_MODEL_ALIASES.get(model_id.lower(), model_id)


def create_model(model_id: str) -> ModelInterface:
    """Factory function to create appropriate model instance.

    Args:
        model_id: Model identifier string. Supports:
            - Claude models: "claude-sonnet-4", "claude-opus-4", etc.
            - GPT models: "gpt-4", "gpt-4-turbo", etc.
            - Gemini models: "gemini-pro", "gemini-ultra", etc.
            - Together AI models: "together/llama-3.3-70b" or full model paths
            - Mock models: "mock-model" (for testing)

    Returns:
        Appropriate ModelInterface implementation.

    Raises:
        ValueError: If model type is not recognized.
    """
    model_id_lower = model_id.lower()

    # Check for Together AI models (prefix or known patterns)
    if model_id_lower.startswith("together/"):
        # Strip prefix and resolve alias
        together_model = model_id[9:]  # Remove "together/"
        resolved = resolve_model_alias(together_model)
        return TogetherModel(resolved)
    elif "/" in model_id and any(
        org in model_id_lower for org in ["meta-llama", "mistralai", "qwen", "deepseek"]
    ):
        # Direct Together AI model path
        return TogetherModel(model_id)
    elif model_id_lower in TOGETHER_MODEL_ALIASES:
        # Together AI alias without prefix
        resolved = resolve_model_alias(model_id)
        return TogetherModel(resolved)

    # Standard providers
    if "claude" in model_id_lower:
        return ClaudeModel(model_id)
    elif "gpt" in model_id_lower:
        return GPTModel(model_id)
    elif "gemini" in model_id_lower:
        return GeminiModel(model_id)
    elif "mock" in model_id_lower:
        return MockModel(model_id)
    else:
        raise ValueError(
            f"Unknown model type: {model_id}. "
            f"Supported: claude-*, gpt-*, gemini-*, together/*, or Together AI model paths"
        )
