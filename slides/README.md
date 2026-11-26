# chat-bridge presentations

Use Node.js 24.22.3 or a later security release in the Node.js 24 line.

```sh
npm ci --ignore-scripts
npm run dev
npm run dev:en
npm run build
```

Run these commands from this directory. The production artifact is `dist/`, with Traditional Chinese at `/` and English at `/en/`. Build both decks together to exercise the language links. The repository's manual **Deploy slides** workflow builds and uploads that directory. Configure the public hostname in GitHub Pages settings.

## Add a slide or effect

1. Add a stable `slideId` to both language decks and use the `research` layout.
2. Add an entry to `effects/strategies.ts`. Text-only slides select `none`.
3. Register new effect components in `effects/registry.ts`. Give each component a static view with the same information and keep localized labels with the component. Use `effects/data.ts` for shared figures and examples.
4. Set the effect's click count in `effects/strategies.ts`. Slidev's next and previous actions move through those steps. For effects with buttons, the buttons select the same Slidev steps.
5. Run `npm run check` or build both decks. Missing, unknown or duplicate IDs and unrecognized strategies fail validation.

The deck uses an illustrative allocation, a schematic retrieval view and historical evaluation figures.
