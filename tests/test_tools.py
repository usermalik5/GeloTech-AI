from pathlib import Path

import pytest

from gelotech_ai.agent.tools import make_inspect_tool, make_read_tool, make_search_tool


def test_search_files_finds_content(tmp_path: Path) -> None:
    (tmp_path / "auth").mkdir()
    (tmp_path / "auth" / "login.py").write_text(
        "def handle_login(user):\n    return user\n", encoding="utf-8"
    )
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")

    result = make_search_tool(tmp_path).execute({"pattern": "handle_login"})

    assert "auth/login.py:1: def handle_login(user):" in result
    assert "main.py" not in result


def test_search_files_is_case_insensitive(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("USER = 'x'\n", encoding="utf-8")

    result = make_search_tool(tmp_path).execute({"pattern": "user"})

    assert "app.py:1: USER = 'x'" in result


def test_search_files_skips_binary_files(tmp_path: Path) -> None:
    (tmp_path / "bin.dat").write_bytes(b"\x00\x01\x02")
    (tmp_path / "ok.txt").write_text("alpha\n", encoding="utf-8")

    result = make_search_tool(tmp_path).execute({"pattern": "alpha"})

    assert "ok.txt:1: alpha" in result


def test_search_files_reports_invalid_regex(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")

    result = make_search_tool(tmp_path).execute({"pattern": "("})

    assert result.startswith("Tool error:")


def test_search_files_no_matches(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")

    result = make_search_tool(tmp_path).execute({"pattern": "zzz"})

    assert result == "No matches found."


def test_search_files_respects_result_limit(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("match\nmatch\nmatch\n", encoding="utf-8")

    result = make_search_tool(tmp_path).execute({"pattern": "match", "max_results": 2})

    assert result.count("a.txt:") == 2


def test_read_file_numbers_lines(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")

    result = make_read_tool(tmp_path).execute({"path": "a.txt"})

    assert "1: one" in result
    assert "2: two" in result
    assert "3: three" in result


def test_read_file_slices_lines(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("\n".join(f"line{i}" for i in range(10)), encoding="utf-8")

    result = make_read_tool(tmp_path).execute(
        {"path": "a.txt", "start_line": 3, "max_lines": 2}
    )

    assert "3: line2" in result
    assert "4: line3" in result
    assert "5: line4" not in result


def test_read_file_rejects_outside_project(tmp_path: Path) -> None:
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError):
        make_read_tool(tmp_path).execute({"path": f"../{outside.name}"})


def test_inspect_project_returns_inventory(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")

    result = make_inspect_tool(tmp_path).execute({})

    assert "Project files:" in result
    assert "README.md" in result


def test_inspect_project_caps_inventory(tmp_path: Path) -> None:
    for i in range(5):
        (tmp_path / f"f{i}.txt").write_text("x", encoding="utf-8")

    result = make_inspect_tool(tmp_path).execute({"max_files": 2})

    assert "- f0.txt" in result
    assert "- f1.txt" in result
    assert "capped at 2 files" in result