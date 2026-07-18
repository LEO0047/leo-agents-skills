# OpenAI Narrative Image Workflow

Use this reference after the base frontend direction and narrative image plan are known and before making image-generation calls. It covers coordinated website backgrounds and scenes as well as isolated assets.

## Site-wide visual bible

Write one compact shared prompt block before individual image prompts:

```text
Website promise: [single product or brand idea the journey must make believable].
Audience and desired action: [who, what they need, and the conversion].
Emotional arc: [opening feeling → evidence/trust → final action].
Visual world: [palette, materials, environment, lighting direction, camera language, depth, texture].
Signature motif: [one recurring form, object, light, or framing device].
Continuity rules: [what must remain consistent across hero, sections, and footer].
Forbidden elements: [styles, objects, text, UI, or visual clichés that would break the product truth].
```

Reuse this block in every relevant prompt, then add the section-specific narrative job and composition. Continuity should come from shared visual decisions, not from repeating the same image.

## Asset manifest template

```markdown
| id | role | display_size | interactive | recolorable | backgrounds | semantics | medium | section_job | text_safe_area | continuity | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hero-environment | background scene | 1440×900 → mobile crop | no | no | self | decorative | generated-raster | establish promise and visual world | left 42% quiet for heading and CTA | shared light and material motif begins here | Environmental storytelling makes the product promise tangible. |
| onboarding-orbit | empty state | 240–360px | no | no | light + dark | meaningful: "No projects yet" | generated-raster | explain the empty state | none | reuse the hero's material and light direction | A distinctive product-world illustration communicates the empty state. |
| close-dialog | control icon | 20px | yes | yes | mixed | decorative; button has an accessible name | vector | dismiss dialog | none | standard control styling | It must remain crisp, themeable, and state-aware. |
| workspace-category | category icon | 64px | yes | no | light + dark | meaningful: category name | compare | help category recognition | none | reuse restrained signature motif | Branding may benefit from generated material, but small-size legibility must win. |
```

Keep only assets that have a real product role. Do not generate decorative filler merely because image generation is available.

## Medium decision guide

Choose `vector` when most of these are true:

- The asset is a familiar functional symbol.
- It appears around `12–32px`.
- It needs `currentColor`, theme recoloring, stroke changes, or multiple interaction states.
- Pixel alignment, instant loading, or CSS animation matters more than material richness.

Choose `generated-raster` when most of these are true:

- Material, lighting, character, depth, atmosphere, or worldbuilding carries product meaning.
- The asset is a hero, mascot, empty state, card art, branded spot illustration, texture, or product mockup.
- It is large enough for generated detail to survive rendering.
- It does not need arbitrary recoloring or shape morphing.

Choose `compare` when the asset is branded and medium-sized, especially around `32–96px`, and neither medium is an obvious winner. Comparison is a visual QA step, not a requirement to duplicate every asset.

## Background-scene prompt pattern

```text
A [hero/section/footer] environmental scene for [specific website and section job].
Narrative purpose: [what the visitor should understand or feel here] and how it advances toward [conversion].
Continue the shared visual bible: [materials, palette, lighting direction, camera language, signature motif].
Composition: target [aspect ratio and viewport], focal subject in [region], quiet text-safe region in [region] for real HTML [heading/copy/CTA].
Responsive crop tolerance: preserve [essential subject or horizon] across desktop and narrow mobile crops; keep critical detail away from fragile edges.
Relationship to adjacent sections: [visual transition entering and leaving this scene].
No text, letters, logos, watermark, mock UI, fake controls, fake data, or decorative elements that imply nonexistent functionality.
The environment and background are intentional; do not use chroma key or transparency.
```

Generate backgrounds as compositional partners for real HTML, not as complete poster designs. The page owns typography, controls, localization, accessibility, and final contrast treatment.

## Isolated-object prompt pattern

```text
A single [asset subject] for [specific product and UI role].
Visual language: [product-specific materials, shapes, palette, lighting, perspective].
It will be displayed at approximately [target CSS size] on [light/dark/mixed] UI surfaces.
Isolated and centered with generous clear padding; preserve the complete silhouette; no crop.
One subject only. No background, frame, card, mock interface, watermark, logo, text, or extra objects.
No cast shadow outside the subject unless explicitly required by the component.
One perfectly uniform chroma-key background outside the subject palette—pure green or pure blue—with the exact key color recorded before generation. No white, gray, checkerboard, gradient, floor, cast shadow, or environmental background. Preserve clean antialiased subject edges and generous clear padding.
```

Do not ask the model to reproduce essential UI labels. HTML text remains sharper, localizable, selectable, accessible, and easier to update.

Chroma-key generation is the default for isolated assets. Choose a key color absent from the subject and record it before generation. Prefer pure green when the subject has no green or yellow-green detail; prefer pure blue when it has no blue or cyan detail. If both conflict, choose another single saturated hue with strong color distance. Keep the background perfectly uniform with no lighting falloff or shadow. Use direct transparent generation only after the active generator has demonstrated reliable real-alpha output.

## Section-sequence continuity

Before generating multiple images, list the page sequence in order and assign each section one job. Check that:

- The opening establishes the visual world and promise.
- Middle sections provide proof, process, differentiation, or trust rather than repeating another hero shot.
- Lighting, materials, horizon, camera distance, or the signature motif create a deliberate transition between neighboring sections.
- Visual intensity leaves enough quiet space around dense copy and becomes stronger only where hierarchy benefits.
- The final scene supports the CTA and feels like the conclusion of the same journey.

Do not generate every section independently with unrelated prompts. Reuse the visual bible and explicitly state what changes from the previous image.

## Automatic local matting

When a generated PNG is opaque or contains a baked checkerboard or simple background, run the bundled macOS Vision matting script automatically:

```bash
scripts/remove-image-background.swift input.png output-transparent.png
scripts/inspect-image-asset.sh --require-alpha output-transparent.png
```

Keep `input.png` unchanged and always write a new output file. Local matting requires no additional confirmation once this skill is active. Do not install image-processing dependencies or use a third-party removal service. Inspect the transparent output on checkerboard, light, and dark surfaces at both master and target sizes before integration.

The script accepts an optional final `trim-radius` from `0` through `24` pixels when a baked white or dark fringe remains. Keep the default `3` first, then increase only when visual inspection proves the source contains a wider matte:

```bash
scripts/remove-image-background.swift input.png output-transparent.png 8
```

## One-pass native background-removal edit

Use a native image edit only when local foreground matting cannot separate the subject from a materially ambiguous background.

Use the generated asset as the sole local reference and request:

```text
Keep the subject, silhouette, materials, colors, lighting, perspective, scale, padding, and composition unchanged.
Remove only the background and any white or dark edge matte. Do not redraw, restyle, add objects, add text, crop, or change the subject.
Return a transparent-background PNG with clean antialiased edges.
```

Only one such edit is allowed by default. Repeated edits tend to drift identity and consume time without proving that the asset is improving.

## Alpha and edge QA

Run:

```bash
scripts/inspect-image-asset.sh --require-alpha path/to/asset.png
```

Then place the asset in a temporary preview with three tiles:

1. Checkerboard to expose opaque pixels.
2. Near-white background to expose dark halos.
3. Near-black background to expose light halos.

Inspect the actual rendered target size as well as the master. Reject assets with clipped silhouettes, accidental shadows, fringe pixels, internal transparency holes, unreadable detail, or composition that collapses at the intended CSS size.

## Candidate comparison

- Create a task-specific temporary directory with `mktemp -d`; do not use a broad shared path or the repo root.
- Keep generated and vector candidates under distinct filenames.
- Render both in the real component with the same dimensions, padding, background, and surrounding content.
- Compare product specificity, visual hierarchy, target-size clarity, edge quality, theme compatibility, interaction-state needs, and loading cost.
- Let the agent choose and record one sentence of rationale. Escalate only if the candidates remain materially tied after in-context inspection.
- Copy only the accepted candidate into the repo. Leave rejected candidates in temporary storage rather than deleting or filing them as product assets.

## Integration checklist

- Follow existing asset naming and directory conventions.
- Preserve a transparent PNG master when alpha is required.
- Set intrinsic width and height to prevent layout shift.
- Configure responsive sizing and object positioning deliberately.
- Lazy-load below-the-fold art; follow the repo's established priority strategy for LCP imagery.
- Use empty alt text for decoration and concise functional alt text for meaningful imagery.
- Verify desktop, mobile, light, and dark contexts.
- Preserve accessible HTML controls and labels even when imagery surrounds them.

## Implemented-page screenshot loop

The required review target is the rendered website, not the generated source image:

1. Serve the actual project locally through its normal development or preview command.
2. Wait for fonts and generated images to load, then capture a representative desktop viewport.
3. Capture a narrow mobile viewport and, when narrative progression matters, a full-page or ordered set of section screenshots.
4. Inspect content and imagery together for text-safe areas, contrast, visual focus, repeated motifs, background continuity, CTA visibility, crop, first-load animation, and horizontal overflow.
5. Make one focused correction to the prompt, asset selection, overlay, layout, crop, scale, or responsive positioning.
6. Recapture the affected viewport and keep only the final QA screenshots as reported artifacts unless comparison evidence is useful. Display the final desktop and mobile captures in the response when supported; otherwise return their clickable local paths.

Never retouch the screenshot to conceal an implementation defect. Correct the website or source asset, then capture it again.

## Proven hero replacement QA

When a generated raster replaces a CSS glyph, outlined numeral, SVG, or other placeholder, do not assume the old geometry remains valid:

1. Load the page from a local HTTP server and wait for the actual image to complete.
2. Confirm `naturalWidth`, `naturalHeight`, and the rendered bounding box rather than judging only the CSS container.
3. Inspect one desktop viewport and one narrow mobile viewport after reload. Tall transparent assets commonly extend beyond a square wrapper and need a different mobile offset.
4. Check heading, introductory copy, CTA, status-row, ticker, and following-section bounds for collision.
5. Check `document.documentElement.scrollWidth` against the viewport width and inspect browser console errors.
6. Make one focused positioning correction, then repeat the same viewport checks.

For detailed subjects, compare the matted output on light and dark backgrounds before integration. Preserve internal neon strips, hardware gaps, dark recesses, and material edges; a valid alpha channel and clean outer contour do not prove those details survived.

## Failure states

- **Native image tool unavailable:** report the blocker; do not silently route to RunComfy.
- **No local file returned:** report that the asset cannot yet be integrated; do not invent a path.
- **Local matting and one native edit both fail:** choose the vector candidate or mark the asset `Provisional` with the exact failed check.
- **Generated detail fails at target size:** prefer the vector candidate even if the master image looks more attractive when enlarged.
- **Generated art implies nonexistent capability or data:** reject it; visual polish cannot invent product truth.
