# Tasks: Bilingual interview deck

- [x] Create both decks and the shared effect strategy, examples and custom layout.
- [x] Add contract validation, pinned dependencies, and a bilingual production build.
- [x] Inspect both decks, exercise the contract and static fallbacks, and audit the lockfile.
- [x] Prepare the changed files and a suggested commit message for the maintainer.

## Verification

- A clean `npm ci --ignore-scripts` completed. The redesigned decks pass `npm run build` and the 16-slide contract check in both locales.
- Negative checks rejected a missing ID, duplicate ID, unregistered ID, mismatched deck, effect declared in a slide and invalid example key.
- Local Chrome rendered all 32 slide views. The retrieval scene changed from 0/9 to 7/9 in both languages. Reduced-motion, unavailable-WebGL and both print views used the static rendering.
- Comparing canvas captures confirmed the camera moves before input and seven rate-policy slots rise after selecting split queries. Visual review shortened dense English table and evaluation copy before the last pass.
- The effect pass exercised all six new timelines by keyboard in both locales, including reverse steps. It also verified direct controls, the shared 3D baseline and recovery states, the Socket.IO marker's movement, and complete print and reduced-motion content.
- The contract check rejected an inline click override and an unrecognized retrieval view.
- The cover pass checked the full-bleed illustration, bilingual heading layout, and start links in Chrome. Both print covers displayed the illustration with the animation and start control suppressed. The 32 slide views also passed the regression pass.
- `npm audit --audit-level=low` reported zero advisories after resolving the indirect dependencies recorded in the research.
- GitHub Actions dispatch and the public endpoint remain unverified. The maintainer owns the commit and publish decision.
