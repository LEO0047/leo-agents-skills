# OpenAI Image Asset Workflow

Use this reference after the base frontend direction is known and before making image-generation calls.

## Asset manifest template

```markdown
| id | role | display_size | interactive | recolorable | backgrounds | semantics | medium | reason |
|---|---|---|---|---|---|---|---|---|
| onboarding-orbit | empty state | 240–360px | no | no | light + dark | meaningful: "No projects yet" | generated-raster | A distinctive product-world illustration communicates the empty state. |
| close-dialog | control icon | 20px | yes | yes | mixed | decorative; button has an accessible name | vector | It must remain crisp, themeable, and state-aware. |
| workspace-category | category icon | 64px | yes | no | light + dark | meaningful: category name | compare | Branding may benefit from generated material, but small-size legibility must win. |
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

## Generation prompt pattern

```text
A single [asset subject] for [specific product and UI role].
Visual language: [product-specific materials, shapes, palette, lighting, perspective].
It will be displayed at approximately [target CSS size] on [light/dark/mixed] UI surfaces.
Isolated and centered with generous clear padding; preserve the complete silhouette; no crop.
One subject only. No background, frame, card, mock interface, watermark, logo, text, or extra objects.
No cast shadow outside the subject unless explicitly required by the component.
Transparent-background PNG with clean antialiased edges and no white or dark matte.
```

Do not ask the model to reproduce essential UI labels. HTML text remains sharper, localizable, selectable, accessible, and easier to update.

## One-pass background-removal edit

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

## Failure states

- **Native image tool unavailable:** report the blocker; do not silently route to RunComfy.
- **No local file returned:** report that the asset cannot yet be integrated; do not invent a path.
- **Transparency fails after one edit:** choose the vector candidate or mark the asset `Provisional` with the exact failed check.
- **Generated detail fails at target size:** prefer the vector candidate even if the master image looks more attractive when enlarged.
- **Generated art implies nonexistent capability or data:** reject it; visual polish cannot invent product truth.
