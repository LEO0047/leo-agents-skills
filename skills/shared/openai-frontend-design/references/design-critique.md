# Design critique

How to look at a generated element and at the built page. Judge everything in its real context at rendered size; beauty in an isolated source image says little about the page.

## Result states

| State | Meaning |
|---|---|
| `pass` | Fits the direction, reads well at rendered size, evidence was inspected |
| `correctable` | The subject is right; a bounded prompt, crop, overlay, layout, or CSS change resolves the issue |
| `regenerate` | Subject, geometry, lighting, reference transfer, or composition is wrong at the root |
| `fallback` | A vector, CSS, static image, or simpler direction serves the page better |

Labels for claims: `已驗證` for checks completed this turn, `Observed` for inspected evidence without end-to-end proof, `Provisional` for a promising but unresolved result, `Uncertainty` for evidence you could not obtain, `未執行` for checks not run.

## Looking at an element

- Does it belong to the direction's world: same medium, light, edge quality, color density, and level of detail as its neighbors? A set of elements that look like five different prompts is the most common failure.
- Does it do a job in its section: set the mood, explain, reward the eye at a pause, or carry the story forward? Decoration with no job is cut.
- At rendered size, are the edges clean, the silhouette complete, the internal gaps free of key color, the fine hardware intact? Check on near-white, near-black, and checkerboard with the contact sheet; a defect that shows only at master size is noted, one that shows at rendered size is fixed.
- Is the alpha real? `sips -g hasAlpha` says `yes`, or the checkerboard is baked pixels.
- Realism-critical subjects: construction that could stand, gravity that holds, light with a source, scale cues, ordinary wear. Fake glyphs, illegible signage, arbitrary cables, uniform glow, and collectible-render symmetry are signs of a prompt that described a style instead of a thing.
- Reference transfer: the visual language came over; people, faces, logos, text, UI, and unrelated objects did not.

## Looking at the page

Capture after fonts, images, and initial transitions settle: a representative desktop viewport, a narrow mobile viewport, and full-page or first-load and scrolled states when reveal, sticky, or intrinsic-media behavior can change geometry.

- One world: the illustrations, type, color, and spacing read as one design. The signature element is the one bold move; everything around it is quiet.
- Hierarchy: the eye lands where the page needs it first. Headings, copy, and calls to action sit in the text-safe regions the direction reserved; an illustration never competes with the words it supports.
- Type: display and body faces are the ones the direction chose, set with intent. Fixed line groups and CJK wrappers hold at both viewports after a cold-style reload.
- Mobile crop: the illustration keeps its meaning when cropped; critical detail stays away from fragile edges; no horizontal overflow, clipping, or overlap.
- Contrast and states: text over imagery stays readable; focus is visible; hover, loading, and empty states that the surface needs are designed, and none are added for their own sake.
- Motion: one grammar, a few transitions that matter, and a reduced-motion route that keeps the hierarchy. Extra animation reads as AI-generated.
- Product truth: no fake data, fake controls, or implied features. Real copy lives in HTML with correct semantics and alt text (`alt=""` for decorative imagery).

Correct the source, the asset, or the layout, then recapture. A screenshot is never retouched.

## Safari and CJK notes from practice

Large CJK display type that fits a full-width hero can overflow a narrow grid column: size headings against the rendered column, wrap approved line groups explicitly, and apply `white-space: nowrap` only after responsive sizing proves the group fits. WebKit can reveal hidden labels when fixed descendants sit inside sticky, transformed, filtered, or backdrop-filtered ancestors: keep persistent accessible labels on a dedicated visually-hidden utility (not a focus-revealed skip-link class), keep the skip link at the document root, and inspect sticky toolbars after scrolling. When the browser tool is Chromium-only, a required Safari check is reported `未執行`.

## Delivery checklist

- The direction document, and what changed after the checkpoint.
- Per element: state, alpha route taken, and any assumption the generator reported.
- The contact sheet path.
- Desktop and mobile screenshots, plus any full-page, first-load, scrolled, or CJK captures taken.
- The critique pass: what you found and what you changed.
- Lint, typecheck, test, or build results where the repo has them.
- Every `Provisional`, `Uncertainty`, and `未執行` item, stated plainly.
