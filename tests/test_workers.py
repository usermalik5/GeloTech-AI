from __future__ import annotations

from gelotech_ai.ui import workers


def test_chat_worker_module_exposes_expected_worker_types() -> None:
    assert workers.OllamaChatWorker is not None
    assert workers.AgentChatWorker is not None
    assert workers.OllamaModelsWorker is not None
