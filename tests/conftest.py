"""Shared pytest fixtures. No test in this suite calls a real model API."""

import importlib

import pytest

API_KEY_VARS = ("TOGETHER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")


@pytest.fixture(scope="session", autouse=True)
def _preload_provider_sdks():
    """Import the provider SDKs once, so timing checks measure calls rather than imports."""
    for module in ("openai", "anthropic", "google.generativeai"):
        importlib.import_module(module)


@pytest.fixture
def no_api_keys(monkeypatch):
    """Remove every provider API key from the environment for one test."""
    for var in API_KEY_VARS:
        monkeypatch.delenv(var, raising=False)
