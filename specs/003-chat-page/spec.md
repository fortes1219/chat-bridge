# Feature Specification: A chat page in the browser

**Feature Branch**: `003-chat-page` (feature directory; no git branch is tied to it)

**Created**: 2026-11-20

**Status**: Draft

**Input**: User description: "After cloning and running one command, a person opens a page in the browser, types a question, and watches the answer appear with its sources, their dates and the fixed notice, in Traditional Chinese or English. Nothing a document or the model writes can run as code in the page."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask in the browser and watch the answer arrive (Priority: P1)

A person who cloned the demo runs `uv run chat-bridge`, opens the address it prints, types a
question and sends it. The sources appear first, each with its file name, heading and event date;
the answer then appears piece by piece; the fixed notice that this is not investment advice is
always on screen with the answer.

**Why this priority**: it is the first thing anyone evaluating the demo looks for. Until it
exists, the demo can only be driven from a terminal.

**Independent Test**: start the service, open the page, ask the sample question, and watch.

**Acceptance Scenarios**:

1. **Given** the service is running and the sample documents are ingested, **When** the user opens the printed address, **Then** a chat page loads with a place to type a question.
2. **Given** the page is open, **When** the user asks "聯準會在這近半年的動向哪些行為導致股市動盪", **Then** the sources appear before the answer text, and the answer text grows while it is being written.
3. **Given** an answer is on screen, **When** the user reads it, **Then** each source shows its file name, heading and event date, the latest date the sources reach is shown, and the fixed notice is visible.
4. **Given** an answer cites a source as `[2]`, **When** the user looks for it, **Then** they can tell which of the listed sources is number 2.
5. **Given** an answer is being written, **When** the user stops it, **Then** the text stops growing and the page is ready for another question.

---

### User Story 2 - Nothing from a document or the model runs in the page (Priority: P1)

Answers and source text come from ingested documents and from the model. If they contain HTML,
scripts or `javascript:` links, the page shows them as text or removes them; it never runs them
and never loads something from another site because of them.

**Why this priority**: the page runs in the user's own browser next to their other tabs. A demo
that executes what it was asked to read is not safe to hand to anyone.

**Independent Test**: ingest a test document whose text holds an image tag with an error handler,
a script tag and a `javascript:` link, ask a question that retrieves it, and watch the page.

**Acceptance Scenarios**:

1. **Given** a test document containing `<img src=x onerror=...>`, a `<script>` tag and a `[link](javascript:...)` has been ingested into a test knowledge base, **When** an answer or a source that quotes it is shown, **Then** no script runs and no dialog opens.
2. **Given** the same answer, **When** the user clicks every link in it, **Then** none of them runs code; ordinary `https` links open as links.
3. **Given** the model writes Markdown (lists, bold, a table), **When** the answer is shown, **Then** it is formatted, not shown as raw symbols.

---

### User Story 3 - The page says plainly when there is no answer (Priority: P2)

When Claude Code is missing or not logged in, when the knowledge base is empty, when the data has
nothing on the question, or when the answer breaks off, the page says which, and what to do.

**Why this priority**: a first-time user will hit one of these before they see a good answer.

**Independent Test**: produce each condition in turn and read what the page shows.

**Acceptance Scenarios**:

1. **Given** the user has just opened the page, **When** it loads, **Then** it shows, before any question is asked, whether Claude Code and Codex are each installed and logged in on this machine, and which one will answer.
2. **Given** neither is logged in, **When** the page loads, **Then** it says so, shows the command to log in, and lets the user check again without reloading.
3. **Given** Claude Code is not logged in, **When** the user asks a question, **Then** the page shows the sources that were found and a message that Claude Code is not logged in, with the command to run.
2. **Given** the knowledge base is empty, **When** the user asks a question, **Then** the page says so and names the `ingest` command.
3. **Given** the question is off-topic, **When** the answer arrives, **Then** the page shows the fixed "the data has nothing on this" answer and no sources.
4. **Given** the answer breaks off with an error, **When** it does, **Then** the text received so far stays on screen with the error under it.

---

### User Story 4 - Traditional Chinese and English (Priority: P2)

Every label, button and message of the page exists in Traditional Chinese and in English, and the
user can switch. The answer itself is in the language of the question, whatever the page language.

**Why this priority**: the demo is shown to readers of both languages.

**Independent Test**: switch the page language and reload.

**Acceptance Scenarios**:

1. **Given** the page is in Traditional Chinese, **When** the user switches to English, **Then** every label, placeholder and message changes, and the questions and answers already on screen stay as they are.
2. **Given** the user chose a language, **When** they reload the page or send its address to someone, **Then** the page opens in that language.
3. **Given** the page is in English, **When** the user asks in Traditional Chinese, **Then** the answer is in Traditional Chinese.

---

### User Story 5 - Still one command (Priority: P2)

`uv run chat-bridge` remains the only command a reader runs. They do not build the page by hand.

**Why this priority**: every extra step loses readers, and the project's rule is clone and run.

**Independent Test**: on a fresh clone with only Python, Node.js and a logged-in Claude Code, run
the one command and open the page.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** the reader runs `uv run chat-bridge`, **Then** the page is served at the address the command prints, and the reader ran no other command for the page.
2. **Given** Node.js is missing, **When** the reader runs the command, **Then** it says that Node.js is needed for the page, instead of failing later with an unrelated error.
3. **Given** the page was prepared once, **When** the command is run again, **Then** it starts without preparing it again.
4. **Given** the README, **When** a reader follows it, **Then** it tells them the one command and the address to open.

---

### Edge Cases

- A very long answer: the page stays responsive, and the newest text is in view unless the user scrolled up to read.
- The user sends a second question while the first is still being written: the first is stopped or the send is disabled; the two answers never interleave.
- An empty question, or one over the length limit: the page does not send it and says why.
- The window is narrow (a laptop split in half): the question box and the answer are still usable.
- The service is stopped while the page is open: the next question shows that the service cannot be reached.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The service MUST serve a chat page at the address it prints on start.
- **FR-002**: The page MUST send the question to the existing chat endpoint and show the response as it streams: sources first, then the answer text piece by piece.
- **FR-003**: The page MUST show, for every answer, each source's number, file name, heading and event date, the latest date the sources reach, and the fixed notice exactly as the service sends it.
- **FR-004**: The page MUST let the user stop an answer that is being written.
- **FR-005**: The page MUST render the answer's Markdown, and MUST neither run nor load anything that an answer or a source contains: scripts, event handlers, `javascript:` and `data:` links, frames and embedded objects are removed or shown as text.
- **FR-006**: The page MUST show a specific message for each of: Claude Code not installed, not logged in, state unknown; knowledge base empty or built by another version; the data has nothing on the question; an error after the answer started; the service unreachable.
- **FR-011**: On opening, and again on request, the page MUST show the login state of each supported assistant program on this machine (Claude Code, Codex): not installed, not logged in, logged in, or unknown. Unknown is never shown as logged in. The check reads only what each program reports about itself; it never opens their credential files.
- **FR-012**: The page MUST say which program answers, and when both are logged in MUST let the user choose. The chosen program is part of the page's address. Answering with Codex is provided by feature 004.
- **FR-007**: Every text of the page MUST exist in Traditional Chinese and English, and the chosen language MUST survive a reload and be part of the page's address.
- **FR-008**: `uv run chat-bridge` MUST remain the only command needed. Preparing the page is done by that command, once, and a missing Node.js is reported as such.
- **FR-009**: The page MUST NOT change what the chat endpoint accepts or refuses: requests still carry a JSON content type, and the service still refuses other hosts and other origins.
- **FR-010**: The page shows one question and its answer at a time as independent exchanges; earlier exchanges stay on screen during the visit, and no conversation history is sent to the model.

### Key Entities

- **Exchange**: one question, its sources, the latest source date, the answer text so far, its state (being written, finished, stopped, failed) and any error.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a fresh clone, a reader gets from the one command to a visible answer in the browser without running any other command.
- **SC-002**: The sources are visible before the first answer text, and the first answer text is visible before the answer is complete.
- **SC-003**: With the hostile test document, 0 scripts run and 0 dialogs open, in the answer and in the sources.
- **SC-004**: 100% of the page's own texts exist in both languages; switching language changes all of them and none of the answers.
- **SC-005**: Each of the no-answer conditions of User Story 3 produces its own message; none shows a blank answer or a raw error object.
- **SC-006**: The existing fast and slow test suites still pass, and the chat endpoint's refusal tests are unchanged.

## Assumptions

- The reader's machine has Python, Node.js and their own logged-in Claude Code, as for the rest of the demo.
- The page is for one person on their own machine; there is no sign-in.
- The look follows one ready-made component set with its chat components; the page does not carry a second component set. The choice is recorded in `plan.md`.
- Out of scope for this feature: proposing and accepting investment-profile changes, suggested questions, conversation history sent to the model, saving exchanges across visits, and list virtualisation.
- Verification that really calls Claude Code is made on the maintainer's machine with the maintainer's consent; everything else is checked without the model.
