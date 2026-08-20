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

### Model providers

Two providers are built in, switchable from the toolbar:

- **Ollama (local)** — free local models through `http://127.0.0.1:11434`.
- **Cloud API (OpenAI-compatible)** — works with DeepSeek, OpenRouter (including `:free` models), Groq, Together, and similar services. Enter the API key in the toolbar or set the `GELOTECH_API_KEY` environment variable, then adjust the base URL and model name as needed. DeepSeek's default base URL is `https://api.deepseek.com/v1` with models like `deepseek-chat`; OpenRouter uses `https://openrouter.ai/api/v1`.

Keys are never written to disk or logged. The application does not download models automatically; model selection stays explicit.

## Safety

Agent permissions are a core feature. Filesystem writes, command execution, Git operations, and other potentially destructive actions should be governed by explicit permission policies. Never commit API keys, passwords, tokens, or other credentials.

## Project status

**M2 implemented — read-only agent with `search_files`, `read_file`, and `inspect_project` tools.**

Next planned milestone: file editing behind the permission dialog system (`Allow Once` / `Always Allow` / `Deny`), then terminal and Git tools.

## License

License will be selected before the first stable release.
