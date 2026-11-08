"""Explicit opt-in integration test; never downloads a model."""

import asyncio
import os

import pytest

from aiko.ai.ollama_client import OllamaClient
from aiko.config import Settings


@pytest.mark.skipif(
    os.environ.get("AIKO_TEST_LIVE") != "1",
    reason="Set AIKO_TEST_LIVE=1 to use installed local Ollama",
)
def test_installed_qwen_final_answer():
    async def run():
        client = OllamaClient(Settings())
        assert "installed" in await client.check()
        answer = await client.chat(
            [{"role": "user", "content": "Reply with a short greeting in Serbian, no explanation."}]
        )
        assert answer.strip()
        assert "<think>" not in answer.lower()

    asyncio.run(run())
