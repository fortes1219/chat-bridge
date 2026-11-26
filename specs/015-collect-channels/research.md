# Research: Collect from the channels with the person's own agent

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Have the person's own Claude Code find the channels' new pages, from a script | Claude Code CLI (installed and logged in by the person) | the person's | proprietary, the person's own install | none added | `hoangsonww/AI-News-Briefing@be45130:briefing.sh:169` (the script starts the CLI it finds) | `hoangsonww/AI-News-Briefing@be45130:briefing.sh:169` (`"$binary" -p …`) |
| Have the person's own Codex do it, with live web search and nothing else | Codex CLI (`@openai/codex`, installed by the person) | 0.166.0 or later | Apache-2.0 | none added | `oEdyb/cron-agents@b006570:config.example.yaml:62-89` (MIT; the `codex-web` program a cron job runs) | `oEdyb/cron-agents@b006570:config.example.yaml:65`, `:68`, `:79`, `:82`, `:86` (`exec`, `--ignore-user-config`, `--sandbox`, `features.shell_tool=false`, `web_search="live"`) |
| Collect each page the agent names | trafilatura | 2.4.0 | Apache-2.0 | none added: feature 013 | `langroid/langroid@fc879d6:pyproject.toml:67` | `langroid/langroid@fc879d6:langroid/parsing/url_loader.py:312`, `:317` |

## Advisories

No package is added. trafilatura 2.4.0 and its dependencies were queried for feature 013 (none).

## Decisions

### 1. The agent finds, the command collects

- **Decision**: The agent returns the pages it found (address and channel id) in a JSON schema; each page must be on the site of the channel it is named for, and the command lists how many pages each channel had; the command collects each page with feature 013's page collecting.
- **Rationale**: Scripts that send a logged-in agent CLI to the web exist (AI-News-Briefing starts `claude -p` and `codex exec` from `briefing.sh`). Claude Code's web reading tool does not hand back the page: "For most pages, Claude doesn't see the full text. It asks a question about the page, and a separate model call reads the page and returns an answer", and "WebFetch reads the first 100,000 when Claude calls it" (code.claude.com/docs/en/tools-reference, read 2026-11-26). The knowledge base needs the page, so the agent names it and the command reads it.
- **Said plainly**: in the projects read, a collector takes its links from feeds, not from a model; an agent naming the pages is the less common way, chosen because the person asked the agent to do the crawling. Two checks stand between a named page and the knowledge base: its site is in the channel list, and the page can be read. Agents cite addresses that never existed ("3--13% of citation URLs are hallucinated", arXiv 2604.03173, *Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents*); such a page cannot be read, so it is named and nothing is written.

### 2. The channel list keeps the precedent's fields

- **Decision**: `id`, `name`, `url`, `enabled`, `topics` (free words), `note`. No `type` (every channel goes to the agent) and no `priority`.
- **Rationale**: tech-news-digest's `sources.json` keeps id, type, name, url, enabled, priority and topics per source (`config/defaults/sources.json:6-16`). The file is named for the person's word for them, channels: the news files already use `sources` for their citations.
- **The sample list**: 13 of the sites the sample news was collected from, each address answered on 2026-11-26. Left out because they refused the command's own requests that day: apnews.com and bls.gov (403), sec.gov (403; it asks for a User-Agent with contact details), wtop.com (closed the connection). A page there could not be collected, so asking the agent for them would only produce refusals.

### 3. Web search and web reading only, reading only on the channels' sites

- **Decision**: Claude Code gets `--tools "WebSearch,WebFetch"`, which limits the tools it has, and `--allowedTools` with `WebSearch`, and `WebFetch(domain:<site>)` and `WebFetch(domain:*.<site>)` for each channel, which lets those run without a prompt; the rest of its start is the chat's (no user settings, no MCP servers, no session saved). Codex gets `-c web_search="live"` instead of `"disabled"`, with its command, file and image tools off, in a read-only sandbox in an empty folder, as the chat starts it otherwise.
- **Rationale** (code.claude.com/docs, read 2026-11-26):
  - `--allowedTools` is "Tools that execute without prompting for permission … To restrict which tools are available, use `--tools` instead"; and "In a Manual mode `claude -p` run, a call that needs approval is denied unless something approves it", which is how `-p` runs start from v2.1.302 (cli-reference, headless).
  - `--restricted` removes "WebFetch, unless you name them individually in `--tools`"; the page does not say what it does to WebSearch, so the run as a person shows whether web search works under it.
  - "If Bash is allowed, Claude can still use `curl`, `wget`, or other tools to reach any URL" (permissions), so no other tool is given.
  - "`WebFetch(domain:example.com)` matches requests to `example.com` only. To also cover subdomains … add a `WebFetch(domain:*.example.com)` rule" (permissions); "WebSearch permission rules take no specifier" (tools-reference), so web search cannot be limited to sites.
  - `--bare` is not used: "bare mode doesn't use your subscription login" (headless).
  - Codex: `--search` is an option of the interactive program only (`openai/codex@af71942:codex-rs/tui/src/cli.rs:84-86`; not in `codex-rs/exec/src/cli.rs`); for `exec` the setting is `web_search`, "Use `"live"` for unrestricted live retrieval, or `"disabled"` to remove the tool" (learn.chatgpt.com/docs/config-file/config-reference); "Treat web results as untrusted" (agent-approvals-security). oEdyb/cron-agents starts Codex for its web step with these same options (`config.example.yaml:62-89`).
  - AI-News-Briefing's `--dangerously-skip-permissions` and `--full-auto` are not followed.

### 3a. A risk the run as a person settles

- Reported from tools-reference by a lookup, not reopened here: with a claude.ai login, web reading in `-p` goes through a built-in subagent ("in the system/init event, agents lists web-fetch and tools doesn't list WebFetch"). Whether that path works when `--tools` names only WebSearch and WebFetch is not written. If web reading does not work and web search does, web search alone returns titles and addresses, which may be enough to name the pages (an inference). T007 shows which.

Settled by the run (Runs below): with `--restricted` and `--tools "WebSearch,WebFetch"`, the person's Claude Code searched and named real pages.

### 4. Pages off the channels' sites are refused

- **Decision**: A page whose host is not the site, or a subdomain of the site, of the channel it is named for is refused and named; so is a page that names no listed channel. With no channel enabled, the agent is not asked.
- **Rationale**: A value outside the list is refused, not used (the project's code rules). Web search cannot be limited to sites, and agents cite addresses they made up (3 to 13 percent, arXiv 2604.03173).

### 5. The start date is the knowledge base's latest event date

- **Decision**: The agent is asked for pages published on or after the knowledge base's latest event date; with no dated document, for the latest pages.
- **Rationale**: News collectors take the date range as a parameter: gnews (`ranahaani/GNews@3f28824:gnews/gnews.py:40-41`, "Date after which results must have been published" at `:56`), newspaper4k's `GoogleNewsSource` (`AndyTheFactory/newspaper4k@22a4be5:newspaper/google_news.py:78-79`), gdeltdoc's `Filters` (`alex9smith/gdelt-doc-api@4122016:gdeltdoc/filters.py:95-96`), all MIT. Taking the start from the knowledge base's latest date has no precedent: it is this project's own step, so a run picks up where the knowledge base ends. On or after, so a later article of the same day is found; a page collected again unchanged is left as it was.

### 6. Web collecting ends in the knowledge base; news files do not

- **Decision**: Collecting from the channels or from web addresses ingests the folder it collected into; writing the market moves of news files ingests nothing.
- **Rationale**: The person runs one command to reach the knowledge base when collecting from the web. The news files are the person's own files, which they ingest themselves.

### 7. The limit

- **Decision**: The agent run has the time limit the chat already gives a program's answer; past it, or with an answer not in the schema, nothing is collected and the command says so.
- **Rationale**: The run is bounded without a new number; whether it is enough for the sample's channels is measured in the run as a person.

## Runs

### The smallest real run (2026-11-26, with the maintainer's consent to one page and one ingest)

One channel (the Federal Reserve's press releases), the first page the agent named, collected and
ingested once into a separate local data folder, then one search; the maintainer's knowledge base
was not touched. The steps were called from a script so that only one page was collected; they are
the functions `collect` runs.

- 15:18:25, Claude Code asked for the channel's pages on or after 2026-11-24; 15:18:57, it named 3 pages, all on the channel's site and all real (`bcreg20261125b.htm`, `bcreg20261125a.htm`, `monetary20261124a.htm`), none refused. 32 seconds.
- 15:19:02, the first page collected; 15:19:19, ingested (1 written, 0 rejected).
- The search "Federal Reserve announcement" found it first, dated 2026-11-25 from the page itself.
- Not run: `uv run chat-bridge collect` itself (the script called its functions, so the command's own steps, and the start date read from the knowledge base, were not run for real; stand-in tests hold them); all 13 channels at once; Codex. The command for them is the person's own run.
- Not shown by the log: whether the agent used web reading as well as web search.
