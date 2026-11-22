# Research: A chat page in the browser

The page is a Vue 3 single-page app built with Vite from `frontend/`, using Nuxt UI's components
and its chat components, served by the FastAPI service. Its data layer is contract first, in four
layers: zod schemas, an oRPC contract that holds each route's types, API functions that call the
service and check every response against the schemas, and one request module that does the
transport. TanStack Query wraps the API functions as an async state machine. The chat endpoint
streams Server-Sent Events. `uv run chat-bridge` builds the page with the reader's own Node.js
the first time, then serves it.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| The page itself | vue | 3.5 | MIT | 2.5 MB | `nuxt-ui-templates/chat-vue@da02783:package.json:36` | `nuxt-ui-templates/chat-vue@da02783:src/main.ts:3`, `:13` |
| Build the page | vite, @vitejs/plugin-vue | 8, 6 | MIT | 2.3 MB, 75 KB (build only) | `nuxt-ui-templates/chat-vue@da02783:package.json:50`, `:43` | `nuxt-ui-templates/chat-vue@da02783:vite.config.ts:1`, `:3`, `:10`, `:17` |
| Components: chat messages and prompt, empty state, side-by-side panels, drawer | @nuxt/ui | 4.13.0 | MIT | 2.9 MB | `nuxt-ui-templates/chat-vue@da02783:package.json:22` | `nuxt-ui-templates/chat-vue@da02783:src/main.ts:9`, `:23`; `vite.config.ts:7`, `:18` |
| Styling the components use | tailwindcss | 4 | MIT | 769 KB (build only) | `nuxt-ui-templates/chat-vue@da02783:package.json:34` | `nuxt-ui-templates/chat-vue@da02783:src/assets/css/main.css:1` |
| Language and program in the address | vue-router | 5 | MIT | 1.3 MB | `nuxt-ui-templates/chat-vue@da02783:package.json:37` | `nuxt-ui-templates/chat-vue@da02783:src/main.ts:5`, `:16-19` |
| Render the answer's Markdown, with scripts, handlers, unsafe links and outside images removed | @comark/vue | 0.9.2 | MIT | 62 KB | `nuxt-ui-templates/chat-vue@da02783:package.json:19` | `nuxt-ui-templates/chat-vue@da02783:src/components/chat/Comark.ts:1` |
| Copy a login command | @vueuse/core | 14 | MIT | 883 KB | `nuxt-ui-templates/chat-vue@da02783:package.json:26` | `nuxt-ui-templates/chat-vue@da02783:src/components/chat/ChatVisibility.vue:4`, `:18`, `:68` |
| Schemas of every request, response and streamed event, checked at the boundary | zod | 4.6.7 | MIT | 5.9 MB | `middleapi/orpc@26175d2:playgrounds/contract-first/package.json:23` | `middleapi/orpc@26175d2:playgrounds/contract-first/src/contract/sse.ts:2`, `:11` |
| The contract: each route's method, path and schemas, with types inferred from it | @orpc/contract | 1.16.4 | MIT | 90 KB | `middleapi/orpc@26175d2:playgrounds/contract-first/package.json:13` | `middleapi/orpc@26175d2:playgrounds/contract-first/src/contract/sse.ts:1`, `:4-11` |
| The request module's one transport, for JSON calls and the chat stream (its fetch adapter returns the response body as a stream) | axios | 1.21 | MIT | 2.1 MB | `vbenjs/vue-vben-admin@e726bc9:packages/effects/request/package.json:28` | `vbenjs/vue-vben-admin@e726bc9:packages/effects/request/src/request-client/request-client.ts:7`, `:76` |
| Read the chat's Server-Sent Events from a POST response | eventsource-parser | 4.1 | MIT | 96 KB | `vercel/ai@d55f3cf:packages/provider-utils/package.json:63` | `vercel/ai@d55f3cf:packages/provider-utils/src/parse-json-event-stream.ts:2-4`, `:22` |
| Server state as an async state machine: pending, error, refetch, cancel | @tanstack/vue-query | 5.108 | MIT | 1.6 MB | `middleapi/orpc@26175d2:playgrounds/nuxt/package.json:19` | `middleapi/orpc@26175d2:playgrounds/nuxt/app/plugins/vue-query.ts:10-23`; `app/components/orpc-stream.vue:2`, `:6` |
| Every page text in Traditional Chinese and English | vue-i18n | 11.4 | MIT | 1.7 MB | `vbenjs/vue-vben-admin@e726bc9:packages/locales/package.json:31` | `vbenjs/vue-vben-admin@e726bc9:packages/locales/src/i18n.ts:11`, `:22` |
| Type-check the page | typescript, vue-tsc | 6, 3 | Apache-2.0, MIT | 23.2 MB, 7 KB (build only) | `nuxt-ui-templates/chat-vue@da02783:package.json:48`, `:53` | `nuxt-ui-templates/chat-vue@da02783:package.json:10` |
| TypeScript settings for Vue in the browser, and Node.js types for the build settings | @vue/tsconfig, @types/node | 0.9.1, 24.19.2 | MIT | 12 KB, 2.5 MB (build only) | `vuejs/create-vue@4a0464c:template/tsconfig/base/package.json:4`; `template/config/typescript/package.json:8` | `vuejs/create-vue@4a0464c:template/tsconfig/base/tsconfig.app.json:2`; `template/tsconfig/base/tsconfig.node.json:19` |
| Lint the page | eslint, eslint-plugin-vue, @vue/eslint-config-typescript (brings typescript-eslint), @eslint/js, globals, eslint-config-prettier | 10.15.0, 10.12.1, 14.9.0, 10.0.1, 17.14.0, 10.1.8 | MIT | 2.8 MB, 1.1 MB, 84 KB, 15 KB, 253 KB, 58 KB (dev only) | `vuejs/create-vue@4a0464c:template/linting/core/ts/package.json:3-5`; `template/linting/core/js/package.json:3`, `:6`; `template/linting/formatter/package.json:3` | `vuejs/create-vue@4a0464c:template/linting/core/ts/eslint.config.js.ejs:2`, `:13`; `template/linting/core/js/eslint.config.js.ejs:2`, `:19`; `template/linting/formatter/eslint.config.js.data.mjs:7-8` |
| Build every icon the page names into the page; one it does not name would still be fetched from the Iconify API, and Nuxt UI has no switch to stop that | @iconify-json/lucide | 1.2.158 | ISC | 676 KB | `nuxt/ui@422d015:playgrounds/vue/package.json:23` | `nuxt/ui@422d015:playgrounds/vue/vite.config.ts:3`, `:9`; `docs/content/docs/1.getting-started/6.integrations/1.icons/2.vue.md:84`, `:110-119`, `:126-144`, `:146-148` |
| Format the page | prettier | 3.10 | MIT | 10.9 MB (dev only) | `vuejs/core@7de9e41:package.json:97` | `vuejs/core@7de9e41:package.json:17-18` |
| Test the page's layers and views | vitest, @vue/test-utils, happy-dom | 5, 2.6, 21 | MIT | 2.8 MB, 1.4 MB, 8.8 MB (test only) | `vuejs/create-vue@4a0464c:template/config/vitest/package.json:9`, `:11`; `nuxt/ui@422d015:package.json:225` | `vuejs/create-vue@4a0464c:template/config/vitest/src/components/__tests__/HelloWorld.spec.js:1`, `:3`, `:8`; `nuxt/ui@422d015:vitest.config.ts:48` |
| Stream the answer as Server-Sent Events | fastapi (`fastapi.sse`) | 0.163.2 | MIT | none added: already a dependency | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/pyproject.toml:6` | `fastapi/fastapi@b283119:docs_src/server_sent_events/tutorial001.py:4`, `:22-25` |
| Serve the built page | fastapi (`StaticFiles`) | 0.163.2 | MIT | none added | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/pyproject.toml:6` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/routes/frontend_routes.py:4`, `:11`, `:22` |
| Build the page with the reader's own Node.js, once, and say so when Node.js is missing or too old | npm (comes with Node.js) | Node.js 22.23.5, 24.22.3 or 26.13.1 or later in the same line | Artistic-2.0 | none added: the reader's own Node.js | `reflex-dev/reflex@df7f157:reflex/utils/js_runtimes.py:25` | `reflex-dev/reflex@df7f157:reflex/utils/js_runtimes.py:818`; `reflex/utils/build.py:297`, `:319-320` |
| Check the project's own code rules by structure, in Python, TypeScript and the script and template of `.vue` files | ast-grep-cli | 0.51.3 | MIT | 17.9 MB on Windows, 8.9 MB on Linux (dev only) | `langgenius/dify@a7ea6e1:.github/workflows/autofix.yml:105` | `langgenius/dify@a7ea6e1:.github/workflows/autofix.yml:105-108`, `:126` |

Sizes are npm's unpacked sizes of each package's version (2026-11-22), not the size each adds to
the built page.

Notes on the citations:

- The page's components and build come from Nuxt UI's official Vue chat template. The template
  manages chat state with the Vercel AI SDK; this page does not take the AI SDK.
- oRPC: the stable line is 1.16.4 (`middleapi/orpc`, branch `1.x`, commit `26175d2`, tagged
  `v1.16.4`); its `main` is a 2.0 beta. Only `@orpc/contract` is used, for the contract and the
  types inferred from it; no oRPC client or link is used, because the page has its own request
  module.
- FastAPI's built-in Server-Sent Events are new in the FastAPI already used here; the example is
  FastAPI's own.
- Reflex is a Python framework whose command checks the Node.js version, runs the package
  manager's `install`, and runs its `export` script, which builds the frontend, on the user's
  machine; that is the shape of this need. Reflex also installs a JavaScript runtime of its own
  when missing; this project does not, it reports the missing Node.js instead (spec FR-008).

## Advisories

Checked 2026-11-22 against the OSV database (`api.osv.dev/v1/querybatch`, ecosystem npm), at the
versions the page would install: vue 3.5.46, vite 8.3.8, @vitejs/plugin-vue 6.0.11, @nuxt/ui
4.13.0, tailwindcss 4.3.5, vue-router 5.5.1, @comark/vue 0.9.2, @vueuse/core 14.4.0, zod 4.6.7,
@orpc/contract 1.16.4, axios 1.21.1, eventsource-parser 4.1.3, @tanstack/vue-query 5.108.2,
vue-i18n 11.4.23, typescript 6.0.3, vue-tsc 3.3.14, eslint 10.15.0, eslint-plugin-vue 10.12.1,
prettier 3.10.1, vitest 5.1.1, @vue/test-utils 2.6.0, happy-dom 21.0.4, and, added when the
page was set up, @vue/tsconfig 0.9.1, @types/node 24.19.2, @vue/eslint-config-typescript 14.9.0,
@eslint/js 10.0.1, globals 17.14.0, eslint-config-prettier 10.1.8, @iconify-json/lucide 1.2.158.
None has a known advisory. eslint-config-prettier 10.1.6 and 10.1.7 were published by a hijacked
account with malware in them (GHSA-f29h-pxvx-f335, MAL-2025-6022); 10.1.8 is the clean release
after them, and the lock file must
not hold either of the two.

`npm audit` of the first `package-lock.json` (T006, 2026-11-22) reports five moderate advisories,
all through one test-only chain: @vue/test-utils 2.6.0 → js-beautify 2.0.3 → glob 13.0.7
(GHSA-3g3m-2fjr-6pw4) and editorconfig 3.0.2 → minimatch 10.2.6 (GHSA-g3hv-75wg-m249). Fixed
glob (14.0.2 and later) and minimatch (11.0.1 and later) exist, but js-beautify 2.0.3, its latest
release, asks for glob ^13 and editorconfig ^3, so no released version reaches them. The fixes
wait in `beautifier/js-beautify` pull requests 2561 and 2569; @vue/test-utils pull request 3039
replaces js-beautify altogether. Its maintainers' note on the override they tried (pull request
3012, not merged) says the flawed code is used only by js-beautify's command line, not by the
`beautify.html()` that @vue/test-utils calls. None of this is in the built page; it is installed
for the build and runs only when the page's tests run.

Decision (2026-11-22, the maintainer): keep these versions, as with the embedded PostgreSQL, since
no released version reaches the fixes. No override is added. Each delivery checks again whether
js-beautify or @vue/test-utils has a release that does, and moves to it. The packages they pull in are checked with `npm audit` once `package-lock.json` exists
(T006, and again in T021).

Python dev tool: ast-grep-cli 0.51.3 on PyPI and the `ast-grep` crate it is built from have no
OSV entry (checked 2026-11-22).

Runtime: Node.js 20 left security support on 2026-04-30. The lines that still get security fixes
are 22, 24 and 26, whose latest security releases are 22.23.5, 24.22.3 and 26.13.1
(`nodejs.org/dist/index.json`, the `security` flag; support windows from `endoflife.date`). The
page's build step requires at least the latest security release of one of those lines and says
so by name when the installed Node.js is older (decision 3).

## Decisions

### 0. The data layer

- **Decision**: `frontend/src/service/` in four layers, plus `queries/`:
  - `schema/`: zod schemas, each `.strict()`, the one truth of each shape (programs, the chat
    context and pieces, the error body);
  - `contract/`: the oRPC contract, one route per call (method, path, summary, input and output
    schemas); the request and response types of the API functions are inferred from it; nothing
    calls it at run time;
  - `api/`: one promise function per call, with a short TSDoc; it checks its input with the
    schema, calls `request`, and checks the 2xx response with `parseContract(schema, data)`,
    which throws a `contract_error` when the service's response does not match. The chat
    function returns the stream's events, each checked the same way;
  - `request.ts`: the only transport, one axios instance with axios's fetch adapter, for the JSON
    calls and for the chat stream (`responseType: 'stream'`), so its interceptor and error
    normalisation exist once. It passes the caller's `signal` through and turns every rejected
    response into one `AppError` (`backend`, `network`, `contract`, `unknown`); a cancellation
    is rethrown as it is. The stream request has no client timeout: the service ends an answer
    at its own limit, and the user can stop it;
  - `error.ts`: `AppError`, the error normalisation and `parseContract`;
  - `queries/`: TanStack Query hooks that take the API functions as they are, as `queryFn` or
    `mutationFn`, with the query's `signal`. Query keys come from one key factory. The shared
    client retries only network errors and 5xx, twice, and never refetches on window focus or
    reconnect.
  No store: the page has no client-owned shared state; server state stays in TanStack Query, the
  language and the program in the address, and per-view state in its composables.
- **Rationale**: a response is checked where it enters the page, so a drifted service is an
  error the page shows, never data it draws; the contract keeps one place for each route's
  method, path and types; TanStack Query removes hand-written loading and error flags. The
  service speaks semantic HTTP status codes, so a rejected request is an error without a wrapper.

### 1. The stream the page reads

- **Decision**: `POST /chat/stream` answers with `text/event-stream` through
  `fastapi.sse.EventSourceResponse`. Each item of today's stream (the context, then each piece of
  the answer) is one unnamed event whose `data` is that item's JSON; an error after the stream
  started is one event named `error` whose `data` is `{"message": ...}`; the stream then ends.
  The page reads it through the request module's axios instance with `responseType: 'stream'`:
  axios's fetch adapter supports the `stream` response type (`axios/axios@9f0f4dd:README.md:2502-2524`)
  and returns the response body as it arrives (`lib/adapters/fetch.js:210`). The body goes through
  `eventsource-parser`'s `EventSourceParserStream`
  (`vercel/ai@d55f3cf:packages/provider-utils/src/parse-json-event-stream.ts:22`); each event's
  data is checked against its schema, and an `error` event becomes an `AppError`.
- **Rationale**: FastAPI writes a yielded object as an unnamed event
  (`fastapi/fastapi@b283119:docs_src/server_sent_events/tutorial001.py:22-25`). A browser's
  `EventSource` cannot send a POST with a body, so the stream is read from the POST's response.
  What the endpoint accepts and refuses does not change.

### 2. Markdown

- **Decision**: answers are rendered by `@comark/vue` (`views/chat/components/AnswerMarkdown.ts`,
  made with `defineMarkdownComponent` as in `nuxt-ui-templates/chat-vue@da02783:src/components/chat/Comark.ts:23-34`):
  - `registerDefaultPlugins: false`: plain Markdown only. Comark's default plugins (raw HTML,
    components, attributes, autolinks, alerts, task lists, frontmatter) are off
    (`comark` 0.9.2 `dist/types.d.ts:537-544`), so raw HTML in an answer is shown as text and a
    citation such as `[2]` is not read as an inline component;
  - its security plugin, as a second layer
    (`comarkdown/comark@74ba41b:docs/content/4.plugins/1.built-in/security.md:20`, `:37-52`, the
    fixed sanitising at `:70`): `allowedTags` set to the tags plain Markdown produces, with every
    other tag replaced by its own text through `tagFallback` and `textContent`; `allowedProtocols`
    `https` and `mailto`; `allowedImagePrefixes` empty and `allowDataImages` `false`, so no image
    is loaded from any site.
  `img` is not an allowed tag, so an answer can neither load an image nor name an icon, which
  Nuxt UI would otherwise fetch from the Iconify API. The renderer parses in an async `setup`,
  which renders only under `<Suspense>`; `App.vue` wraps the app in it, as the template does
  (`nuxt-ui-templates/chat-vue@da02783:src/App.vue:17-21`). Sources and the notice are shown as
  plain text.
- **Proved by (T015)**: `tests/views/chat/hostile.spec.ts` streams an answer and sources holding
  the attacks of spec User Story 2 and more (an image with an error handler, a script, a
  `javascript:` and a `data:` link, an iframe, an object, an embed, a stylesheet link, a style
  block, an inline style with `url()`, a Markdown image from another site and a data image, an
  `<a onclick>`, a component name): no dialog opens, `fetch` is never called, no executable or
  loading element and no `on*` or `style` attribute is in the answer, the sources or the notice,
  and the only link left is the `https` one. A real run in the browser is still due (T022).

### 3. Building and serving the page

- **Decision**: `frontend/` holds the page's source and its `package-lock.json`. On
  `uv run chat-bridge` with no other command, the service checks for Node.js; when the built page
  is missing or the page's sources changed since the last build, it runs `npm run build`, and
  before it `npm install --ignore-scripts` when `node_modules` is missing or `package-lock.json`
  changed since the last install (`reflex-dev/reflex@df7f157:reflex/utils/js_runtimes.py:818`
  installs the same way). `install` updates `node_modules` in place: `npm ci` deletes it first,
  and on Windows that fails while any program has one of its native modules loaded, which
  happened on the first real start. Install scripts stay off, as the packages were checked with
  them off (refusing install scripts: `vuejs/test-utils@6588ec8:pnpm-workspace.yaml:8-9`). The
  service then serves `frontend/dist` (git-ignored) at `/`, with unknown paths
  answered by `index.html` so the address can hold state. A missing Node.js, or one older than
  the latest security release of a supported line (## Advisories), is reported by name with the
  version to install.
- **Rationale**: the maintainer's rule is one command on a machine with Python and Node.js, with
  no page built in advance. Serving a Vite build from FastAPI follows the retrieval template
  (`frontend_routes.py:4`, `:11`, `:22`); building on the user's machine follows Reflex.
  Answering every other address with `index.html` is the server fallback that vue-router's
  history mode asks for ("If the URL doesn't match any static assets, it should serve the same
  `index.html` page", router.vuejs.org/guide/essentials/history-mode, read 2026-11-22). A path
  that leads out of the build gets the page, not the file.

- **Starting, as a person runs it (added after the first real start, 2026-11-22)**: before the
  service starts, the command ingests `data/truth` when nothing has been ingested, so a fresh
  clone can answer with no other command; a database made by another version is not deleted,
  since it also holds the question records, and the error names what to delete. It checks that
  port 8000 can be bound and, when it cannot, says whether chat-bridge is already running there
  (and opens that page) or another program holds it, as Reflex checks a port before it starts
  (`reflex-dev/reflex@df7f157:reflex/utils/processes.py:66-90`, `:133-180`). It prints where
  the page is and opens it in the default browser once the service accepts connections, as
  Streamlit does when its server starts (`streamlit/streamlit@259fbb6:lib/streamlit/web/bootstrap.py:169-194`);
  `--no-browser` turns that off.

### 4. The login screen

- **Decision**: the page reads `GET /chat/programs` through a query before anything else; the
  shared client does not refetch on window focus or reconnect and the query has no interval, so
  only the button refetches. With neither program logged in, a Nuxt UI empty state lists each
  program with its state and next step and the button
  (`nuxt/ui@422d015:docs/content/docs/2.components/empty.md:25`, `:104`). A login command is
  copied with `useClipboard`. A failed query shows the same screen with "the service cannot be
  reached".
- **Rationale**: spec User Story 0. Asking again only when the user presses the button is what
  the maintainer asked for.

### 5. Layout

- **Decision**: `views/chat/` is the one page: one `UDashboardGroup` with the chat panel as the
  main one and a resizable strategy panel beside it
  (`nuxt/ui@422d015:docs/content/docs/2.components/dashboard-panel.md:25`, `:60`); in a narrow
  window the strategy panel moves into a `USlideover`. Until feature 006 exists, the strategy
  panel says that the strategy screen comes in a later step. The chat uses `UChatMessages` with
  plain message objects and a `status` (`chat-messages.md:13`, `:39-71`, `:80`) and
  `UChatPrompt`, which does not send twice while an answer streams (`chat-prompt.md:29`).
  Components emit to the page; they do not call the API.

### 6. Texts and address

- **Decision**: page texts live in `vue-i18n` messages for `zh-TW` and `en`, keys at most three
  levels; the language and the chosen program are query parameters of the address, read and
  written by one composable (the user's choice is a `push`; a correction to a valid value is a
  `replace`). Sample questions are part of the messages, so they follow the language.

## Real runs (with the maintainer's consent)

1. The Fed question from the page, with each logged-in program (SC-001, SC-002).
2. The hostile test document from the page (SC-003).
3. The login screen with neither program logged in, then one logged in and the button pressed (SC-007). This needs logging a program out on the maintainer's machine; it is asked for separately.
