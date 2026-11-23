# Feature Specification: Search each part of a question before answering

**Feature Branch**: `007-search-each-part` (feature directory; no git branch is tied to it)

**Created**: 2026-11-23

**Status**: Draft

**Input**: User description: "A question that asks about several things at once must find sources for each of them, and must not lose any source the question as asked already finds. Before the answer, the answering program lists the separate things the question asks about; the service searches each one and hands the model the question's own sections and each part's sections together. The sample news's market tables stay in what the model reads, as records of what markets did, not as proof that an event moved them. An answer says which parts its sources do not cover instead of claiming the data has nothing, and the date the data reaches is the knowledge base's."

## Background

One search of eight sections answers a question about one thing well. A question that asks about
six things at once got eight sections, seven of them about the same kind of event, and the answer
said the data had nothing on parts that the knowledge base does cover. The search had not returned
them. The answer also gave, as the date the data reaches, the latest date among those eight
sections, which was eleven days before the knowledge base's latest event.

The six-part question this feature is measured with:

> 近期有哪些利率政策與 AI 資本支出事件？這些事件前後，台積電、0050 與美股科技指數分別出現什麼變化？有哪些機構對後市持不同看法？

Its parts: interest-rate policy events; AI capital-spending events; TSMC; the 0050 fund; US
technology indices; institutions that disagree about what comes next.

Each part has a list of core files: the files whose subject is that part. The lists were labelled
before the change, from the files' titles and text, independently of the implementation, and
checked a second time. The 0050 fund appears only in the market tables, in the section
"當日與之後的行情" (market moves on the day and after), so the 0050 part counts market sections of
the interest-rate and AI capital-spending core files.

Retrieval was measured without a model, on this question and 19 others about the sample news
(research.md decision 9). What it showed:

- Handing the model more sections from one search finds more, but not every part: with 50
  sections, the interest-rate part still had no core file. The search for the whole question
  ranks the other parts above it.
- Searching each part on its own and keeping each part's own sections found every part of the
  six-part question, and lost nothing the question's own search found.
- Merging the parts' results into one ranking and cutting it to a fixed length lost the
  interest-rate part again.

## Changes to earlier features

Approving this specification approves these changes to the requirements of features 001 and 003.

| Requirement | Today | After this feature |
|---|---|---|
| 001 FR-002 | Retrieval uses the user's question as asked, and finishes before the response starts. | Retrieval uses the question as asked and each part the program lists for it (FR-001 to FR-004 here). It still finishes before the response starts. |
| 001 FR-004 | The instructions require the model to say it does not know when the passages are not enough. | The instructions require it to answer each part from the sources found for it, and to say which parts its sources do not cover (FR-008 here). |
| 001 FR-006 | The response states the latest date its sources reach. | The response states the latest date the knowledge base reaches (FR-009 here). |
| 001 FR-010, SC-005 | Claude Code is started with all tools off. | Unchanged. Each answer now starts the program twice, once to list the parts and once to answer; both runs have all tools off (FR-001 here). |
| 003 FR-003, US1 scenario 3 | The page shows the latest date the sources reach. | The page shows the latest date the data reaches, and says so when the question could not be split (FR-011 here). |
| 003 FR-002, FR-003, SC-002 | The page lists every source above the answer, before the answer text. | Before the first answer text the page says how many sources were found, with the whole list one click away. The answer comes next, and under it the sources the answer cites. The service still sends every source before the answer (001 FR-001 unchanged); what changes is how the page draws them (FR-013 here). |

Feature 004 (Codex) is changed the same way as Claude Code: the split uses the program chosen for
the answer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Each part of the question is searched before the answer (Priority: P1)

A person asks one question that covers several topics. Before the answer is written, the answering
program lists the separate things the question asks about. The service searches the question as
asked and each listed part, and hands the model the question's own sections first, then each
part's sections. No part's sections are dropped to make room for another's, and none of the
question's own sections is dropped.

**Why this priority**: this is the failure the feature exists to fix. Questions in this field
usually ask about several events and several assets at once.

**Independent Test**: with the sample news ingested, ask the six-part question with each answering
program. Compare the sections handed to the model with each part's core files and with the
sections the question's own search returns.

**Acceptance Scenarios**:

1. **Given** the sample news is ingested, **When** the user asks the six-part question, **Then** the record of the answer shows the parts the program listed and, for the question and for each part, the sections its search returned.
2. **Given** the same question, **When** the sections handed to the model are compared with the core files, **Then** the interest-rate, AI capital-spending, TSMC and US technology index parts each have at least one core file among them, the institutions part has at least one file that sees a buying chance or a recovery and at least one that warns, and the 0050 part has at least one market section of its files.
3. **Given** the same question, **When** the sections handed to the model are compared with the sections the question as asked returns, **Then** every one of the question's sections is among them, numbered before any part's section.
4. **Given** the same question, **When** the answer is checked part by part, **Then** each part is recorded on its own as one of: passed, missed, insufficient evidence, or wrong number; every number in the answer is checked against the text it cites; no single overall score is given.
5. **Given** the same question in English, **When** the answer ends, **Then** scenarios 1 to 4 hold for it as well, and the answer is in English.
6. **Given** a question about one thing, **When** the program lists no parts, **Then** the model is given the question's own sections only, and the answer cites the same or overlapping sources as before the change.

---

### User Story 2 - A split that fails is never shown as a normal answer (Priority: P1)

Listing the parts is a run of the answering program, and it can fail: the program errs, runs too
long, or returns something that is not a valid list. The answer then goes on with the question's
own sections, and the person is told that the question was searched as a whole because it could not
be split.

**Why this priority**: a broken split looks exactly like a working one unless it is said. An
answer that silently searched less would hide the failure from the person and from whoever could
fix it.

**Independent Test**: make the split fail in each of those ways with a stand-in program, and read
the response and the page.

**Acceptance Scenarios**:

1. **Given** the split run fails, times out, returns no structured output, or returns a list that does not pass the check of FR-002, **When** the answer is given, **Then** the response says the question could not be split and was searched as a whole, the page shows this in its language, and the record keeps the reason.
2. **Given** the split failed, **When** the sections handed to the model are listed, **Then** they are the question's own sections.
3. **Given** the program lists no parts, **When** the answer is given, **Then** no failure is reported: a question about one thing needs no split.

---

### User Story 3 - What the program lists stays search text (Priority: P1)

The listed parts are written by a model from text that comes from outside the app. They are
checked and used only as search text. They never become instructions, a command or a query
statement, and they do not reach the program's instructions.

**Why this priority**: a question can be written to steer the split. Whatever the split returns,
it must not reach anything but the knowledge-base search.

**Independent Test**: stand-in programs that return lists that are too long, hold parts that are
too long, hold other fields, or hold SQL and prompt text; and a real run of a question that asks
the split to list many parts or to search for files on the machine.

**Acceptance Scenarios**:

1. **Given** the split returns more than the most parts allowed, **When** it is checked, **Then** the parts past the limit are left out and the record says how many there were.
2. **Given** a part is empty or longer than allowed, or the list has fields other than the parts, **When** it is checked, **Then** the split counts as failed (User Story 2).
3. **Given** a part holds SQL or instructions, **When** it is searched, **Then** it is passed to the search as a bound parameter and returns knowledge-base sections only, or none.
4. **Given** any recorded real run, **When** both command lines are inspected, **Then** neither holds the question, a passage or a part.

---

### User Story 4 - Honest about what the data covers (Priority: P2)

The answer says which parts the sources it was given do not cover. It does not say the knowledge
base has nothing on them: the sections handed to the model are the top of rankings, and a topic
that ranked lower is still in the knowledge base. Market tables are quoted as records of what
markets did on and after an event's date, not as proof that the event moved them. The date the data
reaches is the latest event date in the whole knowledge base.

The fixed answer, "the data has nothing on this", is a different case, and it stays. It is given only
when the search for the question as asked found no section at all. That is a statement the search
has checked across the whole knowledge base.

**Why this priority**: an assistant that calls a search miss an absence misleads the reader about
the data. The market tables align daily closes with event dates without checking when each event
was published relative to each market's trading session, so a move on the event's date is not
evidence that the event caused it.

**Independent Test**: ask the six-part question and a question about 0050's moves; read the date,
the wording about missing parts and the wording about market moves.

**Acceptance Scenarios**:

1. **Given** the sample news, whose latest event date is 2026-11-17, **When** any question is answered, **Then** the date the data reaches is 2026-11-17, whatever the sources found.
2. **Given** the sources do not cover a part of the question, **When** the answer reaches that part, **Then** it says the sources it was given do not cover that part, not that the knowledge base has nothing on it.
3. **Given** a question about how 0050 or TSMC moved around an event, **When** the answer quotes a market table, **Then** it gives the numbers with the trading dates they belong to and does not say the event caused the move.
4. **Given** a question for which the search of the question as asked finds no section at all, **When** it is asked, **Then** the fixed answer is returned without starting a program, as before.

---

### Edge Cases

- The program lists a part that is the question itself, or the same part twice: each text is searched once.
- A part's search finds nothing: the part adds no section; the record shows it.
- A part's search finds only sections already found: no section is listed twice; each keeps the number it got first.
- While the parts are being listed and searched, before any source arrives, the page shows that the data is being searched, and the stop button works.
- The answer writes a bracket that is not a source number, such as a date `[2026-11-05]`, or a number no source has: it is not listed as a cited source.
- The user stops the answer while the parts are being listed or searched: the split run is stopped as the answer run is, the answer stops as before, and the record keeps what was listed and searched.
- The split run succeeds but the answer run fails: the answer fails as before, with the sources already sent.
- An older knowledge base: no change to how it is reported; this feature adds no column to the knowledge base.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Before an answer, the service MUST start the program chosen for the answer, Claude Code or Codex, once to list the separate things the question asks about, as search texts in a given JSON shape. That run MUST be isolated as the answer run is: all tools off, the question on standard input, API-key variables removed, nothing from the person's own settings.
- **FR-002**: The service MUST check what the split returns: an object whose only field is a list of texts, each text 1 to 200 characters. Up to 8 parts are kept; more are left out and their number recorded. Anything else, or no structured output, is a failed split.
- **FR-003**: The service MUST search the question as asked for its best 30 sections, from 50 candidates per method, and each kept part, as listed and without the question added to it, for its best 8 sections, from 20 candidates per method.
- **FR-004**: The sections handed to the model MUST be the question's own sections first, in rank order, then each part's sections in the order the parts were listed. A section found again keeps the number it got first. No section is dropped to fit a total.
- **FR-005**: The parts MUST be used only as search text, passed to the search as bound parameters. They MUST NOT be placed in the instructions of the answer run.
- **FR-006**: When the split fails (FR-002), runs past its time limit, or the program reports an error during it, the answer MUST go on with the question's own sections, the response MUST say that the question was searched as a whole because it could not be split, and the record MUST keep the reason.
- **FR-007**: When the search for the question as asked returns nothing, the fixed answer MUST be returned without starting a program, as before; no split is run.
- **FR-008**: The instructions to the answering program MUST tell it to answer each part of the question from the sources found for it, to say which parts its sources do not cover, and to quote market tables as records of what markets did on the dates given, without saying an event caused a move. They MUST NOT tell it to say that the data has nothing.
- **FR-009**: The date the data reaches MUST be the latest event date among all documents in the knowledge base, not the latest among the sources found.
- **FR-010**: The record of each question MUST keep the parts listed, how many were left out, the split's time and its error if any, and for the question and each part the sections its search returned and the number each section was given.
- **FR-011**: The page MUST label the date as the date the data reaches, and show that the question was searched as a whole when the split failed, in both languages. Until the sources arrive, it MUST say that the data is being searched, without naming a program it does not know yet.
- **FR-012**: The `search` command's output MUST stay as it is: the chat's settings for this feature do not change the command's.
- **FR-013**: With 30 to 70 sources per answer, the page MUST NOT list them all above the answer. Before the first answer text it MUST say how many sources were found, with the whole list one click away. Under the answer it MUST list the sources the answer cites, read from the source numbers in brackets in its text, each with its number, file name, heading and event date. When a finished answer cites none, it MUST say so. The whole list stays one click away whatever the answer cites, so sources given by code stay visible when the model is led astray.

### Key Entities

- **Part**: one search text the program listed for the question, and the sections its search returned.
- **Split outcome**: the parts kept, how many were left out, and whether the split worked, was not needed, or failed and why.
- **Core files of a part**: the files whose subject is that part of the six-part question, labelled before the change and checked a second time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the recorded real runs of the six-part question, one with each program in each language, every part has at least one core file among the sections handed to the model (the institutions part one from each side), and every section the question as asked returns is among them.
- **SC-002**: A slow test, run in the container without a model, replays the parts recorded in those runs and the parts split from the question's own wording, and shows the same two things for each.
- **SC-003**: For every failure kind of User Story 2, a fast test shows the response saying the question was searched as a whole, and 0 failures produce a response that looks like a normal split.
- **SC-004**: In every recorded real run, the response carries the fixed notice and a source list, and neither command line holds the question, a passage or a part: 0 exceptions.
- **SC-005**: The date the data reaches is 2026-11-17 for every question on the sample news.
- **SC-006**: The existing fast and slow test suites pass, and the `search` command's output for the existing test queries is unchanged.
- **SC-007**: The real runs report, as measured: the split run's time, the parts' searches' time, the time to the first source, the number of parts each program listed, and the number of sections and characters handed to the model.

## Assumptions

- Listing the parts is one more start of the program per answer, so the sources reach the page later than before. The real runs report by how much (SC-007).
- Handing the model 30 to 70 sections instead of 8 makes its input several times longer. Whether answers get better or worse with that much input has not been measured; the real runs check the answers part by part (User Story 1 scenario 4).
- The measurement behind FR-003 split the questions by their own wording, without a model. The parts a real program lists are expected to be fewer and closer to the question; whether they also pass is shown by the real runs (SC-001).
- The limit of 8 parts is a safety bound, not a value tuned on these questions (research.md decision 4).
- One gap stays open after the measurement. For a question about the Taiwan market's records around 5, 6 and 9 November 2026, the file of the 5 November event was found by its news section, but that file's market section was not: it ranked 16th for the part naming that day and 39th for the question as asked. The real runs include this question, to see whether the gap stays when a program lists the parts. If it does, it is the next thing to fix, after looking up how others bring a found file's other sections along.
- Verification runs that really call Claude Code or Codex are made with the maintainer's consent, and their records are part of the delivery.
- Out of scope for this feature, each measured or listed for later: a re-ranking model (measured: no gain worth its time); article titles in the index (measured with the title added to every indexed section, market tables included: no gain; adding it to news sections only was not measured); reading the front-matter fields into the knowledge base or filtering on them; redoing the market comparison; showing the listed parts on the page; conversation history.
