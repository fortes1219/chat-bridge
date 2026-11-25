# Tasks: Previous closes

Each task that changes behaviour is handed over as its own commit, made by the maintainer, before
the next starts.

- [x] T001 The spec, plan, research and tasks (one commit).
- [x] T002 `prices.py`: the previous close of each day for each series, from FinMind, the exchanges' open-data APIs and Yahoo's own quote, in that order; ex-dividend days from the advance notices; every quote of a series takes the previous close of its day; FinMind's latest close kept; requests declared. Fast tests for each scenario of User Stories 1 and 2 (one commit).
- [ ] T003 The panel's words for what is left out, in both languages, with page tests (User Story 3; one commit).
- [ ] T004 Checks; the service run on today's data (SC-002); OSV.
- [ ] T005 Real run during Taiwan trading hours (09:00 to 13:30) and US trading hours (22:30 to 05:00, Taipei time): a live price's previous close, and the prices following (SC-003; the maintainer agreed to the trading-hours run on 2026-11-25).
- [ ] T006 Real run of a dropped connection and its reconnection: asked of the maintainer separately, since it cuts this machine's network.
- [ ] T007 Measure when each open-data daily table changes to the day (read again in the evening of a trading day), and record it in research.md decision 8.
- [ ] T008 Name the exchanges' open data as a source where the panel names its sources, and in the README, in the form the Open Government Data License asks for (data.gov.tw/license, section 3(2) and its attribution annex); check whether FinMind and the Taipei Exchange ask for the same (one commit, before T003). Until it is done, the public repository does not meet that license.
