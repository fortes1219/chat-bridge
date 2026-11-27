# Research: Repeated tables and notes sent once

Sources were opened on 2026-11-27. A citation `owner/repo@commit:path:line` points at the file as it
was at that commit.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Tell a table block or note line already sent from a new one by its exact text, keeping the first (decision 2) | Python standard library (`dict`) | 3.13.18 | PSF-2.0 | none added: part of Python | `open-webui/open-webui@926f826:pyproject.toml:124` | `open-webui/open-webui@926f826:backend/open_webui/retrieval/utils.py:633`, `:649-653` |

No package is added.

## Advisories

No package or runtime is added or changed. The lock files are sent to OSV and `npm audit` again
before this feature is delivered, as for every delivery.

## Decisions

### 1. The search keeps its quotas

- **Decision**: No list keeps fewer sections than today: the question's own 8, its wider 30, each
  part's 8.
- **Rationale**: Replayed in the test container on the 26 recorded cases (6 real runs and Claude
  Code's real splits of 20 questions) and 9 questions about market numbers, no model called, each
  list taken deeper and cut at every smaller quota, the question's own 8 always kept whole. Only
  today's quotas and the wider list at 29 (1,760 characters less) lose nothing; the wider list at 30
  with parts at 7 loses 5 items, at 6 loses 11, and the wider list at 20 with parts at 8 loses one
  item and one market row. A cut made after the lists are merged is the shape that lost the
  interest-rate aspect when it was measured here before (`specs/007-search-each-part/`), and the
  shape the sampled chat products use (`open-webui/open-webui@926f826:backend/open_webui/retrieval/utils.py:631-664`;
  `run-llama/llama_index@40d4f79:llama-index-core/llama_index/core/retrievers/fusion_retriever.py:286-295`).
  Keeping each list whole is the shape of `langchain-ai/langchain@30c4e38:libs/langchain/langchain_classic/retrievers/multi_query.py:162`, `:240`.
- **Alternatives**: Smaller quotas per list, or a token budget after a round-robin merge
  (`HKUDS/LightRAG@47038cf:lightrag/operate.py:6698-6749`, `:6893-6923`): both lose items on these
  questions. Letting a model pick or answer each part first: one or more model runs more per
  question.

### 2. A repeated table or note is sent once

- **Decision**: Inside one input, a table block or a quoted line the same as one sent earlier is
  replaced by a line naming the first section that sent it (FR-001 to FR-003).
- **Rationale**: Keeping one copy of the same content has two precedents, at two levels. By content:
  open-webui keys chunks by the SHA-256 of their text and keeps the first
  (`open-webui/open-webui@926f826:backend/open_webui/retrieval/utils.py:298-300`, `:649-653`). By
  a shared parent: LangChain's `MultiVectorRetriever` collects the parent id of every found child
  without repeats and fetches each parent once
  (`langchain-ai/langchain@30c4e38:libs/langchain/langchain_classic/retrievers/multi_vector.py:107-113`);
  there the parents share an id, not only their content. The pointer line itself has no precedent
  found: it is this project's own, and the real run checks that the programs read it right
  (SC-003). It is plain text, so a document could hold the same words; the worst that follows is a
  program reading another section's table as this one's.
- **Limits**: A pointer replaces only what it is shorter than, and points only at an earlier
  section, never at the one it is in.
- **Alternatives**: Sending each distinct table once in a block of its own, before the sections:
  it moves each table away from its event. Leaving the repeated note out without a pointer: the note
  says which market the event is in, and a table without it no longer says so.

### 3. What it saves

- **Decision**: Expect about a tenth on most questions and about a sixth on the holdings question;
  measure the feature's own input in the replay (SC-002).
- **Rationale**: Simulated on the replayed inputs, applying the rule to the market sections and
  counting the pointer lines: the 26 cases save 5.1% / 11.3% / 16.2% (minimum / median /
  maximum); the holdings question's four recorded splits save 14.5% to 16.2% (93,502 to 79,958
  characters for the largest). No distinct table row is lost. The simulation left the news
  sections out of the rule; the replay of SC-002 runs the feature's own code on every section.

### 4. One place builds the input

- **Decision**: The folding is in `model_input`, which builds both the answer's input and the
  revision's.
- **Rationale**: The sources sent to the page and the record's sections come from the same found
  sections before `model_input` is called, so they stay whole (FR-006).

### 5. The prompts say what the lines mean

- **Decision**: One sentence in `chat/answer_prompt.md` and in `strategy/revision_prompt.md`, beside
  the sentence on market tables.
- **Rationale**: The programs are told what each part of their input is; a line they were not told
  about could be read as a missing table.

## Runs

### Replay in the test container (SC-002, 2026-11-27)

The 26 recorded cases, the 9 market questions and the four recorded splits of the holdings
question through the search, each input built as at HEAD `31812f5` (every section whole) and with
this feature's `model_input`; no model called. Today's lengths equal those of an earlier replay at
HEAD, case by case.

| Cases | Characters saved, minimum / median / maximum |
|---|---|
| 26 recorded | 5.1% / 11.3% / 16.2% |
| 9 market questions | 4.5% / 15.8% / 17.6% |
| 4 holdings splits | 14.5% / 15.4% / 16.2% (93,502 to 79,958 for the largest) |

- Every distinct table line of today's input is in the feature's, in every case.
- One replacement falls outside a market section: two files carry the same quoted line, "the
  sources read for this file do not record the decision's effect on stocks", and the second gets
  a pointer.
- No input grew.

### Real run

Not made before this version was committed (T006).
