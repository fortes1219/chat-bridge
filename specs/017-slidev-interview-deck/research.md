# Research: Bilingual interview deck

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Compile a Markdown presentation per public base path | @slidev/cli | 53.1.0 | MIT | 338 KB unpacked | `antfu/talks@d759559:package.json:19` | `antfu/talks@d759559:scripts/build.ts:38` |
| Supply the standard Slidev layout and export baseline | @slidev/theme-default | 0.25.0 | MIT | 36 KB unpacked | `antfu/talks@d759559:package.json:21` | `slidevjs/slidev@437f139:packages/slidev/node/options.ts:41` |
| Read slide frontmatter with the same parser as the build | @slidev/parser | 53.1.0 | MIT | 34 KB unpacked | `slidevjs/slidev@437f139:packages/slidev/package.json:70` | `slidevjs/slidev@437f139:packages/slidev/node/options.ts:25` |
| Render shared typed components from the slide layout | vue | 3.5.46 | MIT | 2.64 MB unpacked | `Tresjs/cientos@8362924:package.json:62` | `Tresjs/cientos@8362924:src/core/controls/OrbitControls.vue:6` |
| Mount a local WebGL scene from a Vue component | @tresjs/core | 5.12.0 | MIT | 219 KB unpacked | `Tresjs/cientos@8362924:package.json:60` | `Tresjs/cientos@8362924:src/core/controls/OrbitControls.vue:2` |
| Supply the Three.js renderer and scene primitives | three | 0.187.0 | MIT | 21.0 MB unpacked | `Tresjs/cientos@8362924:package.json:61` | `Tresjs/cientos@8362924:src/core/controls/OrbitControls.vue:4` |

## Advisories

OSV returned no advisories for the six exact direct versions on 2026-11-26. The official Node.js release index listed 24.22.3 as the latest Node 24 release on that date. The resolved npm lockfile is subject to a delivery audit.

The initial npm resolution selected DOMPurify 3.4.15 through Monaco and image-size 1.2.1 through PptxGenJS. The lockfile overrides these to 3.5.0 and 2.1.0 respectively. Neither fixed version returned an OSV result. A clean lockfile resolution and installation reported zero npm audit advisories.

## Decisions

- Two builds retain a stable link per language while sharing the layout, data and effects.
- `slideId` is stable across language and ordering. The strategy table owns the effects. Slidev's frontmatter context provides the ID at render time.
- Draw the retrieval experiment as a schematic, with an equivalent text view. The coordinates are illustrative. Do not expose private material or present the proposal example as financial advice.
- Use a manually triggered Pages workflow. The site uses relative language URLs and repository settings own the custom domain.

## Redesign references

- Compare the official [Seriph, Apple Basic and Bricks themes](https://github.com/slidevjs/themes) for editorial typography, sparse cover layouts and colored sections. The deck borrows their layout ideas and keeps its stylesheet and assets local.
- Use single-metric, comparison and steps compositions inspired by the [Tahta layout catalog](https://github.com/zcag/tahta). Shared Vue components still own the effects, localization and numerical data.
- The [Three.js voxel painter](https://threejs.org/examples/webgl_interactive_voxelpainter.html) shows a ground plane and spatial cells. The [dynamic geometry example](https://threejs.org/examples/webgl_instancing_dynamic.html) shows repeated solid geometry in motion. The evidence board uses separate lanes, solid slots and a camera move to explain the demo's 0/9 to 7/9 change.

## Step effects

- [Slidev's absolute click positions](https://sli.dev/guide/animations#absolute-position) anchor each effect timeline in the layout. The two language entries share those positions through their slide IDs.
- [Vue TransitionGroup](https://vuejs.org/guide/built-ins/transition-group.html) animates the RRF example's stable passage keys when the order changes. The sample ranks are illustrative. The scoring formula follows the search service.
- [ECharts' delayed bar animation](https://echarts.apache.org/examples/en/editor.html?c=bar-animation-delay) informed the staged recall comparison. The figure uses exact labels and Vue-rendered bars.
- [Vue Flow's animated edges](https://vueflow.dev/examples/edges/animating-edges) informed the transport lanes. The fixed diagram uses Vue events and CSS motion. The existing packages cover the effects.
