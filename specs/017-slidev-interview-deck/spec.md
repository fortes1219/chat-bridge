# Feature 017: Bilingual interview deck

The maintainer can share a Chinese or an English presentation of chat-bridge. Each version presents the same product, retrieval evaluation and model boundaries. The deck is a standalone Slidev project.

- Open with the portfolio holder's question. Give document preparation, hybrid ranking, the retrieval failure, evaluation, alternatives, model governance and the portfolio workflow their own slides.
- Each slide declares a semantic `slideId`. Both decks use the same set of IDs.
- A shared map selects one registered effect and any approved example data for each ID. A text-only slide explicitly selects `none`.
- The cover shows an example question, its evidence and the proposal as layered panels. The interactive retrieval slide shows three sets of evidence on separate platforms. The camera moves toward the missing topic and seven of the nine rate-policy slots rise in sequence when the viewer selects split queries. The proposal slide shows the current and proposed weights in an illustrative portfolio.
- Page 5 reveals searchable passages and the attached market table. Page 6 combines two rankings and shows one RRF calculation. Pages 7 and 8 share the same scene and carry its camera position from the missed topic to the recovered sources.
- Page 9 shows the before and after recall with counts and denominators. Page 10 reveals the results and costs of the three retrieval approaches. Page 14 animates the chat response and quote update on separate paths.
- The shared effect, rather than the Markdown entry, owns the number of steps. Forward and backward navigation update the effect state. Any on-slide controls update the same Slidev step.
- Interactive views use the effect components. Static contexts, reduced motion and unavailable WebGL show the same evidence without motion.
- A build refuses absent or duplicate IDs, mismatched decks, unmapped IDs and invalid strategies. The error names the affected ID or file.
- The site builds to `slides/dist`, with Chinese at `/` and English at `/en/`. The maintainer controls public submission and deployment.
