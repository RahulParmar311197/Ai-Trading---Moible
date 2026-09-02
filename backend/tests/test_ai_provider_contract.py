import httpx
import pytest

from app.ai.provider import AIProviderError, HttpAIProvider


def test_http_provider_extracts_generic_output(monkeypatch):
    captured = {}

    def fake_post(endpoint, *, json, headers, timeout):
        captured.update(endpoint=endpoint, json=json, headers=headers, timeout=timeout)
        return httpx.Response(200, json={"output": {"summary": "ok"}})

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = HttpAIProvider("https://ai.example.test", api_key="secret", model="test-model", timeout=7)

    result = provider.complete(system="system", payload={"symbol": "NIFTY"})

    assert result == {"summary": "ok"}
    assert captured["json"] == {"model": "test-model", "system": "system", "input": {"symbol": "NIFTY"}}
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["timeout"] == 7


def test_http_provider_extracts_openai_style_json_content(monkeypatch):
    def fake_post(*args, **kwargs):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"summary":"ok"}'}}]},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = HttpAIProvider("https://ai.example.test")

    assert provider.complete(system="system", payload={}) == {"summary": "ok"}


def test_http_provider_rejects_non_json_model_content(monkeypatch):
    def fake_post(*args, **kwargs):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not json"}}]},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = HttpAIProvider("https://ai.example.test")

    with pytest.raises(AIProviderError, match="non-JSON"):
        provider.complete(system="system", payload={})


def test_http_provider_sanitizes_transport_errors(monkeypatch):
    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("private detail")

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = HttpAIProvider("https://ai.example.test")

    with pytest.raises(AIProviderError, match="request failed") as exc_info:
        provider.complete(system="system", payload={})
    assert "private detail" not in str(exc_info.value)


def test_http_provider_does_not_require_api_key(monkeypatch):
    captured = {}

    def fake_post(endpoint, *, json, headers, timeout):
        captured["headers"] = headers
        return httpx.Response(200, json={"summary": "ok"})

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = HttpAIProvider("https://ai.example.test")

    assert provider.complete(system="system", payload={}) == {"summary": "ok"}
    assert "Authorization" not in captured["headers"]
