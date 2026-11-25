# Feature Specification: Your own holdings

**Feature Branch**: `011-own-holdings` (feature directory; no git branch is tied to it)

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "The person adds, changes and removes the holdings of the profile themselves, at any time; the sample stays made up. When the answering program gives advice, the holdings as they are now are part of what it is given."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Change the holdings on the strategy panel (Priority: P1)

The person opens the holdings editor on the strategy panel, adds a holding by its Yahoo Finance
symbol with a name, a quantity and an average cost, changes the quantity, cost or name of a
holding, removes one, sets the cash amount, and saves. The panel then shows the saved holdings,
valued at their prices.

**Acceptance Scenarios**:

1. **Given** the sample profile, **When** the person adds `AAPL` with a quantity and a cost and saves, **Then** the holdings list it, its target is 0%, and its price is read and followed like the others.
2. **Given** a holding, **When** the person changes its quantity or cost and saves, **Then** its value, weight and profit follow the new numbers.
3. **Given** a holding, **When** the person removes it and saves, **Then** it and its target are gone; when the targets then add up to other than 100%, the panel says so.
4. **Given** an open proposal, **When** the person saves holdings, **Then** the proposal is closed as replaced, since it was checked against the holdings before.
5. **Given** a symbol of a Taiwan listing (four to six digits, a letter for some ETFs, then `.TW` or `.TWO`), **When** it is saved, **Then** it is a Taiwan holding in Taiwan dollars; **given** a US ticker (one to five letters, a share class after a dash), **then** it is a US holding in US dollars.
6. **Given** any other symbol (another market's suffix such as `.HK`, `.T`, `.L`; an index with `^`; a currency pair with `=X`; a coin such as `BTC-USD`; `CASH`), **When** the person saves, **Then** nothing is saved and the panel says that only Taiwan and US listings are kept.
7. **Given** a symbol listed twice, an empty name or one longer than 40 characters, a quantity not above 0, a negative cost or cash, any amount above 1e15, or more than 30 holdings besides cash, **When** the person saves, **Then** nothing is saved and the panel says which holding is wrong and why.
8. **Given** a symbol of the right form that Yahoo has no prices for, **When** it is saved, **Then** it is kept and shown without a price, as a holding whose price is missing is shown now.

### User Story 2 - Advice is given on the holdings as they are now (Priority: P1)

**Acceptance Scenarios**:

1. **Given** any question that is answered from the sources, **When** it is sent to the answering program, **Then** the program is given the current holdings with the values, weights, profit and total the service computed, and the targets and rules.
2. **Given** a question about the person's own holdings or strategy that names none of them, **When** its parts are listed for the search, **Then** the program that lists them is given the holdings' symbols and names, so each holding can be searched for.
3. **Given** a question that asks to revise the strategy, **When** the program proposes targets, **Then** they are for the holdings as they are now.

## Requirements *(mandatory)*

- **FR-001**: Saving replaces the holdings with the ones sent, in their order, in one transaction; a holding kept keeps its target, a new one gets 0%, a removed one loses its target.
- **FR-002**: Every check is done by the service before anything is written; the first problem is named with the holding's place in the list.
- **FR-003**: After a save, the prices of new holdings are read and the live prices follow the saved holdings, without the save waiting for them.
- **FR-004**: The numbers the model is given are computed by the service; the model computes none of them.
- **FR-005**: The sample notice stays: the profile is made up and nothing on the panel is investment advice.
- **FR-006**: The README says how to change the holdings and what is not done.

## Not done

- Targets are not typed in: they change only when the person accepts a proposal. After all the holdings are replaced by new ones, every new holding's target is 0% and the total is the cash's alone, until a proposal is accepted.
- Listings other than Taiwan and US, indices, currencies and coins are not kept.
- No trades and no history: the holdings are a quantity and an average cost the person types, and saving replaces them.
- A question about the holdings that names none is searched for at most 8 of them: the split lists at most 8 searches, and up to 30 holdings can be kept.
## Success Criteria *(mandatory)*

- **SC-001**: Each scenario has a fast test; the database writes have a slow test.
- **SC-002**: Run as a person with the service: add, change and remove a holding on the page, see the panel follow, and see a question's input to the stand-in program carry the new holdings.

## Assumptions

- Cash is one amount in Taiwan dollars, as in the sample.
