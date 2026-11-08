import asyncio
import json

import httpx
import pytest

from aiko.ai.conversation_service import build_context
from aiko.ai.ollama_client import OllamaClient, OllamaError, final_answer
from aiko.characters.profile import CharacterManager
from aiko.config import Settings


def test_final_only_and_request_contract():
    def handler(request):
        body = json.loads(request.content)
        assert body["think"] is False
        assert body["options"] == {"num_ctx": 4096, "num_predict": 768}
        return httpx.Response(
            200,
            content=b'{"message":{"thinking":"secret","content":"<think>hidden</think>Hello"},"done":true}\n',
        )

    client = OllamaClient(Settings(), httpx.MockTransport(handler))
    assert asyncio.run(client.chat([{"role": "user", "content": "Hi"}])) == "Hello"


@pytest.mark.parametrize(
    "body",
    [
        b"no json\n",
        b'{"message":{"content":42}}\n',
        b'{"message":{"content":"unfinished"}}\n',
        b'{"error":"private server data"}\n',
    ],
)
def test_malformed_and_incomplete_streams(body):
    client = OllamaClient(
        Settings(), httpx.MockTransport(lambda r: httpx.Response(200, content=body))
    )
    with pytest.raises(OllamaError):
        asyncio.run(client.chat([]))


@pytest.mark.parametrize("status", [400, 404, 500, 302])
def test_server_errors_and_redirects(status):
    client = OllamaClient(Settings(), httpx.MockTransport(lambda r: httpx.Response(status)))
    with pytest.raises(OllamaError):
        asyncio.run(client.chat([]))


def test_connection_failure():
    def handler(request):
        raise httpx.ConnectError("private details", request=request)

    with pytest.raises(OllamaError, match="Cannot reach local"):
        asyncio.run(OllamaClient(Settings(), httpx.MockTransport(handler)).check())


def test_missing_model():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"models": []}))
    with pytest.raises(OllamaError, match="ollama pull qwen3:8b"):
        asyncio.run(OllamaClient(Settings(), transport).check())


def test_reasoning_fragments():
    assert final_answer("<think>unfinished") == ""
    assert final_answer("hidden</think>Final") == "Final"


def test_context_budget():
    profile = CharacterManager().current()
    history = [{"role": role, "content": "z" * 600} for role in ["user", "assistant"] * 10]
    result = build_context(profile, history, 4096)
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"
    assert len(result) < len(history)
    with pytest.raises(ValueError, match="too long"):
        build_context(profile, [{"role": "user", "content": "ž" * 5000}], 4096)
