# Research: Asking about your own documents

Sources were opened on 2026-11-25. A citation `owner/repo@commit:path:line` points at the file as it
was at that commit. An installed package is cited by its version and its path in the package.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Remove, in the ingest's transaction, every stored document that is not in the folder (decision 1) | SQLAlchemy | 2.1.9 | MIT | none added: already a dependency | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/pyproject.toml:13` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/postgres_models.py:4`, `:54` |
| Read the sample questions file and refuse one that is not the shape (decision 2) | pydantic | 2.14.3 | MIT | none added: already a dependency | `fastapi/full-stack-fastapi-template@77e550a:backend/pyproject.toml:10` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/api_models.py:5`, `:93-97` |
| The sample questions' schema in the page's contract, checked when they arrive | zod | 4.6.7 | MIT | none added: already a dependency | `middleapi/orpc@26175d2:playgrounds/contract-first/package.json:23` | `middleapi/orpc@26175d2:playgrounds/contract-first/src/contract/sse.ts:2`, `:11` |
| Ask the service for the sample questions once the page opens | @tanstack/vue-query | 5.108 | MIT | none added: already a dependency | `middleapi/orpc@26175d2:playgrounds/nuxt/package.json:19` | `middleapi/orpc@26175d2:playgrounds/nuxt/app/plugins/vue-query.ts:10-23`; `app/components/orpc-stream.vue:2`, `:6` |

No package is added.

## Advisories

No package or runtime is added or changed, so there is nothing new to check. The lock files are
sent to OSV and `npm audit` again before this feature is delivered, as for every delivery.

## Decisions

### 1. `ingest <folder> --replace` keeps only the folder's documents

**Decision**: `ingest` keeps doing what it does: it adds and updates the folder's documents and
removes nothing else. With `--replace`, every stored document that is not one of the folder's
readable documents is removed as well, in the same transaction as the folder's documents are
written. A run with `--replace` on a folder in which nothing can be read removes nothing and fails.

**Rationale**:
- LangChain's indexing API has the same two modes: by default it deletes nothing, and with
  `cleanup="full"` it deletes "all documents that have not been returned by the loader during this
  run of indexing" (langchain-core 1.8.4, installed here as a dependency of langchain-text-splitters,
  `langchain_core/indexing/api.py:302`, `:353-363`; the deletion is `:583-595`). The option is
  chosen by the caller, so loading a second source does not wipe the first.
- The same documentation warns that in full mode "the loader should be returning the entire
  dataset, and not just a subset of the dataset. Otherwise, the auto_cleanup will remove documents
  that it is not supposed to" (`api.py:325-330`). A folder in which nothing can be read is the
  extreme of that: a wrong path, or files of a kind the command does not read. Removing everything
  then would leave an empty knowledge base, which the service fills with the sample news again at
  its next start; so nothing is removed and the person is told.
- The knowledge base keeps one row per document and its sections and search entries hang off it
  with `ON DELETE CASCADE` (`chat_bridge/ingest/models.py:83`, `:114`), so removing a document is one
  `DELETE` on the documents, as the ingest already does for a file that can no longer be read.
  A question record and a proposal keep copies of their sources, so they are not touched.

**Alternatives considered**:
- Replacing by default: the README ingests two folders of samples one after the other
  (`data/truth` and `data/documents`); the second would remove the first.
- A separate command that empties the knowledge base: two commands for one wish, and between them
  the knowledge base is empty.
- Removing only documents that came from the same folder before: the knowledge base stores each
  path relative to the folder it was ingested from, not the folder itself; keeping the folder is a
  change to the stored data without a precedent found.

### 2. The sample questions come with the sample news

**Decision**: the four sample questions move out of the page's texts into
`data/sample_questions.json`, each in Traditional Chinese and English. The service reads and checks
the file the first time the page asks for the questions and keeps it; a broken file makes that
request fail, and the page then shows no questions, as it does without the sample news.
`GET /chat/samples` sends them while the knowledge base holds any of the
sample news files (by their stored path), and an empty list otherwise. The page shows what it is
sent, and nothing when it is sent nothing.

**Rationale**:
- open-webui keeps its prompt suggestions, with their translations, in the server's configuration
  (`open-webui/open-webui@0666e59d26a4:backend/open_webui/config.py:1706`, `:3265-3266`) and sends
  them to the page from its config endpoint (`backend/open_webui/main.py:2307`, `:2538-2539`), so a
  deployment shows suggestions that fit what it serves.
- Here what the questions fit is the sample news. Only the service knows whether the knowledge base
  still holds it; checking a handful of paths is one indexed query.

**Alternatives considered**:
- Questions made from the stored documents' titles: no precedent found.
- Questions written by the answering program from the documents: a model call on every page load,
  on the person's plan.
- Keeping the questions in the page: the page cannot know what the knowledge base holds.

### 3. The instructions describe documents, not market news

**Decision**: the first lines of `answer_prompt.md`, `split_prompt.md` and `revision_prompt.md` say
the sources are sections of the documents in a knowledge base. "When you mention an event or a
market move, say the event date" becomes "when a source you use has an event date, say it". The
paragraph on sections headed "當日與之後的行情" stays: it applies only when such a section is among
the sources.

**Rationale**: the instructions are given on every question; naming market news would tell the
model that someone's contract or manual is news.

**What it changes elsewhere**: the split's examples ("an event, a policy, a company, an asset, an
index, or a group and its views") are kept: they are kinds of subject, and a document about other
things has subjects too. Whether the wording changes how the programs split or answer is only seen
in a real run, which needs the maintainer's consent.

### 4. The question box's hint

**Decision**: "問問知識庫裡的文件……" and "Ask about the documents in the knowledge base…", for any
knowledge base. The sample is named by its questions, not by the hint.

### 5. The answer's notice

**Decision**: "本回答由 AI 依知識庫裡的文件產生，不是投資建議。" and "This answer is generated by AI
from the documents in the knowledge base and is not investment advice." "Public data" was true of
the sample news only. "Not investment advice" stays: the screen beside the chat is an investment
strategy, and the answers to it are about that strategy whatever the documents are.

### 6. A run without `--replace` says what else is stored

**Decision**: after a run without `--replace`, the command counts the stored documents that are not
in the folder and, when there are any, says how many and that `--replace` keeps only the folder's.
It does not list them: after the sample news that is 71 lines.

**Rationale**: LangChain's indexing API returns what it did as counts (`num_added`,
`num_updated`, `num_skipped`, `num_deleted`; langchain-core 1.8.4 `indexing/api.py:598-603`) and
leaves the documents it did not touch unmentioned, which suits a loader that adds to a store on
purpose. Here the person who replaces the sample with their own folder and forgets the option would
see answers from both and nothing saying so; one line in the output says so at the moment it
happens. The count is one query on every stored path, so each run now reads them all, with or without the
option; before, a run looked only at the folder's own paths.
