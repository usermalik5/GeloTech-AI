"""Qt worker threads for network operations so the UI stays responsive."""

import asyncio

from PySide6.QtCore import QThread, Signal

from gelotech_ai.agent.agent import ReadOnlyAgent
from gelotech_ai.models.base import ModelProvider


class OllamaModelsWorker(QThread):
    """Discover model names from a provider."""

    models_ready = Signal(list)
    error = Signal(str)

    def __init__(self, provider: ModelProvider) -> None:
        super().__init__()
        self.provider = provider

    def run(self) -> None:
        try:
            models = asyncio.run(self.provider.list_models())
            self.models_ready.emit(models)
        except Exception as exc:  # noqa: BLE001  # UI boundary: convert provider failures to text.
            self.error.emit(str(exc))


class OllamaChatWorker(QThread):
    """Stream one chat response from a provider."""

    chunk = Signal(str)
    finished_ok = Signal()
    error = Signal(str)

    def __init__(self, provider: ModelProvider, messages: list[dict[str, str]]) -> None:
        super().__init__()
        self.provider = provider
        self.messages = messages

    def run(self) -> None:
        async def consume() -> None:
            async for text in self.provider.stream(self.messages):
                self.chunk.emit(text)

        try:
            asyncio.run(consume())
            self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001  # UI boundary: convert provider failures to text.
            self.error.emit(str(exc))


class AgentChatWorker(QThread):
    """Run the read-only agent loop in a worker thread."""

    chunk = Signal(str)
    tool_used = Signal(str)
    finished_ok = Signal()
    error = Signal(str)

    def __init__(self, agent: ReadOnlyAgent, messages: list[dict[str, object]]) -> None:
        super().__init__()
        self.agent = agent
        self.messages = messages

    def run(self) -> None:
        async def consume() -> None:
            async for text in self.agent.run(self.messages, on_tool_call=self.tool_used.emit):
                self.chunk.emit(text)

        try:
            asyncio.run(consume())
            self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001  # UI boundary: convert agent failures to text.
            self.error.emit(str(exc))
