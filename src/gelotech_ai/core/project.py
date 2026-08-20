"""Project discovery and safe text-file inspection helpers."""

from dataclasses import dataclass
from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "dist",
    "build",
}

MAX_FILES = 5000
MAX_PREVIEW_BYTES = 512 * 1024


@dataclass(frozen=True)
class ProjectFile:
    """A discovered file relative to the project root."""

    path: Path
    size: int


def discover_files(root: Path, *, limit: int = MAX_FILES) -> list[ProjectFile]:
    """Return readable project files while skipping generated/dependency trees."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Project path is not a directory: {root}")

    files: list[ProjectFile] = []
    for path in sorted(root.rglob("*"), key=lambda p: str(p).lower()):
        if len(files) >= limit:
            break
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        files.append(ProjectFile(path.relative_to(root), size))
    return files


def read_text_file(root: Path, relative_path: Path, *, max_bytes: int = MAX_PREVIEW_BYTES) -> str:
    """Read a UTF-8-ish text file for display/context without exceeding a size limit."""
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError("File is outside the opened project")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    if candidate.stat().st_size > max_bytes:
        raise ValueError(f"File is larger than the {max_bytes // 1024} KiB preview limit")

    data = candidate.read_bytes()
    if b"\x00" in data:
        raise ValueError("Binary files are not supported in the text preview")
    return data.decode("utf-8", errors="replace")
