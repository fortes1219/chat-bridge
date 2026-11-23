# Implementation Plan: A chat page in the browser

**Branch**: `dev/rc-0.1.0` (feature directory `specs/003-chat-page/`) | **Date**: 2026-11-22 | **Spec**: [spec.md](spec.md)

## Summary

`uv run chat-bridge` builds the page once with the reader's own Node.js and serves it from the
same address as the service. The page first asks the service which of Claude Code and Codex is
logged in; with neither, it shows only how to log in and a button to check again. With one, it
shows the chat as the main panel and a place for the strategy screen beside it. The page's data
layer is contract first: zod schemas, an oRPC contract for each route's types, API functions that
check every response against the schemas, and one request module; TanStack Query wraps the API
functions. A question goes to the chat endpoint, which now streams Server-Sent Events; each event
is checked as it arrives; the sources appear first, then the answer, rendered as sanitised
Markdown, with the fixed notice. Every text exists in Traditional Chinese and English, and the
language and the chosen program are in the address.

Before the page is built, the four review follow-ups of feature 004 are done (its tasks T013 to
T016): the page's login screen shows what they correct.

## Technical Context

**Language/Version**: Python 3.13 (service); TypeScript 6 with Vue 3.5 (page)

**Primary Dependencies**: service: FastAPI 0.163.2 (`fastapi.sse`, `StaticFiles`), nothing
added. Page: Nuxt UI 4.13, zod 4, `@orpc/contract` 1.16.4 (types only), axios with its fetch
adapter and eventsource-parser (transport), TanStack Vue Query 5, vue-router 5, vue-i18n 11, `@comark/vue`
0.9.2; built with Vite 8. Every one is in research.md's Packages table.

**Storage**: none new.

**Testing**: pytest for the service (the stream format, serving the page, the build step's
decisions); Vitest with Vue Test Utils and happy-dom for the page, one spec per layer and view in
`frontend/tests/` mirroring `src/`; `vue-tsc` for types; ESLint and Prettier. Real runs in the
browser with the maintainer's consent (research.md).

**Target Platform**: the reader's machine: Windows, macOS, Linux, with Python and a Node.js that
still gets security fixes, at its latest security release (research.md, ## Advisories).

**Project Type**: a command-line tool that starts a local web service and its page.

**Constraints**: one command (spec FR-008); the endpoint's refusals unchanged (FR-009); nothing an
answer or a source holds runs in the page (FR-005); the frontend standards of the constitution.

## Constitution Check

| Principle | How this plan meets it |
|---|---|
| I. Ecosystem Precedent First | Each need is an installed package in research.md's Packages table; components and build follow Nuxt UI's official Vue chat template, without its AI SDK. |
| II. Clone and Run | The one command builds the page with the reader's Node.js and serves it; nothing is built in advance or installed by hand. |
| III. Raw Documents Go to the Embedding Model | Unchanged: the page shows what the service sends. |
| IV. Untrusted Content Stays Data | Answers and sources are rendered sanitised; sources as plain text; the notice and sources come from the service. |
| V. Feature-Based Structure and Clean Code | `service/` in four layers, `queries/`, and `views/<feature>/` with its components and composables; lookups as tables; at most three levels. |
| VI. Cost Follows the Work | The page is built once and rebuilt only when its sources change; the login states are read once and on request, never on a timer or on focus. |
| VII. Tests Prove What the User Gets | Service tests for the stream and serving; page tests per layer and view, the login screen, sanitising and language; real runs in the browser. |
| VIII. Honest Claims | The page shows the notice, the sources' dates, and "the data has nothing on this" as the service sends them. |
| Frontend Standards | Contract first with zod and oRPC, every response and streamed event checked against its schema at the API boundary; server state in TanStack Query; no Socket.IO here (the chat streams in its POST); three levels; feature folders; Nuxt UI only; both languages. |

Result: passes.

## Project Structure

```text
chat_bridge/
├── chat/router.py        # /chat/stream answers text/event-stream through fastapi.sse
├── web.py                # new: build the page once with Node.js, serve frontend/dist
└── cli.py                # the no-argument command builds the page before it serves

frontend/                 # new
├── package.json, package-lock.json, vite.config.ts, vitest.config.ts, tsconfig*.json
├── eslint.config.js, .prettierrc.json, index.html
├── src/
│   ├── main.ts, App.vue
│   ├── router/index.ts
│   ├── i18n/             # zh-TW and en messages, at most three key levels
│   ├── service/
│   │   ├── schema/       # zod, .strict(): programs, chat context and pieces, error body
│   │   ├── contract/     # oRPC contract: method, path, summary, schemas (types only)
│   │   ├── api/          # programs.ts, chat.ts: input check, request, parseContract
│   │   ├── request.ts    # the only transport: one axios instance (fetch adapter) for JSON and the stream
│   │   └── error.ts      # AppError, normalisation, parseContract
│   ├── queries/          # keys.ts, query-client.ts, use-programs-query.ts, use-ask-mutation.ts
│   └── views/
│       └── chat/
│           ├── ChatPage.vue
│           ├── components/   # LoginGate, ChatPanel, SourceList, SampleQuestions, StrategyPlace
│           └── composables/  # useAddressState (language, program), useAsk (stream, stop)
└── tests/                # mirrors src/: service/, queries/, views/chat/

tests/web/test_web.py, tests/chat/test_stream_events.py   # service side
README.md, README_tzh.md, .gitignore (frontend/dist, frontend/node_modules)
```

## Complexity Tracking

None.
