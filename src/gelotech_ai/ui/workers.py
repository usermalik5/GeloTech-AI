"""Qt worker threads for network operations so the UI stays responsive."""

import asyncio

from PySide6.QtCore import QThread, Signal

from gelotech_ai.models.ollama import OllamaProvider


class OllamaModelsWorker(QThread):
    """Discover local Ollama models."""

    models_ready = Signal(list)
    error = Signal(str)

    def __init__(self, provider: OllamaProvider) -> None:
        super().__init__()
        self.provider = provider

    def run(self) -> None:
        try:
            models = asyncio.run(self.provider.list_models())
            self.models_ready.emit(models)
        except Exception as exc:  # UI boundary: convert provider failures to text.
            self.error.emit(str(exc))


class OllamaChatWorker(QThread):
    """Stream one chat response from Ollama."""

    chunk = Signal(str)
    finished_ok = Signal()
    error = Signal(str)

    def __init__(self, provider: OllamaProvider, messages: list[dict[str, str]]) -> None:
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
        except Exception as exc:  # UI boundary: convert provider failures to text.
            self.error.emit(str(exc))
