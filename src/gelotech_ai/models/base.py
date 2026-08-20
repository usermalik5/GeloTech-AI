"""Common interface for AI model providers."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ToolCall:
    """A tool request emitted by the model."""

    name: str
    arguments: dict[str, object]


@dataclass(frozen=True)
class AgentEvent:
    """One streamed event from an agent-capable model: text and/or tool calls."""

    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()


class ModelProvider(Protocol):
    """Minimal streaming interface used by the agent layer."""

    async def list_models(self) -> list[str]:
        """Return model names available from the provider."""
        return []

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Yield text chunks for a conversation."""
        yield ""

    async def stream_agent(
        self, messages: list[dict[str, object]], tools: list[dict[str, object]]
    ) -> AsyncIterator[AgentEvent]:
        """Yield text and tool-call events for a tool-enabled conversation."""
        yield AgentEvent()