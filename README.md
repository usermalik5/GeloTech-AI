# GeloTech AI

A Windows-first Python desktop AI coding assistant inspired by the agent workflow of tools like OpenCode.

## Vision

GeloTech AI is intended to be a practical, local/free-first coding workspace where an AI can understand a project, inspect files, make controlled edits, run commands, and work with Git from a native desktop GUI.

## Goals

- Professional Windows desktop GUI with PySide6
- Local/free-first AI through Ollama
- Pluggable OpenAI-compatible model providers
- Project-aware coding agent
- File inspection, search, and editing tools
- Terminal and Git integration
- Explicit persistent permissions for agent actions
- Streaming model responses
- Context management and project indexing
- Windows packaging and installer

## Architecture

```text
GeloTech AI Desktop
        |
        v
     PySide6 GUI
        |
        v
     Agent Engine
        |
   +----+-------------------------+
   |    |       |       |         |
 Files Search Terminal Git   Permissions
   |                              |
   +--------------+---------------+
                  |
                  v
          Model Provider Layer
                  |
        +---------+----------+
        |         |          |
      Ollama  OpenAI-compat  Future
```

The GUI, agent engine, tools, and model adapters are intentionally separated so each layer can be tested independently.

## Development

Python 3.11+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m gelotech_ai
```

## Safety

Agent permissions are a core feature. Filesystem writes, command execution, Git operations, and other potentially destructive actions should be governed by explicit permission policies. Never commit API keys, passwords, tokens, or other credentials.

## Project status

**Early development / architecture stage.**

## License

License will be selected before the first stable release.
