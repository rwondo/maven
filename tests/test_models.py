"""Tests for the provider adapters: routing, missing keys and retries."""

import time
from types import SimpleNamespace

import pytest
from tenacity import wait_none

from maven.async_models import (
    AsyncClaudeModel,
    AsyncGeminiModel,
    AsyncGPTModel,
    AsyncMockModel,
    AsyncTogetherModel,
    create_async_model,
)
from maven.models import (
    ClaudeModel,
    GeminiModel,
    GPTModel,
    MockModel,
    ModelConfigError,
    TogetherModel,
    create_model,
)


@pytest.mark.parametrize(
    ("model_id", "cls", "resolved_id"),
    [
        ("together/llama-3.1-8b", TogetherModel, "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"),
        ("qwen-2.5-7b", TogetherModel, "Qwen/Qwen2.5-7B-Instruct-Turbo"),
        (
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            TogetherModel,
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
        ),
        ("together/some-org/new-model", TogetherModel, "some-org/new-model"),
        ("claude-sonnet-4", ClaudeModel, "claude-sonnet-4"),
        ("gpt-4o", GPTModel, "gpt-4o"),
        ("gemini-2.0-flash", GeminiModel, "gemini-2.0-flash"),
        ("mock-a", MockModel, "mock-a"),
    ],
)
def test_create_model_routes_by_name(model_id, cls, resolved_id):
    model = create_model(model_id)
    assert type(model) is cls
    assert model.model_id == resolved_id


@pytest.mark.parametrize(
    ("model_id", "cls"),
    [
        ("together/llama-3.1-8b", AsyncTogetherModel),
        ("claude-sonnet-4", AsyncClaudeModel),
        ("gpt-4o", AsyncGPTModel),
        ("gemini-2.0-flash", AsyncGeminiModel),
        ("mock-a", AsyncMockModel),
    ],
)
def test_create_async_model_routes_by_name(model_id, cls):
    assert type(create_async_model(model_id)) is cls


def test_unknown_model_is_rejected():
    with pytest.raises(ValueError, match="Unknown model type"):
        create_model("some-unknown-model")


@pytest.mark.parametrize(
    ("model", "env_var"),
    [
        (TogetherModel("meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"), "TOGETHER_API_KEY"),
        (GPTModel("gpt-4o"), "OPENAI_API_KEY"),
        (ClaudeModel("claude-sonnet-4"), "ANTHROPIC_API_KEY"),
        (GeminiModel("gemini-2.0-flash"), "GOOGLE_API_KEY"),
    ],
)
def test_missing_key_fails_fast_without_retrying(no_api_keys, model, env_var):
    start = time.monotonic()
    with pytest.raises(ModelConfigError, match=env_var):
        model.generate("prompt", "reliability_check")
    assert time.monotonic() - start < 1.0  # retries would wait 2s+ between attempts


async def test_async_missing_key_fails_fast(no_api_keys):
    start = time.monotonic()
    with pytest.raises(ModelConfigError, match="TOGETHER_API_KEY"):
        await AsyncTogetherModel("meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo").generate("p", "r")
    assert time.monotonic() - start < 1.0


def fake_openai_client(outcomes):
    """Client whose chat.completions.create() raises or returns each outcome in turn."""
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        message = SimpleNamespace(content=outcome)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return client, calls


def test_transient_api_errors_are_retried():
    model = TogetherModel("some/model")
    model._client, calls = fake_openai_client([TimeoutError(), TimeoutError(), "VERDICT: RELIABLE"])
    generate_now = TogetherModel.generate.retry_with(wait=wait_none())

    assert generate_now(model, "prompt", "role") == "VERDICT: RELIABLE"
    assert len(calls) == 3


def test_last_api_error_is_raised_after_three_attempts():
    model = TogetherModel("some/model")
    model._client, calls = fake_openai_client([TimeoutError("slow")] * 3)
    generate_now = TogetherModel.generate.retry_with(wait=wait_none())

    with pytest.raises(TimeoutError, match="slow"):  # the provider's error, not RetryError
        generate_now(model, "prompt", "role")
    assert len(calls) == 3
