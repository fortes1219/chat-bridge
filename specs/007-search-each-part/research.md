# Research: Search each part of a question before answering

Sources were opened on 2026-11-23. A citation `owner/repo@commit:path:line` points at the file as it
was at that commit. Documentation pages that carry no commit are cited by URL and the line in the
Markdown version of the page (`<page>.md`) as read that day.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Ask the person's Claude Code for the parts of a question in a given JSON shape | Claude Code CLI (`claude -p --output-format json --json-schema`), installed by the person | the person's install | Proprietary (Anthropic); not copyleft | none added: the person's own install | `HKUDS/Vibe-Trading@84af312:agent/src/providers/claude_cli.py:104` | `HKUDS/Vibe-Trading@84af312:agent/src/providers/claude_cli.py:289-290`, `:334` |
| Ask the person's Codex for the parts of a question in a given JSON shape | Codex CLI (`codex exec --output-schema`), installed by the person | 0.166.0 or later | Apache-2.0 | none added: the person's own install | `openai/codex@a0436d6:sdk/typescript/src/exec.ts:50` | `openai/codex@a0436d6:sdk/typescript/src/exec.ts:142-143` |
| Check the list the program returns: one field, the number of parts, each part's length | pydantic | 2.14.3 | MIT | none added: already a dependency | `fastapi/full-stack-fastapi-template@77e550a:backend/pyproject.toml:10` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/api_models.py:5`, `:93-97` |
| Index the event date and read the latest one | SQLAlchemy | 2.0 | MIT | none added: already a dependency | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/pyproject.toml:13` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/postgres_models.py:4`, `:54`; `src/backend/fastapi_app/setup_postgres_database.py:19` |

Merging the lists is the few lines that join these together; decision 2 says whose shape they
follow.

## Advisories

No package is added. The lock is checked against the OSV database before delivery, as every
delivery is.

## Decisions

### 1. The question is split once, before the answer, by the program that will answer it

**Decision**: before each answer, the service starts the program chosen for the answer once more,
with all tools off, and asks it to list the separate things the question asks about as search
texts, in a given JSON shape. The service searches each, then starts the program again to answer.
Splitting is a fixed step of preparing the sources, not something the program decides to do while
answering.

**Rationale**:
- Microsoft's agentic retrieval plans the queries in one model call and runs all of them together
  (`https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview`). Its billing example
  says plans average three subqueries and each subquery reranks up to 50 chunks.
- At TREC 2025, the Glasgow team ran the same retrieval two ways
  (`https://trec.nist.gov/pubs/trec34/papers/uogTr.rag.pdf`): decomposing once and searching each
  sub-question scored 0.3071 strict vital and 0.5590 sub-narrative coverage with 9.71 searches per
  question; letting the model decide its searches turn by turn scored 0.1510 and 0.3562 with 3.82.
  The two runs used different generation models, so this is not a same-model comparison.
- MIT Lincoln Laboratory decomposed each question once, into about eight subqueries on average
  (`https://trec.nist.gov/pubs/trec34/papers/MITLL.rag.pdf`).
- Asking for a JSON shape from the command line is documented for both programs (decision 5).
- The program that answers is the person's own; using it for the split adds no login and no key.

**Alternatives considered**:
- Giving the program the search as a tool to call while it answers. The program then decides
  whether and how often to search, which is the turn-by-turn approach above; and it needs a token,
  a server and a limit of its own. Not used.
- Splitting by the question's own wording, without a model. It was the stand-in for the program in
  the measurement (decision 9). It passed there, but 93 of its 103 pieces added no gold file and
  they brought 409 of the 465 sections it added; and no retrieval chat found splits questions by
  rules: every project read lets a model write the queries (LangChain, LlamaIndex, decision 2).
- Raising only the number of sections from one search. Measured: 50 sections still had no
  interest-rate core file for the six-part question (decision 9).
- A re-ranking model. Measured on the same questions: the two smaller models pushed news sections
  out (43 of 60 against 45 today); the largest found one more than giving 20 sections and added 36
  seconds a question.

### 2. Merging: each part keeps its own sections, union in order, no cut

**Decision**: the model is given the question's own sections first, in rank order, then each
part's sections in the order the parts were listed. A section found again keeps its first place and
number. Nothing is cut to a total.

**Rationale**:
- LangChain's `MultiQueryRetriever` searches every query, joins the lists and keeps each document
  once, in the order found, without cutting
  (`langchain-ai/langchain@66889e2:libs/langchain/langchain_classic/retrievers/multi_query.py:153`
  searches the queries together, `:231-240` the unique union, `:45-46` the order). With
  `include_original` the question as asked is one of the queries (`:60`, `:111-114`).
- Because nothing is cut, every part keeps the sections its own search found, and every section of
  the question's own search stays.
- Measured (decision 9): fusing every list by rank and cutting to 20 or 30, as LlamaIndex's
  `QueryFusionRetriever` does in its reciprocal-rank mode
  (`run-llama/llama_index@dc29b64:llama-index-core/llama_index/core/retrievers/fusion_retriever.py:122`,
  `:277`, `:286-287`), left the interest-rate part with no core file in every variant measured.

**Alternatives considered**: appending the question to each part before searching it, as MIT
Lincoln Laboratory does. Measured: worse in every variant. On this hybrid search the part's words
are drowned by the question's, so each part's search returns the question's own sections again.

### 3. How many sections: 30 for the question, 8 for each part

**Decision**: the question as asked keeps its best 30 sections, from 50 candidates per method. Each
part keeps its best 8, from 20 candidates per method, as one search does today.

**Rationale**: measured on the 20 questions (decision 9), with the parts split from the questions'
wording:

| The question keeps | Gold found / 63 | Lost against today | Taiwan market question / 3 | Sections per question (min, median, max) | Characters, median and max |
|---|---|---|---|---|---|
| 8 | 55 | 0 | 0 | 18, 29.5, 55 | 16,150 and 31,782 |
| 20 | 58 | 0 | 1 | 25, 35.5, 61 | 18,566 and 37,589 |
| 30 | 59 | 0 | 2 | 34, 42.5, 66 | 21,612 and 43,517 |

All three found every part of the six-part question. 30 found the most and is the only one that
found most of the market sections the Taiwan market question asks for. The cost is the length of
what the model reads: about 22,000 characters for the median question, against about 3,300 today.

**Not measured**: whether answers get better or worse with that much input. The real runs check
the answers part by part.

### 4. At most 8 parts, as a safety bound

**Decision**: up to 8 parts are kept. More are left out, and the record keeps how many there were.

**Rationale**:
- The bound keeps a question, or a document, from making one answer run dozens of searches. It is
  not tuned on these questions.
- 8 is about what long questions were split into at TREC 2025: about eight subqueries on average
  (MIT Lincoln Laboratory), 9.71 searches per question (Glasgow). Microsoft's documentation gives
  no bound.
- Leaving out what is past the bound follows LlamaIndex, which trims the generated queries because
  "The LLM often returns more queries than we asked for"
  (`run-llama/llama_index@dc29b64:llama-index-core/llama_index/core/retrievers/fusion_retriever.py:110-111`).
- The real runs record how many parts each program lists.

### 5. Asking for the parts in a given shape

**Decision**: the split run uses the same isolation as the answer run (tools off, question on
standard input, key variables removed) and asks for one field, `parts`, a list of texts.
- Claude Code: `--output-format json --json-schema '<schema>'`; the parts are in the response's
  `structured_output` field.
- Codex: `--output-schema <file>`, the schema in a file in the run's empty folder; the parts are
  the final agent message, read from the `--json` events as the answer is today.

**Rationale**:
- `https://code.claude.com/docs/en/cli-reference` `cli-reference.md:104`: `--json-schema` gives
  "validated JSON output matching a JSON Schema" in print mode.
- `https://code.claude.com/docs/en/headless` `headless.md:174`: the output is in the
  `structured_output` field; `:186`: a run that ends without valid structured output has no such
  field, so its absence is checked.
- Vibe-Trading starts `claude -p` with `--json-schema` and fails when `structured_output` is missing
  (`HKUDS/Vibe-Trading@84af312:agent/src/providers/claude_cli.py:289-290`, `:334-335`).
- `openai/codex@6ff1e1ca3b30:codex-rs/exec/src/cli.rs:52-54`: `--output-schema` is "Path to a JSON
  Schema file describing the model's final response shape". OpenAI's SDK passes it the same way
  (`openai/codex@a0436d6:sdk/typescript/src/exec.ts:142-143`).
- The schema is fixed text, not user text, so it may be on the command line; the question still
  goes on standard input.

### 6. The parts are data

**Decision**: what the split returns is checked with a pydantic model: one field, `parts`, a list
of texts of 1 to 200 characters; any other field, an empty or longer text, or no structured output
is a failed split. Each part is passed to `search()`, where it becomes a bound parameter of the
query, as the question is today. The parts are not put in the answer run's instructions or input.

**Rationale**: the parts are written by a model from outside text. The Azure template checks what a
model writes for its search tool against typed pydantic models before it builds a query
(`Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/api_models.py:86-97`).
200 characters is longer than any part in the measurement (the longest piece was 55 characters,
the longest whole sentence 129) and far shorter than a pasted document.

### 7. A failed split is said, not hidden

**Decision**: when the split fails, runs past 120 seconds, or the program reports an error during
it, the answer goes on with the question's own 30 sections. The context says the question was
searched as a whole, the page shows it in its language, and the record keeps the reason.

**Rationale**: the constitution (V) refuses silent defaults, and a fallback that looks like a
working split is one. Going on with the question's own sections keeps an answer possible when the
split alone fails. 120 seconds is well past the 8 to 19 seconds a program took to start and write
its first word in earlier real runs, and well short of the answer's 600-second limit.

### 8. Market tables: records of what markets did, not proof of cause

**Decision**: market sections are handed to the model like any other section. The instructions
tell it to quote them as records of what markets did on the dates given, and not to say an event
caused a move.

**Rationale**: the tables align daily closes with event dates without checking when each event was
published relative to each market's trading session. A move on the event's date is therefore a
record, not evidence of cause.

### 9. The measurement

All runs were in the test container (6 CPUs, 8 GB), on the 71 sample files, without a model.
20 questions about the sample news, each with draft gold files (63 in all; one question, about the
Taiwan market's moves, counts the market sections of its gold files). A gold file counts when one of
its news sections is among the sections given; market sections count only for that question. The
six-part question's parts are counted against their core files.

Results (the question's own search; "today" is 8 sections from 20 candidates):

| Variant | Sections given | Gold found / 63 | Lost against today | Interest-rate core files for the six-part question |
|---|---|---|---|---|
| Today | 8 | 45 | 0 | 0 of 9 |
| One search, 20 sections | 20 | 52 | 1 | 0 of 9 |
| One search, 30 sections | 30 | 56 | 0 | 0 of 9 |
| One search, 50 sections | 50 | 61 | 0 | 0 of 9 |
| Article title added to every indexed section | 20 | 51 | 1 | 0 of 9 |
| Split, each part's own 8, union (decision 2) | 18 to 55 | 55 | 0 | 7 of 9 |
| Split, all lists fused by rank, cut to 30 | 30 | 52 to 56 | 0 to 1 | 0 of 9 |
| Split with the question appended to each part | 8 to 18 | 48 | 0 | 0 of 9 |

- The parts were cut from each question's own wording at its punctuation and its list words
  ("、", "與", "和", "及", "and"), without a model and without the gold files. Splitting only at
  sentences left TSMC with no core file.
- With the question keeping 30 and each part 8, the six-part question's parts had: interest-rate 7
  of 9, AI capital spending 7 of 10, TSMC 2 of 3, US technology indices 7 of 8, institutions that see
  a chance 3 of 5, institutions that warn 2 of 3; and 0050 market sections were among them.
- Gold files still missed by that variant: two for the six-part question (whose parts are all
  covered), one market section for the Taiwan market question, and one file for a question that
  lists three days of market events.
- Searching the parts one after another took a median of 6.8 seconds a question. Running the
  searches concurrently did not shorten it, because each search embeds its query on the same CPU.
  The plan runs them in one session with one embedding call; that time is not measured yet.

### 10. The date the data reaches: the latest event date in the knowledge base

**Decision**: `SELECT max(event_date) FROM documents`, with a B-tree index on
`documents.event_date`, declared on the model and created by `create_all` as the Azure template
declares and creates its indexes.

**Rationale**:
- Azure declares indexes on the model: `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/postgres_models.py:4`, `:54`.
- It creates them with `create_all`: `src/backend/fastapi_app/setup_postgres_database.py:19`.
- The latest date among the sources found said more about the search than about the data.

**Known limit**: `create_all` does not add an index to a table that already exists. A knowledge
base built before this feature answers the same query without the index, reading one row per
ingested file, 71 for the sample news, until it is rebuilt.

### 11. The instructions: answer each part, say what the sources do not cover

**Decision**: replace "If they do not hold the answer, say that the data has nothing on it" with
instructions to answer each part of the question from the sources found for it, and to say which
parts the sources it was given do not cover; add the market-table wording of decision 8.

**Rationale**: the Azure template's answer prompt limits the claim to the sources given: "If there
isn't enough information below, say you don't know"
(`Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/prompts/answer.txt:4`).
Telling the model to say "the data has nothing" turned every search miss into a claim about the
whole knowledge base.

### 12. The six-part question as a regression test, and what it can and cannot show

**Decision**: a slow test, run in the container without a model, takes the six-part question in
Traditional Chinese and in English and checks the sections the chat would hand the model:
- with the parts split from the question's own wording, as measured;
- after the real runs, with the parts each program actually listed, saved to the test data.

For each, every part has at least one core file (the institutions part one from each side), the
0050 part has a market section of its files, and every section of the question's own search is
there. A second slow test checks that the `search` command's output for the existing test queries
is unchanged.

The data file `tests/data/multi_part_question.json` holds the question in both languages, each
part's core file names with the side of each institutions file, and, after the real runs, the parts
the programs listed.

**What the test cannot show**: what parts a program lists for a question it has not been asked
before. That needs the model. It is shown by the recorded real runs, and by questions that took no
part in building this feature, which are kept apart from this work and run only after delivery.

## Real runs (each needs the maintainer's consent)

To run after the code, each recorded in full:
- the six-part question, with Claude Code and with Codex, in Traditional Chinese and in English;
- a question about one thing, with each program;
- the question about 0050's moves around an event, with each program;
- the question about the Taiwan market's records around 5, 6 and 9 November 2026, with each
  program, to see whether the 5 November market section is still missed (spec Assumptions);
- the attacks recorded for feature 001, and a question that asks the split to list many parts and
  to search for a file on the machine;
- the split of each of the 20 measurement questions, with Claude Code, without the answer run: the
  parts it lists, and whether the sections they find pass the two checks of decision 9.

Each run reports the times of SC-007. Each Claude Code run also shows that the schema reached it
unchanged: an invalid schema makes Claude Code exit with an error (`headless.md:184`), and a run
whose schema arrived changed would return no `structured_output`.
