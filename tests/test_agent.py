import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from gelotech_ai.agent.agent import ReadOnlyAgent
from gelotech_ai.agent.tools import make_search_tool
from gelotech_ai.core.permissions import PermissionAction, PermissionDecision, PermissionPolicy
from gelotech_ai.models.base import AgentEvent, ToolCall


async def consume_agent(
    agent: ReadOnlyAgent, messages: list[dict[str, object]], used: list[str]
) -> str:
    parts: list[str] = []
    async for text in agent.run(messages, on_tool_call=used.append):
        parts.append(text)
    return "".join(parts)


class FakeProvider:
    """Scripted provider: first call returns a tool call, second returns text."""

    def __init__(self) -> None:
        self.calls = 0

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        yield ""

    async def stream_agent(
        self, messages: list[dict[str, object]], tools: list[dict[str, object]]
    ) -> AsyncIterator[AgentEvent]:
        self.calls += 1
        if self.calls == 1:
            yield AgentEvent(tool_calls=(ToolCall("search_files", {"pattern": "login"}),))
        else:
            yield AgentEvent(content="Found in auth/login.py")


def test_agent_runs_tool_then_answers(tmp_path: Path) -> None:
    (tmp_path / "auth").mkdir()
    (tmp_path / "auth" / "login.py").write_text(
        "def handle_login(user):\n    return user\n", encoding="utf-8"
    )
    provider = FakeProvider()
    agent = ReadOnlyAgent(provider, [make_search_tool(tmp_path)])
    messages: list[dict[str, object]] = [
        {"role": "user", "content": "Where is login handled?"}
    ]
    used: list[str] = []

    answer = asyncio.run(consume_agent(agent, messages, used))

    assert answer == "Found in auth/login.py"
    assert used == ["search_files"]
    assert messages[1]["role"] == "assistant"
    assert messages[1]["tool_calls"] == [
        {"function": {"name": "search_files", "arguments": {"pattern": "login"}}}
    ]
    tool_content = messages[2]["content"]
    assert isinstance(tool_content, str)
    assert "auth/login.py" in tool_content
    assert messages[3]["content"] == "Found in auth/login.py"


def test_agent_streams_multiple_tool_rounds(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("login = True\n", encoding="utf-8")
    agent = ReadOnlyAgent(ThreeRoundProvider(), [make_search_tool(tmp_path)])
    messages: list[dict[str, object]] = [{"role": "user", "content": "Find login."}]
    used: list[str] = []

    answer = asyncio.run(consume_agent(agent, messages, used))

    assert answer == "Final answer."
    assert used == ["search_files", "search_files"]
    assert len([m for m in messages if m["role"] == "tool"]) == 2


class ThreeRoundProvider(FakeProvider):
    async def stream_agent(
        self, messages: list[dict[str, object]], tools: list[dict[str, object]]
    ) -> AsyncIterator[AgentEvent]:
        if self.calls < 2:
            self.calls += 1
            yield AgentEvent(tool_calls=(ToolCall("search_files", {"pattern": "login"}),))
        else:
            self.calls += 1
            yield AgentEvent(content="Final answer.")


class LoopProvider:
    """Provider that always requests a tool, to exercise the round limit."""

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        yield ""

    async def stream_agent(
        self, messages: list[dict[str, object]], tools: list[dict[str, object]]
    ) -> AsyncIterator[AgentEvent]:
        yield AgentEvent(tool_calls=(ToolCall("search_files", {"pattern": "x"}),))


def test_agent_stops_at_round_limit(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    provider = LoopProvider()
    agent = ReadOnlyAgent(provider, [make_search_tool(tmp_path)], max_rounds=3)
    messages: list[dict[str, object]] = [{"role": "user", "content": "Go."}]
    used: list[str] = []

    asyncio.run(consume_agent(agent, messages, used))

    assert used == ["search_files"] * 3
    tool_messages = [m for m in messages if m["role"] == "tool"]
    assert len(tool_messages) == 4
    assert "limit reached" in tool_messages[-1]["content"]


class UnknownToolProvider(FakeProvider):
    async def stream_agent(
        self, messages: list[dict[str, object]], tools: list[dict[str, object]]
    ) -> AsyncIterator[AgentEvent]:
        self.calls += 1
        if self.calls == 1:
            yield AgentEvent(tool_calls=(ToolCall("does_not_exist", {}),))
        else:
            yield AgentEvent(content="I cannot do that.")


def test_agent_handles_unknown_tool(tmp_path: Path) -> None:
    agent = ReadOnlyAgent(UnknownToolProvider(), [make_search_tool(tmp_path)])
    messages: list[dict[str, object]] = [{"role": "user", "content": "Go."}]
    used: list[str] = []

    asyncio.run(consume_agent(agent, messages, used))

    tool_content = messages[2]["content"]
    assert isinstance(tool_content, str)
    assert "Unknown tool" in tool_content


def test_agent_denies_reads_when_policy_denies(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    policy = PermissionPolicy()
    policy.set(PermissionAction.READ_FILES, PermissionDecision.DENY)
    agent = ReadOnlyAgent(FakeProvider(), [make_search_tool(tmp_path)], policy=policy)
    messages: list[dict[str, object]] = [{"role": "user", "content": "Go."}]

    asyncio.run(consume_agent(agent, messages, []))

    tool_content = messages[2]["content"]
    assert isinstance(tool_content, str)
    assert "blocked" in tool_content


def test_agent_allows_reads_when_policy_allows(tmp_path: Path) -> None:
    (tmp_path / "auth").mkdir()
    (tmp_path / "auth" / "login.py").write_text(
        "def handle_login(user):\n    return user\n", encoding="utf-8"
    )
    policy = PermissionPolicy()
    policy.set(PermissionAction.READ_FILES, PermissionDecision.ALWAYS_ALLOW)
    agent = ReadOnlyAgent(FakeProvider(), [make_search_tool(tmp_path)], policy=policy)
    messages: list[dict[str, object]] = [{"role": "user", "content": "Go."}]
    used: list[str] = []

    asyncio.run(consume_agent(agent, messages, used))

    tool_content = messages[2]["content"]
    assert isinstance(tool_content, str)
    assert "auth/login.py" in tool_content