"""Common interface for AI model providers."""

from collections.abc import AsyncIterator
from typing import Protocol


class ModelProvider(Protocol):
    """Minimal streaming interface used by the agent layer."""

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Yield text chunks for a conversation."""
        yield ""
