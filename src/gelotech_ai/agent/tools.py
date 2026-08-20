"""Read-only agent tools operating on the opened project."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from gelotech_ai.core.context import build_project_context
from gelotech_ai.core.project import discover_files, read_text_file

SEARCH_LINE_LIMIT = 200


@dataclass(frozen=True)
class AgentTool:
    """A named, schema-described tool callable by the model."""

    name: str
    description: str
    parameters: dict[str, object]
    execute: Callable[[dict[str, object]], str]

    @property
    def schema(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def make_search_tool(root: Path) -> AgentTool:
    """Regex content search across discoverable text files."""

    def execute(args: dict[str, object]) -> str:
        pattern = str(args.get("pattern", "")).strip()
        max_results = int(args.get("max_results", 30))
        if not pattern:
            return "Tool error: 'pattern' is required."
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            return f"Tool error: invalid regular expression: {exc}"
        matches: list[str] = []
        for item in discover_files(root):
            if len(matches) >= max_results:
                break
            try:
                text = read_text_file(root, item.path)
            except (OSError, ValueError):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    snippet = line.strip()[:SEARCH_LINE_LIMIT]
                    matches.append(f"{item.path.as_posix()}:{lineno}: {snippet}")
                    if len(matches) >= max_results:
                        break
        if not matches:
            return "No matches found."
        return "\n".join(matches)

    return AgentTool(
        name="search_files",
        description=(
            "Search file contents in the opened project with a case-insensitive "
            "regular expression. Returns 'path:line: text' matches."
        ),
        parameters={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression to search for in file contents.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matches to return (default 30).",
                },
            },
            "required": ["pattern"],
        },
        execute=execute,
    )


def make_read_tool(root: Path) -> AgentTool:
    """Numbered line view of a text file inside the project."""

    def execute(args: dict[str, object]) -> str:
        rel = str(args.get("path", "")).strip()
        if not rel:
            return "Tool error: 'path' is required."
        try:
            start_line = int(args.get("start_line", 1))
            max_lines = int(args.get("max_lines", 200))
        except (TypeError, ValueError):
            return "Tool error: start_line and max_lines must be integers."
        if start_line < 1 or max_lines < 1:
            return "Tool error: start_line and max_lines must be positive."
        text = read_text_file(root, Path(rel))
        lines = text.splitlines()
        if start_line > len(lines):
            return f"File has {len(lines)} lines; start_line {start_line} is past the end."
        selected = lines[start_line - 1 : start_line - 1 + max_lines]
        numbered = [f"{start_line + i}: {line}" for i, line in enumerate(selected)]
        return f"{Path(rel).as_posix()} ({len(lines)} lines)\n" + "\n".join(numbered)

    return AgentTool(
        name="read_file",
        description=(
            "Read a text file from the opened project as numbered lines. "
            "Paths are relative to the project root."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the project root."},
                "start_line": {
                    "type": "integer",
                    "description": "First line to return, 1-based (default 1).",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to return (default 200).",
                },
            },
            "required": ["path"],
        },
        execute=execute,
    )


def make_inspect_tool(root: Path) -> AgentTool:
    """Compact inventory of the opened project."""

    def execute(args: dict[str, object]) -> str:
        max_files = int(args.get("max_files", 200))
        return build_project_context(root, max_files=max_files)

    return AgentTool(
        name="inspect_project",
        description="Return a compact inventory of files in the opened project.",
        parameters={
            "type": "object",
            "properties": {
                "max_files": {
                    "type": "integer",
                    "description": "Cap on the number of files listed (default 200).",
                },
            },
            "required": [],
        },
        execute=execute,
    )