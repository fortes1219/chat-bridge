# Implementation Plan: Bilingual interview deck

Use a standalone npm project under `slides/`. A custom Slidev layout reads the active slide's frontmatter and passes its ID to an effect host. The host loads a registered Vue component. Each component owns its animation and static representation. Retrieval and proposal examples are shared and localized at render time.

Use distinct page compositions for a question, a case, an explanation, an experiment and a comparison. Hold the bilingual page order in sync. Use the existing Three.js and TresJS dependencies to render the three evidence platforms, the camera move and the staged reveal.

Attach the six effects through the existing strategy registry. Register the final click position in the shared layout and give each effect the current click number. Render explanatory diagrams in Vue and CSS, and use the retrieval scene for both the baseline and the comparison.

Use the Slidev parser for build-time checks of both Markdown entries. Build them separately under their respective base paths into one publishable directory. Use hash routes so numbered Slidev links can be opened on a static host.

The feature contains the decks, components, shared examples, validation and build commands, and an explicitly triggered Pages workflow. Use public-safe prose and illustrative holdings. The portfolio app, private material and account settings are outside this feature.
