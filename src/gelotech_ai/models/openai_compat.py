"""OpenAI-compatible cloud model provider.

Covers DeepSeek, OpenRouter (including free models), Groq, Together, and any
other service exposing the OpenAI chat-completions API. The API key is read
from the ``GELOTECH_API_KEY`` environment variable or passed explicitly; it is
never written to disk or logged.
"""

import json
import os
from collections.abc import AsyncIterator

import httpx

from gelotech_ai.models.base import AgentEvent, ToolCall

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"


class OpenAICompatError(RuntimeError):
    """Raised when the cloud provider is unreachable or returns an error."""


class OpenAICompatProvider:
    """Streaming, tool-capable provider for OpenAI-compatible APIs."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str = "",
        model: str = "",
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("GELOTECH_API_KEY", "")
        self.model = model
        self._transport = transport

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise OpenAICompatError(
                "No API key. Set the GELOTECH_API_KEY environment variable or "
                "enter a key in the toolbar."
            )
        return {"Authorization": f"Bearer {self.api_key}"}

    async def list_models(self) -> list[str]:
        """Return model IDs advertised by the provider."""
        try:
            async with httpx.AsyncClient(timeout=15, transport=self._transport) as client:
                response = await client.get(f"{self.base_url}/models", headers=self._headers())
            if response.status_code >= 400:
                raise OpenAICompatError(self._error_message(response))
        except OpenAICompatError:
            raise
        except (httpx.HTTPError, OSError) as exc:
            raise OpenAICompatError(f"Cannot reach {self.base_url}: {exc}") from exc
        payload = response.json()
        return [
            str(item["id"])
            for item in payload.get("data", [])
            if isinstance(item, dict) and item.get("id")
        ]

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Stream assistant text from the chat completions endpoint."""
        async for event in self._stream_events(messages, tools=None):
            if event.content:
                yield event.content

    async def stream_agent(
        self, messages: list[dict[str, object]], tools: list[dict[str, object]]
    ) -> AsyncIterator[AgentEvent]:
        """Stream text and tool-call events."""
        async for event in self._stream_events(messages, tools=tools):
            yield event

    async def _stream_events(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]] | None,
    ) -> AsyncIterator[AgentEvent]:
        if not self.model:
            raise OpenAICompatError("No model is selected.")
        request: dict[str, object] = {"model": self.model, "messages": messages, "stream": True}
        if tools:
            request["tools"] = tools
        try:
            async with httpx.AsyncClient(timeout=None, transport=self._transport) as client, (
                client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=request,
                    headers=self._headers(),
                )
            ) as response:
                    if response.status_code >= 400:
                        body = await response.aread()
                        raise OpenAICompatError(self._error_message(response, body))
                    pending: dict[int, dict[str, str]] = {}
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            payload = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        choices = payload.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        content = delta.get("content") or ""
                        if content:
                            yield AgentEvent(content=content)
                        for raw_call in delta.get("tool_calls") or []:
                            if not isinstance(raw_call, dict):
                                continue
                            index = int(raw_call.get("index", 0))
                            entry = pending.setdefault(index, {"name": "", "arguments": ""})
                            fn = raw_call.get("function", {})
                            if not isinstance(fn, dict):
                                continue
                            entry["name"] += str(fn.get("name") or "")
                            entry["arguments"] += str(fn.get("arguments") or "")
                        if choices[0].get("finish_reason") == "tool_calls":
                            break
            calls = tuple(self._finalize_call(index, entry) for index, entry in sorted(pending.items()))
            if calls:
                yield AgentEvent(tool_calls=calls)
        except OpenAICompatError:
            raise
        except (httpx.HTTPError, OSError) as exc:
            raise OpenAICompatError(f"Cannot reach {self.base_url}: {exc}") from exc

    def _finalize_call(self, index: int, entry: dict[str, str]) -> ToolCall:
        raw = entry.get("arguments", "") or "{}"
        try:
            arguments = json.loads(raw)
        except json.JSONDecodeError:
            arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}
        return ToolCall(entry.get("name", ""), arguments)

    def _error_message(
        self, response: httpx.Response, body: bytes | None = None
    ) -> str:
        detail = ""
        if body:
            try:
                payload = json.loads(body)
                detail = str(payload.get("error", {}).get("message", ""))
            except json.JSONDecodeError:
                detail = body.decode("utf-8", errors="replace")[:300]
        return f"Provider error {response.status_code}: {detail}".strip()