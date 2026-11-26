English | [繁體中文](README_tzh.md)

# chat-bridge

![Which market news matters to my holdings? Portfolio research with sources and allocation previews.](docs/readme-cover.png)

[View the presentation in English](https://chat-bridge.akasa-lab.dev/en/)

Which market news matters to the stocks I hold? chat-bridge is a local RAG demo for researching
Taiwan and US equities. Ask in English or Traditional Chinese and follow the citations back to
market news and other documents. If you ask for a change to your allocation, you can compare
the proposed weights and rule checks before deciding whether to accept it.

## Quick start

Clone the repository with Git or download it as a ZIP. Install [Node.js](https://nodejs.org/en/download)
and [uv](https://docs.astral.sh/uv/getting-started/installation/). Use a current Node.js LTS release.
The minimum versions for the 22, 24 and 26 release lines are 22.23.5, 24.22.3 and 26.13.1 respectively.
uv downloads the Python version pinned in `.python-version` when needed.

Install and sign in to **one** of these chat backends with your own account.

| Chat backend | Sign-in command | Installation guide |
| --- | --- | --- |
| Claude Code | `claude auth login` | [Claude Code setup](https://code.claude.com/docs/en/setup) |
| Codex | `codex login` | [Codex CLI setup](https://github.com/openai/codex) |

Open a new terminal after installation so it can find the new commands. From the repository root, run:

```sh
uv run chat-bridge
```

The app builds the web interface, indexes the bundled news if the knowledge base is empty, and opens
[the chat page](http://127.0.0.1:8000). Allow several minutes and a few gigabytes for the first run.
The locked Python dependencies take about 1.2 GB, mostly CPU-only PyTorch, and the embedding model
adds about 2.3 GB. Later runs reuse the installed dependencies and index.

Press Ctrl+C to stop the service. Use `--no-browser` to start it without opening a tab, or
`uv run chat-bridge --help` to see other commands. If chat-bridge is already running, the command
reopens the existing page. If another program is using port 8000, the startup message identifies
the conflict.

## Try the research flow

1. **Ask about the market.** Pick a sample question or ask how Fed policy has affected Taiwan
   equities. Open the source list to see what the app retrieved, then follow the numbered
   citations in the answer.
2. **Set up a portfolio.** Start with the simulated holdings or choose **Edit holdings** to change
   the quantities, average costs and cash. Set rules such as a maximum weight for one holding or market.
3. **Review an allocation change.** Ask the chat to revise your strategy. The proposal shows the
   current and suggested target weights, the difference for each position, and which rules pass
   before and after. Accepting updates the target weights. Rejecting closes the proposal.
   The app does not place trades.

Both the interface and the chat support Traditional Chinese and English. The interface starts in
the browser's language and has a language switch. This demo is for research and does not provide
investment advice.

### Portfolio details

- Use Yahoo Finance symbols such as `2330.TW`, `6488.TWO`, `AAPL` and `BRK-B`. The portfolio
  supports up to 30 Taiwan and US holdings plus cash. When a question mentions "my holdings"
  without naming any, chat searches for up to eight individually.
- A new holding starts at a 0% target weight. Removing a holding also removes its target. If the
  targets no longer add up to 100%, the panel flags it. Ask the chat for a revision and accept
  the proposal to set new targets.
- The panel uses the latest available prices to value holdings. Saving edited holdings replaces
  the stored quantities and costs.

## How retrieval works

1. **Index documents.** The app stores passages in embedded PostgreSQL with pgvector. It keeps
   heading paths so a citation can point to the relevant passage. PDFs use page labels and the
   text already in the file. Scanned PDFs need OCR before import. Long passages are split at
   natural breaks using the embedding model's 512-token limit. Markdown tables stay whole.
2. **Find related passages.** Hybrid search combines jieba keyword search and local bge-m3
   embeddings with Reciprocal Rank Fusion. Chinese and English queries can retrieve passages in
   either language. The synonym list expands names such as 費半 to 費城半導體指數 and SOX. Markdown
   tables are indexed separately for keyword search and ranked below matching prose.
3. **Cover each part of the question.** Chat keeps the original question's top eight results,
   runs a broader search over the text, then searches separately for up to eight validated
   subquestions. It removes duplicates and adds market tables from the matched files. If query
   splitting fails or times out after 120 seconds, chat uses the results from the original query.
4. **Answer from the results.** The answering program gets retrieved passages and their metadata.
   The app attaches the source list, the knowledge base's latest event date and the investment
   disclaimer. If retrieval finds nothing, the app reports the gap without calling the answering
   program.

On 20 sample questions with manually specified subquestions, this retrieval pass found **59 of
63 expected files**, up from **45 of 63** with the original top-eight search. It kept every file
the baseline found. The added context increased response time in the recorded runs, and chat
still missed some topics in one language or the other. [Retrieval evaluation and timings](specs/007-search-each-part/research.md)

### Chat API

Try the endpoints in the [local API docs](http://127.0.0.1:8000/docs).

| Endpoint | What it returns |
| --- | --- |
| `GET /chat/programs` | Installation and sign-in status for each backend, without starting a model |
| `POST /chat/stream` | Server-Sent Events for the question and any allocation proposal |
| `GET /chat/records` | Recent questions and their retrieval results. Add `?unanswered=true` to find queries that retrieved nothing |

Post JSON such as `{"question": "Did the Fed raise rates?"}`. Optionally set `program` to
`claude-code` or `codex`. By default, the app uses Claude Code when signed in, then Codex.
When you select a backend explicitly, it must be signed in.

The first payload, `response.context`, carries the sources, latest indexed event date, backend
name, `split_failed` flag and bilingual disclaimer. Answer text arrives in
`response.output_text.delta`, incrementally for ordinary Claude Code replies and in a single
payload for Codex or a combined answer and proposal. Allocation requests can also emit
`response.proposal`. A failure during streaming emits an `error` event. A retrieval setup
failure returns HTTP 503 before streaming starts. Market quote updates use a separate Socket.IO
connection. [Frontend chat contract](frontend/src/service/contract/chat.ts)

### Local use and model permissions

The service binds to loopback and accepts only local host names. It is intended for one user
on a trusted computer. The embedded PostgreSQL instance has no password, and on Windows other
processes on the same computer can connect to it while it is running.

Questions and passages reach the answering program through standard input as data. Claude Code
runs with its tools disabled. Codex runs in an empty working directory in a read-only sandbox,
with command, file and web tools disabled. Its patch tool is present but cannot write in that
sandbox. chat-bridge uses the sign-in saved by the selected CLI and strips API key environment
variables before launching it. The app inserts the sources and disclaimer itself.

Three recorded trials on Codex 0.166.0 covered a malicious chat message, an instruction hidden
in a document to change the answer, and a document instruction to read a local file. The replies
kept their citations and disclaimer, and the local file content was absent. Each case was run
once. Prompt injection can still affect generated text. [Runner flags and trial results](specs/004-answer-with-codex/research.md)

## Import and search documents

```sh
uv run chat-bridge ingest data/documents
uv run chat-bridge search "台積電 法說會"
uv run chat-bridge search "Did the Fed raise rates?" --limit 5
```

- `ingest` scans folders recursively for `.docx`, `.doc`, `.pdf`, `.txt` and `.md` files. It
  skips unchanged files and reports unreadable ones while importing the rest. It uses pypdf for
  PDF, office-oxide for `.doc` and MarkItDown for `.docx`. Convert `.odt` to DOCX or PDF, and save
  text files as UTF-8. [Sample documents and permissions](docs/sample_documents.md)
  · [PDF extraction notes](specs/005-long-documents/research.md)
- `search` returns five results by default, with file, event date, heading, snippet and keyword
  and vector ranks. `--as-of 2026-07-31` filters whole files by their Markdown `event_date`.
  It excludes undated files and can still include later developments written into an earlier
  event's file.
- After editing `data/synonyms.txt`, run `ingest` to rebuild the keyword index. Existing vectors
  are reused. The database, dictionary and model are stored under the Git-ignored `local_data/`
  directory. Use `CHAT_BRIDGE_LOCAL_DATA` to choose a different location.
- For scripts, exit code `0` means success, `1` means a file could not be imported or
  search returned no matches, and `2` means an error.

### Use only your own documents

```sh
uv run chat-bridge ingest path/to/your-folder --replace
```

Plain `ingest` adds the folder to the existing knowledge base. With `--replace`, the app removes
stored documents outside the selected folder, including the sample news, and lists what it
removed. If none of the files can be read, it preserves the existing index. Rerun the command
after adding, editing or deleting files. The bundled questions disappear when the sample news is
removed. Reimport it with `uv run chat-bridge ingest data/truth`.

## Add more market events

```sh
uv run chat-bridge collect
uv run chat-bridge truth
uv run chat-bridge ingest data/truth
```

1. **Collect sources.** `collect` uses your signed-in CLI to find events from
   `data/channels.json`, starting at the latest bundled event date. Use `--until 2026-11-25`
   to cap the date or pass article and feed URLs directly. The app fetches approved pages and
   stores one folder per event in `local_data/collected/`. It honors robots.txt, verifies TLS,
   blocks local and private addresses, and limits downloads to 20 MB. Download PDF files separately
   and use `ingest` on them.
2. **Write event records.** `truth` turns collected pages into sourced Markdown records in
   `data/truth`. It checks source excerpts, language, approved vocabulary and numeric notation.
   It retries a rejected draft once and keeps events that still fail for a later run.
   `--limit 3` processes three events, and `--workers 2` reduces the default concurrency from
   five to two. `--into` changes where records are written. Successful events are removed from
   the collection queue even when you write to a custom folder. To regenerate them in the default
   folder, collect them again.
3. **Index the records.** `ingest` makes the new events available to chat. Collection and writing
   use your CLI account's allowance. Review the source terms before reusing collected material.

[Event format and collection targets](docs/truth_format.md) · [Exposure vocabulary](docs/exposure_vocabulary.md)

To refresh only the market-moves section of an existing record, pass the file or directory to
`collect`:

```sh
uv run chat-bridge collect data/truth/2026-11-17-taiex-falls-947-points.md
```

Day 0 is the first trading session that closes at or after the event's `event_time`. Records
without that field use their event date. The app uses Yahoo Finance daily closes and fills
missing Taiwan closes from FinMind when available. Missing data stays marked as missing.
Reimport the updated files when you want chat to use them.

## Market data and attribution

The strategy panel gets quotes from Yahoo Finance through yfinance and links to Yahoo's terms.
For Taiwan previous closes and ex-dividend reference prices, it also uses the
[FinMind public API](https://finmind.github.io/en/PrivacyPolicy/) and exchange open data.

> Taiwan Stock Exchange 2026 TWSE OpenAPI 1.0: STOCK_DAY_ALL (daily trading of listed stocks),
> TWT48U_ALL (ex-dividend and ex-rights notices of listed stocks)
>
> Taipei Exchange 2026 TPEx OpenAPI 1.0.0: tpex_mainboard_daily_close_quotes (OTC stock quotes),
> tpex_exright_prepost (ex-dividend and ex-rights notices of OTC stocks)
>
> The Open Data is made available to the public under the Open Government Data License, User can
> make use of it when complying to the condition and obligation of its terms.
>
> Open Government Data License: https://data.gov.tw/license

The bundled news covers Taiwan and US equities, the Federal Reserve and the AI industry from June
to November 2026. Each event file links to its sources and includes market moves around the event.
The repository also provides the bilingual sample questions, aliases and market series. [Event format](docs/truth_format.md)

## Development

```sh
uv run pytest
uv run ruff check chat_bridge tests
uv run ruff format --check chat_bridge tests
uv run mypy chat_bridge tests
```

The default test run needs neither the model nor the database. Run the integration suite with
`uv run pytest -m slow`, or run it in a Linux container:

```sh
docker compose -f compose.test.yml run --rm slow-tests
```

The slow suite loads the embedding model, starts PostgreSQL and indexes the sample news. It
includes a 41-question retrieval regression check. It uses a separate data directory and can
reuse an existing model cache via `HF_HUB_CACHE`. The container builds pgvector for portable
x86-64 use, mounts the test inputs read-only and caches dependencies and the model in Docker
volumes. [Retrieval regression baseline](tests/data/search_yield.yaml)

### Run without uv

Python 3.11.5 or later is required for this fallback. pip resolves the dependencies independently
of `uv.lock` and may download a larger PyTorch build on Linux.

- Windows (PowerShell)

  ```powershell
  py -m venv .venv
  .venv\Scripts\Activate.ps1
  py -m pip install -e .
  chat-bridge
  ```

- macOS or Linux

  ```sh
  python3 -m venv .venv
  source .venv/bin/activate
  python3 -m pip install -e .
  chat-bridge
  ```
