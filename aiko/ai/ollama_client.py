import asyncio
import json
import re
from collections.abc import Callable

import httpx

from aiko.config import Settings


class OllamaError(Exception):
    """Safe actionable text suitable for the UI (never raw server bodies)."""


def final_answer(text: str) -> str:
    text = re.sub(r"<think\b[^>]*>.*?</think\s*>", "", text, flags=re.I | re.S)
    text = re.sub(r"<think\b[^>]*>.*$", "", text, flags=re.I | re.S)
    # A closing tag without its opener is ambiguous: discard the preceding fragment.
    if re.search(r"</think\s*>", text, re.I):
        text = re.split(r"</think\s*>", text, flags=re.I)[-1]
    return text.strip()


class OllamaClient:
    def __init__(self, settings: Settings, transport=None):
        self.settings = settings.validate()
        self.transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.settings.ollama_url.rstrip("/"), trust_env=False,
            follow_redirects=False, timeout=httpx.Timeout(90, connect=3),
            transport=self.transport,
        )

    def _status(self, response: httpx.Response) -> None:
        if response.status_code == 404:
            raise OllamaError(f"Model or endpoint missing. Check ollama list; if needed, run: ollama pull {self.settings.model}")
        if response.status_code == 400:
            raise OllamaError("Ollama rejected the request. Use an up-to-date Ollama and a model supporting think:false, such as qwen3:8b.")
        if response.status_code != 200:
            raise OllamaError(f"Ollama returned HTTP {response.status_code}. Check the local Ollama application.")

    async def check(self) -> str:
        try:
            async with self._client() as client:
                response = await client.get("/api/tags")
                self._status(response)
                models = response.json()["models"]
                names = {model["name"] for model in models}
                wanted = self.settings.model
                if wanted not in names and f"{wanted}:latest" not in names:
                    raise OllamaError(f"Ollama reachable; model missing. Run explicitly: ollama pull {wanted}")
                return f"Local Ollama reachable · {wanted} installed (checked now)"
        except httpx.TimeoutException as exc:
            raise OllamaError("Ollama check timed out. Check the local server and retry.") from exc
        except httpx.RequestError as exc:
            raise OllamaError("Cannot reach local Ollama. Start Ollama from Start, or run ollama serve, then Check connection.") from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise OllamaError("Ollama returned an invalid model list. Check its version and URL.") from exc

    async def chat(self, messages: list[dict], progress: Callable[[], None] | None = None) -> str:
        payload = {
            "model": self.settings.model, "messages": messages, "stream": True,
            "think": False, "keep_alive": "5m",
            "options": {"num_ctx": self.settings.context_size, "num_predict": 768},
        }
        parts: list[str] = []
        total = 0
        wire_size = 0
        done = False
        try:
            async with asyncio.timeout(180):
                async with self._client() as client:
                    async with client.stream("POST", "/api/chat", json=payload) as response:
                        self._status(response)
                        buffer = b""
                        async for chunk in response.aiter_bytes():
                            wire_size += len(chunk)
                            if wire_size > 1_000_000:
                                raise OllamaError("Ollama response exceeded the safety limit. Try a shorter request.")
                            buffer += chunk
                            if len(buffer) > 128_000:
                                raise OllamaError("Ollama returned an oversized response frame.")
                            while b"\n" in buffer:
                                line, buffer = buffer.split(b"\n", 1)
                                if not line.strip():
                                    continue
                                event = json.loads(line)
                                if not isinstance(event, dict) or "error" in event:
                                    raise OllamaError("Ollama interrupted generation. Check the model and available memory.")
                                message = event.get("message", {})
                                content = message.get("content", "")
                                if not isinstance(content, str):
                                    raise ValueError("invalid content")
                                parts.append(content)
                                total += len(content)
                                if total > 32000:
                                    raise OllamaError("Answer exceeded 32,000 characters. Ask for a shorter answer.")
                                if progress:
                                    progress()
                                if event.get("done") is True:
                                    done = True
                            if done:
                                break
                        if not done:
                            raise OllamaError("Ollama stream ended before completion. Please retry.")
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise OllamaError("Generation timed out (90s silence / 180s total). Try a shorter prompt or check Ollama.") from exc
        except httpx.RequestError as exc:
            raise OllamaError("Connection to local Ollama failed or was interrupted. Start Ollama and retry.") from exc
        except (ValueError, TypeError, AttributeError) as exc:
            raise OllamaError("Ollama returned malformed chat data. Check its version and retry.") from exc
        answer = final_answer("".join(parts))
        if not answer:
            raise OllamaError("The model returned no final answer. Use qwen3:8b with current Ollama and try again.")
        return answer
