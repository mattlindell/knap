# Obsidian Summarizer

NEVER use shell commands with quoted characters in flag names - this causes a permission prompt requiring human input that holds up the entire process.

NEVER use `cd` combined with any command. You are already in the project directory. Run all commands directly.

## Environment

- Python venv: `.venv/Scripts/python.exe` (Windows/MINGW64)
- Package manager: `uv` (not pip) — `uv sync`, `uv sync --group dev`
- Test runner: `.venv/Scripts/python.exe -m pytest tests/ -v`
- Dependencies in `pyproject.toml` — use `[dependency-groups]` not `[project.optional-dependencies]` for dev deps

## Architecture

Pipeline-based clipping processor:

- `config.py` + `config.yaml` — YAML config with deep merge defaults
- `extractors/` — URL classifier, video (yt-dlp), article (BeautifulSoup), quality gate
- `llm/` — Provider abstraction (Ollama, OpenAI-compatible) with factory pattern
- `templates/` — Jinja2 output templates (summary.md.j2, failed_extraction.md.j2)
- `clipping_watcher.py` — Watchdog-based file watcher orchestrating the pipeline
- `tests/` — pytest suite, all external calls mocked

## Agent skills

### Issue tracker

Issues are tracked in **Linear** via the Linear MCP — Photon Ventures team, "Tool Chest" project, every issue labeled `summarizer`. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical triage roles map 1:1 to the Photon Ventures "Agentic State Machine" labels (mutually exclusive). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
