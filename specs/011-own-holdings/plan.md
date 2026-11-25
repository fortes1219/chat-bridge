# Implementation Plan: Your own holdings

**Spec**: [spec.md](spec.md)

## Summary

Add a holdings editor to the strategy panel and `PUT /strategy/holdings`, shaped like the rules
editor and `PUT /strategy/rules`. After a save, the price feed follows the saved holdings. The
block of holdings that revision questions carry goes with every answered question, with the
numbers the service computed.

## Technical Context

- Python 3.11 or later, FastAPI, SQLAlchemy, pydantic; Vue 3 with Nuxt UI, zod, oRPC and
  TanStack Query, as the rules editor.
- Cost: a save is one transaction on at most the holdings sent; the prices are read only for the
  new symbols' series once, then the live stream is restarted with the saved symbols.

## Files

- `chat_bridge/strategy/schemas.py`: `HoldingInput`, `HoldingsRequest`, the new error codes.
- `chat_bridge/strategy/store.py`: `check_holdings`, `save_holdings`.
- `chat_bridge/strategy/state.py`: follow the saved holdings' prices.
- `chat_bridge/strategy/router.py`: `PUT /strategy/holdings`.
- `chat_bridge/strategy/revision.py`: the computed numbers in the strategy block.
- `chat_bridge/chat/service.py`, `chat/answer_prompt.md`: the strategy block with every question.
- `frontend/src/service/schema`, `contract`, `api`; `views/strategy/components/HoldingsEditor.vue`,
  `composables/useHoldingsEditor.ts`; the texts in both languages.
- Tests beside the existing strategy and chat tests.
