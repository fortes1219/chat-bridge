# Feature Specification: The strategy screen beside the chat

**Feature Branch**: `006-strategy-screen` (feature directory; no git branch is tied to it)

**Created**: 2026-11-22

**Status**: Draft

**Input**: User description: "The chat stays the centre of the demo. Beside it, the person sees their own investment strategy: summary number cards, an allocation donut, profit and loss, a quotes column, and the checks of rules they set themselves. When they ask in the chat for the strategy to be revised, the answering program hands back a revised strategy; the screen shows current, proposed and change side by side, and the person accepts or rejects it. It is not a copy of a trading product and connects to no broker."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See my strategy at a glance (Priority: P1)

Beside the chat, the person sees a sample investment profile: what they hold, what it is worth,
how it is split, what they gained or lost, and the latest price of each holding with its time.

**Why this priority**: a revision means nothing until the person can see what is being revised.

**Independent Test**: open the page with the sample profile and read the strategy screen.

**Acceptance Scenarios**:

1. **Given** the sample profile, **When** the strategy screen opens, **Then** number cards show the total value, the change since the previous close, the total profit or loss, and the time the prices are from.
2. **Given** the same, **When** the user looks at the allocation, **Then** a donut shows each holding's and cash's share of the total, and the shares add up to 100%.
3. **Given** the same, **When** the user reads the holdings, **Then** each shows its quantity, average cost, latest price with the time of that price, market value, weight, and profit or loss in money and in percent.
4. **Given** a holding whose price could not be had, **When** the screen shows it, **Then** its price is shown as missing, not as zero, it is left out of the totals, and the cards say how many holdings are left out.
5. **Given** the sample profile, **When** the user reads the screen, **Then** it says plainly that the profile is a simulated sample and nothing on the screen is investment advice.
6. **Given** the same, **When** the user looks for their current strategy, **Then** each holding and cash shows its target weight next to its actual weight, without asking for a revision first.

---

### User Story 2 - Ask for a revision and see the difference (Priority: P1)

The person asks in the chat for their strategy to be revised, for example "依據聯準會這半年的動向，
調整我的配置以降低風險". The answering program, Claude Code or Codex, answers from the retrieved
sources as usual and also hands back a revised strategy in a fixed format. The service checks it.
The strategy screen then shows, for each holding and for cash, the current target, the proposed
target and the change; the chat shows a card pointing to it.

**Why this priority**: this is the second half of the demo's task: turning a question about one's
own profile into new settings, with the difference visible at once.

**Independent Test**: ask the sample revision question with each program and read both panels.

**Acceptance Scenarios**:

1. **Given** the sample profile, **When** the user asks the sample revision question, **Then** the chat shows the answer with its sources and a proposal card, and the strategy screen shows a three-column table of current target, proposed target and change for each holding and cash.
2. **Given** a proposal, **When** it is shown, **Then** the numbers in the change column, and the rule checks of the proposed strategy, are computed by the service, not taken from the model's text.
3. **Given** a proposal, **When** the user reads why, **Then** each reason cites the numbered sources it rests on, in the same numbering as the answer.
4. **Given** the program hands back something that does not follow the format, names a holding that is not in the profile, or whose targets do not add up to 100%, **When** the service checks it, **Then** no proposal is shown, and the chat says why the proposal was refused.
5. **Given** a question that asks for no revision, **When** it is answered, **Then** no proposal is shown.
6. **Given** Claude Code answers, or Codex answers, **When** the same revision question is asked, **Then** both hand back a proposal through the same format and the screen behaves the same.

---

### User Story 3 - Accept or reject (Priority: P1)

Nothing changes until the person says so. Accepting makes the proposed targets the current ones
and keeps the previous version; rejecting leaves everything as it was.

**Why this priority**: the program proposes; only the person decides.

**Independent Test**: accept one proposal and reject another; read the strategy and its versions.

**Acceptance Scenarios**:

1. **Given** a proposal is shown, **When** the user has done nothing, **Then** the current strategy is unchanged.
2. **Given** a proposal, **When** the user rejects it, **Then** the current strategy stays as it was and the proposal is closed.
3. **Given** a proposal, **When** the user accepts it, **Then** the proposed targets become the current ones, the rule checks are recomputed, and the previous strategy is kept as an earlier version with the time and the question that led to the change. The holdings, the cards and the donut do not change, because nothing is traded; the screen says so.
4. **Given** the answering program, **When** it answers, **Then** it can only hand back a proposal; it never changes the profile itself.

---

### User Story 4 - The rules I set, checked (Priority: P2)

The person sets limits on the target weights of their own strategy: the most any one holding may
weigh, the least any held holding may weigh, or the most one market may weigh. The screen shows
how many of the rules the strategy meets, and which ones it breaks; a proposal shows the checks
before and after.

**Why this priority**: what counts as better is the person's own measure, not the program's.

**Independent Test**: set three rules, break one, and read the checks; then read them on a proposal.

**Acceptance Scenarios**:

1. **Given** the sample profile's rules, **When** the screen opens, **Then** it shows "M of N rules met" and each rule with pass or fail.
2. **Given** the user adds, changes or turns off a rule, **When** they save it, **Then** the checks are recomputed at once.
3. **Given** a proposal, **When** it is shown, **Then** each rule's result is shown for the current and for the proposed strategy.
4. **Given** a rule of an unknown kind, or a limit outside 0 to 100 percent, **When** the user saves it, **Then** it is refused with the reason.

---

### User Story 5 - Prices with their time (Priority: P2)

The quotes column shows each holding's latest price and the time it is from, and the numbers that
depend on prices follow it.

**Why this priority**: value, profit and loss, and weight all rest on prices, and a price without
its time misleads.

**Independent Test**: open the screen, read the times; change the price feed's data and watch.

**Acceptance Scenarios**:

1. **Given** a holding listed in Taiwan, **When** its price is shown, **Then** it is the latest daily close from the Taiwan Stock Exchange's public data, with its date.
2. **Given** a holding listed in the US, or the Philadelphia Semiconductor index, **When** its price is shown, **Then** it comes from a public source that needs no key, with its time, and the README names the source and its terms of use.
3. **Given** a new price arrives while the page is open, **When** it does, **Then** the column, cards, donut and actual weights update without a reload; the rule checks, which look at target weights, do not change.

---

### Edge Cases

- No price at all can be had: the screen shows the holdings and the strategy with prices missing, and says so; it does not show zero values.
- The user asks for a revision while a proposal is still open: the new proposal replaces the open one, which is closed as not accepted.
- The program hands back a proposal and an answer that disagree: the proposal is checked on its own; the answer text is shown as written.
- The window is narrow: the strategy screen is in the drawer of the chat page (feature 003), and a proposal card in the chat opens it.
- Every text of the screen exists in Traditional Chinese and English, as for the chat page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST ship one simulated sample profile: holdings with market, quantity and average cost; cash; target weights; and a few rules. It MUST be labelled as a simulated sample, not investment advice.
- **FR-002**: The strategy screen MUST show summary number cards, an allocation donut, the holdings with profit and loss, a quotes column with each price's time, and the rule checks, all computed by the service from the profile and the prices.
- **FR-003**: Both answering programs MUST be able to hand back a revised strategy in one fixed format (new target weights for the profile's holdings and cash, and reasons citing source numbers), using each program's own way to return a result in a given format.
- **FR-004**: The service MUST check every proposal before showing it: the format, only holdings already in the profile and cash, targets between 0% and 100% adding up to 100%, and source numbers that exist. A proposal that fails any check MUST be refused with the reason, never shown or repaired.
- **FR-005**: The change column and the rule checks of a proposal MUST be computed by the service.
- **FR-006**: The current strategy MUST change only when the user accepts a proposal. Each accepted change MUST keep the previous strategy as a version with its time and the question that led to it.
- **FR-007**: Rules MUST be set by the user and are checked against the strategy's target weights. Each rule is one kind (the most any one holding may weigh, the least any held holding may weigh, the most one market may weigh) with a limit in percent, and can be turned off.
- **FR-008**: Prices MUST reach the page over the real-time connection of the frontend standards, each with the time it is from; the numbers that depend on prices follow them.
- **FR-009**: The answering programs MUST get the profile, the rules and the prices as data from the service, with the retrieved passages; they get no tool to fetch prices or change the profile themselves.

### Key Entities

- **Profile**: holdings (symbol, name, market, quantity, average cost) and cash.
- **Strategy**: the target weight of each holding and of cash; the current one and its earlier versions.
- **Rule**: kind, limit, on or off.
- **Price**: symbol, price, the time it is from, its source.
- **Proposal**: the proposed targets, the reasons with source numbers, the program that made it, and whether it was accepted, rejected or replaced.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With the sample profile, the five parts of the strategy screen are shown on opening, with no value shown as zero for a missing price.
- **SC-002**: The sample revision question, asked once with Claude Code and once with Codex, yields a checked proposal shown as current, proposed and change in both runs.
- **SC-003**: Every malformed proposal in the tests is refused with its reason, and none is shown.
- **SC-004**: In every test, the stored strategy is unchanged until acceptance, and after acceptance the previous version can be read back.
- **SC-005**: The change column equals the service's own computation in every test.
- **SC-006**: The existing fast and slow test suites still pass.

## Assumptions

- The profile, strategy, rules and versions are kept in the same local database as the knowledge base, in their own tables.
- There is no broker, no orders and no trading: accepting changes the targets, not the holdings.
- Whether the answer text still streams piece by piece when the program also hands back a proposal in a given format is not yet known; the plan measures it. If it does not, the answer to a revision question arrives whole, as Codex's answers already do.
- Back-tests and performance curves are out of scope.
- The page is the chat page of feature 003; this feature fills the place it leaves for the strategy screen.
- Verification that really calls either program is made on the maintainer's machine with the maintainer's consent.
