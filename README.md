English | [繁體中文](README_tzh.md)

# chat-bridge

A RAG demo that turns market news into a searchable knowledge base, so users can ask questions in natural language and adjust their investment settings against metrics they define themselves. Work in progress.

## Run it with one command

Prerequisites:

- [uv](https://docs.astral.sh/uv/) (a Python project manager; see the next section if you don't have it)
- Node.js
- Your own logged-in Claude Code

From the repository root:

```
uv run chat-bridge
```

On the first run, uv creates `.venv` inside the repository and installs dependencies from `uv.lock`; if the Python version in `.python-version` is not on your machine, uv downloads it. Later runs start directly as long as the dependencies have not changed.

Current status: only the development environment is in place. `uv run chat-bridge --version` prints the version; without arguments it prints a one-line notice. There is no service to start yet.

### If you don't have uv

From the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/):

- Windows (PowerShell):

  ```
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

- macOS / Linux:

  ```
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Without uv (fallback)

Requires Python 3.11 or later. This path does not use `uv.lock`, so dependency versions may differ from the ones above.

- Windows:

  ```
  py -m venv .venv
  .venv\Scripts\activate
  py -m pip install -e .
  chat-bridge
  ```

- macOS / Linux:

  ```
  python3 -m venv .venv
  source .venv/bin/activate
  python3 -m pip install -e .
  chat-bridge
  ```

## Sample data

- `data/truth/`: events from June to November 2026 covering Taiwan and US equities, the Federal Reserve and the AI industry. One file per event; every item links to its source, and each file includes market moves before and after the event. Titles and Chinese-source items are in Traditional Chinese; items from English sources stay in English. The format is described in `docs/truth_format.md` (Traditional Chinese).

## Development

```
uv run pytest
```

Add a dependency with `uv add <package>`; it updates both `pyproject.toml` and `uv.lock`.
