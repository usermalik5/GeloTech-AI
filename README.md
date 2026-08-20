# GeloTech AI

A Windows-first Python desktop AI coding assistant inspired by the agent workflow of tools like OpenCode.

## Current milestone: M2 — Read-only Agent

The chat is now a project-aware agent. When a project is open, the local model
can call read-only tools before answering:

- `search_files` — case-insensitive regex search across project file contents
- `read_file` — numbered line view of any text file inside the project
- `inspect_project` — compact file inventory for model context
- Tool requests are executed against the opened project in a worker thread so the GUI stays responsive
- Results are fed back to the model until it answers or the round limit is hit
- Tool usage appears inline in the chat
- M1 features remain: project browser, safe file previews, and plain streaming chat when no project is open

Everything stays **read-only**: no file writes, terminal execution, or Git mutations yet. Those arrive in M3 behind explicit permission dialogs.

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

**M2 implemented — read-only agent with `search_files`, `read_file`, and `inspect_project` tools.**

Next planned milestone: file editing behind the permission dialog system (`Allow Once` / `Always Allow` / `Deny`), then terminal and Git tools.

## License

License will be selected before the first stable release.
