"""Ollama model provider using its local HTTP API."""

import json
from collections.abc import AsyncIterator

import httpx


class OllamaError(RuntimeError):
    """Raised when Ollama is unavailable or returns an invalid response."""


class OllamaProvider:
    """Streaming provider for a local Ollama server."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def list_models(self) -> list[str]:
        """Return locally installed Ollama model names."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            raise OllamaError(
                "Cannot connect to Ollama. Start Ollama and try again."
            ) from exc

        payload = response.json()
        return [item["name"] for item in payload.get("models", []) if item.get("name")]

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Stream assistant text from Ollama's chat endpoint."""
        if not self.model:
            raise OllamaError("No Ollama model is selected.")

        request = {"model": self.model, "messages": messages, "stream": True}
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/chat", json=request
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            payload = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if payload.get("error"):
                            raise OllamaError(str(payload["error"]))
                        content = payload.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if payload.get("done"):
                            break
        except OllamaError:
            raise
        except (httpx.HTTPError, OSError) as exc:
            raise OllamaError(
                "Cannot connect to Ollama. Start Ollama and try again."
            ) from exc
