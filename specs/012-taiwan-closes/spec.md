# Feature Specification: Previous closes

**Feature Branch**: `012-taiwan-closes` (feature directory; no git branch is tied to it)

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "The strategy panel knows every holding's previous close, as every quote screen does: on an ordinary day the close of the trading day before, on a Taiwan ex-dividend or ex-rights day the exchange's reference price. Yahoo's daily series can miss a day, so the previous close has more than one source, and the panel says it does not know only when none of them has it."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Today's change is measured from the right previous close (Priority: P1)

The person looks at the strategy panel. Each holding's change today, and the day's change of the
whole portfolio, are measured from the previous close, as a broker's quote screen measures them.

**Acceptance Scenarios**:

1. **Given** Yahoo's daily series lacks the trading day before today for a Taiwan holding (0050 and 006208 on 2026-11-24), **When** the panel shows today's change, **Then** the previous close is that day's close (95.70 and 215.10) and the change is −5.40 and −11.95.
2. **Given** a Taiwan holding's ex-dividend or ex-rights day with the exchange's reference price known (0050 on 2026-07-21: close 99.20 before, reference price 98.60), **When** the change of that day is shown, **Then** it is measured from the reference price.
3. **Given** a Taiwan holding whose ex-dividend day is today by the exchange's advance notice, **When** the reference price is not known yet, **Then** the reference price is the previous close less the cash dividend when the notice gives a cash dividend only; otherwise no change is shown for it and the panel says why; never a change measured from the close before the dividend. When the exchange's reference price arrives, it replaces the worked-out one, which may differ by the rounding to the price tick.
4. **Given** a live price during the trading day, **When** it arrives, **Then** its previous close is the same one, not one worked out from the stream.
5. **Given** a weekend or a holiday before the day, **When** the change is shown, **Then** the previous close is the close of the last trading day.
6. **Given** a Taiwan holding whose latest close Yahoo has not got yet, **When** FinMind has it, **Then** the panel shows that close, with its day.
7. **Given** an OTC holding (6488.TWO), **When** its data is read, **Then** it is read by its code (6488) as the listed ones are.
8. **Given** FinMind cannot be reached, refuses the request, or does not know the code, **When** the previous close is needed, **Then** it comes from the exchanges' open-data APIs (the latest day of every listed and OTC security), and else from Yahoo's own quote; only when none of them has it is the holding named as not known.
9. **Given** a US holding whose day before is missing from Yahoo's daily series, **When** its change is shown, **Then** the previous close comes from Yahoo's own quote; only when that has none either is it named.
10. **Given** an open-data daily table whose date is earlier than the quote's day, **When** it gives the previous close, **Then** the previous close is its close; **given** its date is the quote's day, **then** the previous close is its close less its change; **given** that day is an ex-dividend or ex-rights day, **then** the table's change is not used and the previous close is the reference price (scenarios 2 and 3).
11. **Given** the service has run since the day before, **When** the first quote of a new trading day arrives for a series, **Then** that series goes through the sources again for that day, once a series a day, and its previous close is the day before's close.

### User Story 2 - The answering program is given the same previous close (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a question answered with the holdings, **When** the program is given each holding's latest price, **Then** the previous close beside it is the one the panel uses.

### User Story 3 - The panel says plainly what is left out (Priority: P2)

**Acceptance Scenarios**:

1. **Given** holdings whose previous close no source has, **When** the panel shows the day's change, **Then** it says, in the page's language: 「{names} 缺前一天的收盤價，今天的漲跌沒有算進這幾檔。」 / "{names}: the previous close is missing, so today's change leaves them out."
2. **Given** a holding on its ex-dividend day whose reference price cannot be known yet, **Then** it says: 「{names} 今天除權息，參考價還沒公布，今天的漲跌沒有算進這幾檔。」 / "{names}: ex-dividend today and the reference price is not out yet, so today's change leaves them out."

## Requirements *(mandatory)*

- **FR-001**: For a Taiwan holding, the previous close of a day is the exchange's reference price when the day is one of its ex-dividend or ex-rights days, and otherwise the close of the last trading day before it.
- **FR-002**: The sources of a Taiwan previous close, in order: FinMind's daily closes and ex-dividend results; the exchanges' open-data APIs (the latest day's close and change, the OTC market's next reference price, the advance notices of ex-dividend days); Yahoo's own quote. For a US holding: Yahoo's daily series, then Yahoo's own quote.
- **FR-003**: Each source is read without a key, when the service starts, when the holdings change, and when a series' first quote of a new trading day is newer than the day its previous close was read for (once a series a day), and only when it is needed:
  - FinMind: two requests a Taiwan series (daily closes, ex-dividend results).
  - The advance notices of ex-dividend days: the listed market's when a listed holding is held, the OTC market's when an OTC holding is held; one request each.
  - The open-data daily tables: the listed market's only when a listed holding still has no previous close after FinMind, the OTC market's only when an OTC holding has none, or to take its next reference price on an OTC holding's ex-dividend day; one request each.
  - Yahoo's own quote: one request a series that still has no previous close.
- **FR-004**: No real-time data is read from FinMind; only daily closes and the reference prices of ex-dividend and ex-rights days.
- **FR-005**: Nothing is guessed: a change is shown only from a previous close one of the sources gives, or from a reference price worked out from a cash dividend the exchange announced.

## Not done

- The Taiwan exchanges' own websites and their real-time quote service: their terms and robots.txt forbid programs.
- Fugle: it needs an account and a key.
- A US ex-dividend day is measured as Yahoo measures it; that is not checked against an exchange.

## Success Criteria *(mandatory)*

- **SC-001**: Each scenario has a fast test.
- **SC-002**: With the service running on today's data, the panel shows 0050 and 006208 measured from 95.70 and 215.10, and no holding is named as missing its previous close.
- **SC-003**: During Taiwan and US trading hours, a live price's previous close is the one the panel showed before the market opened.
