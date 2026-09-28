"""Shared pytest fixtures. No test in this suite calls a real model API."""

import pytest

API_KEY_VARS = ("TOGETHER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")


@pytest.fixture
def no_api_keys(monkeypatch):
    """Remove every provider API key from the environment for one test."""
    for var in API_KEY_VARS:
        monkeypatch.delenv(var, raising=False)
