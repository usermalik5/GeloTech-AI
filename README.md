# GeloTech AI

A Windows-first Python desktop AI coding assistant inspired by the agent workflow of tools like OpenCode.

## Current milestone: M1 — Local Project + AI Chat

The first usable workspace is now implemented:

- Open a local project directory
- Browse its files from a native Qt tree
- Preview UTF-8 text files safely
- Skip common generated/dependency directories
- Build a compact project file inventory for model context
- Detect locally installed Ollama models
- Stream responses from Ollama without freezing the GUI
- Keep multi-turn chat history
- Run without a cloud API key when using Ollama locally

No file writes, terminal execution, or Git mutations are enabled yet. Those will be introduced behind the permission system in later milestones.

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

### Ollama

Install and start Ollama on Windows, then install at least one local model. GeloTech AI checks `http://127.0.0.1:11434` for installed models and streams chat through Ollama's local API.

The application does not download models automatically. This keeps model selection explicit and avoids unexpected multi-gigabyte downloads.

## Safety

Agent permissions are a core feature. Filesystem writes, command execution, Git operations, and other potentially destructive actions should be governed by explicit permission policies. Never commit API keys, passwords, tokens, or other credentials.

## Project status

**M1 implemented — local project browser + Ollama streaming chat.**

Next planned milestone: file search, targeted file-context loading, and the first read-only agent tools.

## License

License will be selected before the first stable release.
