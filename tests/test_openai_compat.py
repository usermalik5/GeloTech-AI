import asyncio
from collections.abc import AsyncIterator

import httpx
import pytest

from gelotech_ai.models.base import AgentEvent
from gelotech_ai.models.openai_compat import OpenAICompatError, OpenAICompatProvider


async def collect(agen: AsyncIterator[str]) -> str:
    parts: list[str] = []
    async for part in agen:
        parts.append(part)
    return "".join(parts)


def make_provider(handler: httpx.MockTransport) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        base_url="https://example.test/v1",
        api_key="test-key",
        model="deepseek-chat",
        transport=handler,
    )


def test_list_models_parses_ids() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={"data": [{"id": "deepseek-chat"}, {"id": "deepseek-reasoner"}]},
        )

    provider = make_provider(httpx.MockTransport(handler))

    assert asyncio.run(provider.list_models()) == [
        "deepseek-chat",
        "deepseek-reasoner",
    ]


def test_list_models_requires_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": []})

    provider = OpenAICompatProvider(
        base_url="https://example.test/v1",
        api_key="",
        model="x",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(OpenAICompatError, match="API key"):
        asyncio.run(provider.list_models())


def test_stream_yields_content_chunks() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = (
            'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
            'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
            'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            "data: [DONE]\n\n"
        )
        return httpx.Response(200, content=body)

    provider = make_provider(httpx.MockTransport(handler))

    assert asyncio.run(collect(provider.stream([]))) == "Hello world"


def test_stream_agent_accumulates_tool_calls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert '"tools"' in request.content.decode()
        body = (
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,'
            '"function":{"name":"search_","arguments":"{\\"pat"}}]}}]}\n\n'
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,'
            '"function":{"name":"files","arguments":"tern\\": \\"login\\"}"}}]}}]}\n\n'
            'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}\n\n'
            "data: [DONE]\n\n"
        )
        return httpx.Response(200, content=body)

    provider = make_provider(httpx.MockTransport(handler))

    events: list[AgentEvent] = []

    async def run() -> None:
        async for event in provider.stream_agent([], [{"type": "function"}]):
            events.append(event)

    asyncio.run(run())

    assert len(events) == 1
    (call,) = events[0].tool_calls
    assert call.name == "search_files"
    assert call.arguments == {"pattern": "login"}


def test_stream_reports_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401, json={"error": {"message": "Invalid API key"}}
        )

    provider = make_provider(httpx.MockTransport(handler))

    with pytest.raises(OpenAICompatError, match="401"):
        asyncio.run(collect(provider.stream([])))