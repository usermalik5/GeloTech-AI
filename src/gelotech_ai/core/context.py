"""Small, deterministic project context builder for the first chat milestone."""

from pathlib import Path

from gelotech_ai.core.project import discover_files


def build_project_context(root: Path, *, max_files: int = 200) -> str:
    """Build a compact file inventory suitable for a model system message."""
    files = discover_files(root, limit=max_files)
    lines = [f"Project root: {root}", "Project files:"]
    lines.extend(f"- {item.path.as_posix()} ({item.size} bytes)" for item in files)
    if len(files) == max_files:
        lines.append(f"- ...inventory capped at {max_files} files")
    return "\n".join(lines)
