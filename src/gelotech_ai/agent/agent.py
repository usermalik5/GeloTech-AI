"""Read-only agent: an Ollama model driving read-only project tools."""

from collections.abc import AsyncIterator, Callable, Sequence

from gelotech_ai.agent.tools import AgentTool
from gelotech_ai.core.permissions import PermissionAction, PermissionDecision, PermissionPolicy
from gelotech_ai.models.base import ModelProvider, ToolCall


class ReadOnlyAgent:
    """Run a tool loop where the model may call read-only project tools.

    The model streams text; whenever it requests tool calls they are executed
    against the opened project and results are fed back. The loop ends when the
    model answers without requesting tools or the round limit is reached.
    """

    def __init__(
        self,
        provider: ModelProvider,
        tools: Sequence[AgentTool],
        *,
        policy: PermissionPolicy | None = None,
        max_rounds: int = 8,
    ) -> None:
        self.provider = provider
        self._tools = {tool.name: tool for tool in tools}
        self._schemas = [tool.schema for tool in tools]
        self._policy = policy
        self._max_rounds = max_rounds

    async def run(
        self,
        messages: list[dict[str, object]],
        *,
        on_tool_call: Callable[[str], None] | None = None,
    ) -> AsyncIterator[str]:
        """Stream the agent's final answer while executing any tool requests."""
        rounds = 0
        while rounds < self._max_rounds:
            content = ""
            calls: list[ToolCall] = []
            async for event in self.provider.stream_agent(messages, self._schemas):
                if event.content:
                    content += event.content
                    yield event.content
                if event.tool_calls:
                    calls = list(event.tool_calls)
            messages.append(self._assistant_message(content, calls))
            if not calls:
                return
            rounds += 1
            for call in calls:
                if on_tool_call is not None:
                    on_tool_call(call.name)
                messages.append({"role": "tool", "content": self._run_tool(call)})
        messages.append({"role": "tool", "content": "Tool round limit reached; stop here."})

    def _assistant_message(self, content: str, calls: list[ToolCall]) -> dict[str, object]:
        message: dict[str, object] = {"role": "assistant", "content": content}
        if calls:
            message["tool_calls"] = [
                {"function": {"name": call.name, "arguments": call.arguments}} for call in calls
            ]
        return message

    def _run_tool(self, call: ToolCall) -> str:
        tool = self._tools.get(call.name)
        if tool is None:
            return f"Unknown tool: {call.name}"
        if self._policy is not None and (
            self._policy.get(PermissionAction.READ_FILES) == PermissionDecision.DENY
        ):
            return "Tool blocked by permission policy: file reads are denied."
        try:
            return tool.execute(call.arguments)
        except (OSError, ValueError) as exc:
            return f"Tool error: {exc}"