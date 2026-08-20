from pathlib import Path

import pytest

from gelotech_ai.core.context import build_project_context
from gelotech_ai.core.project import discover_files, read_text_file


def test_discover_files_skips_generated_directories(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / ".venv" / "secret.py").write_text("ignored", encoding="utf-8")

    files = discover_files(tmp_path)

    assert [item.path.as_posix() for item in files] == ["src/app.py"]


def test_read_text_file_rejects_paths_outside_project(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError):
        read_text_file(tmp_path, Path("..") / outside.name)


def test_project_context_contains_inventory(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")

    context = build_project_context(tmp_path)

    assert "Project files:" in context
    assert "README.md" in context
