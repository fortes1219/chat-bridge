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

On the first run, uv creates `.venv` inside the repository and installs dependencies from `uv.lock`; if the Python version in `.python-version` is not on your machine, uv downloads it. The dependencies take about 1.2 GB, most of it the CPU-only build of PyTorch. Later runs start directly as long as the dependencies have not changed.

Current status: you can ingest documents and search them from the command line (see the next section). Without arguments, `uv run chat-bridge` lists its commands. The chat page is not built yet.

## Ingest documents and search them

```
uv run chat-bridge ingest data/truth
uv run chat-bridge search "台積電 法說會"
uv run chat-bridge search "Did the Fed raise rates?"
```

- `ingest <folder>` reads every `.docx`, `.pdf`, `.txt`, and `.md` file in the folder and its subfolders. It converts each file to Markdown, splits it at the headings, and stores the sections in an embedded PostgreSQL database. A file that has not changed since the last run is skipped.
- A file that cannot be read is listed with the reason, and the other files are still stored. This covers unsupported file types, text files that are not UTF-8, and PDFs without a text layer. No OCR is done.
- `search <question>` lists the sections that match best, each with its file, heading path, and a snippet. Use `--limit` to change how many are listed (the default is 5). When no section matches, the command says that the data has none.
- Search is hybrid, in Traditional Chinese or English. Keyword search uses the jieba tokenizer. Vector search uses the [bge-m3](https://huggingface.co/BAAI/bge-m3) embedding model, which runs on your CPU, so a question in English also finds sections in Chinese, and the other way round. The two rankings are merged with Reciprocal Rank Fusion. Each result shows the merged score and where each method ranked it (`-` when that method did not find it).
- A Markdown table, including one converted from Word or PDF, is searched apart from the text around it. It ranks below text in keyword search and is left out of vector search, so a name that every table lists does not crowd out the text about it. A word that only a table holds is still found.
- A question also searches for the synonyms of its names, from `data/synonyms.txt` (for example 費半 also searches for 費城半導體指數 and SOX). After you edit that file, run `ingest` again; it rebuilds the keyword index and keeps the vectors.
- Each `search` command takes about 15 seconds, most of it starting Python and loading the model.
- The first run downloads jieba's Traditional Chinese dictionary (8.6 MB) and the bge-m3 model (about 2.3 GB). The database, the dictionary and the model are kept in `local_data/`, which git ignores. To start over, delete that folder. To use another folder, set `CHAT_BRIDGE_LOCAL_DATA`.
- Exit codes: `0` when everything succeeded, `1` when `ingest` rejected a file or `search` found nothing, and `2` on an error.

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

Requires Python 3.11 or later. This path does not use `uv.lock`, so dependency versions may differ from the ones above. pip also installs the default PyTorch build, which on Linux includes CUDA and is several gigabytes larger.

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
- `data/synonyms.txt`: names that mean the same thing, one group per line, in the Solr synonyms format. The comments at the top list what is left out on purpose and why.

## Development

```
uv run pytest
uv run pytest -m slow
uv run ruff check chat_bridge tests
uv run ruff format --check chat_bridge tests
uv run mypy chat_bridge tests
```

- `uv run pytest` runs the tests that need neither the embedding model nor the database. They take seconds.
- `uv run pytest -m slow` runs the tests marked slow. They load the model, start the embedded database, and ingest `data/truth`, which takes several minutes. One of them searches 41 questions and fails if the results get worse than the measured baseline in `tests/data/search_yield.yaml`.
- Tests never use the project's `local_data/`: each run gets a data folder of its own. The model is the one exception. If `local_data/models` already holds it, the tests read it from there, through huggingface_hub's `HF_HUB_CACHE` setting, instead of downloading 2.3 GB again. Set `HF_HUB_CACHE` yourself to keep the model somewhere else; the app reads the same setting.

The lint, format, and type-check settings follow the FastAPI repository. Add a dependency with `uv add <package>`; it updates both `pyproject.toml` and `uv.lock`.
