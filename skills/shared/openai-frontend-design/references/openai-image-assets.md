# OpenAI Narrative Image Asset Workflow

Use this reference after the Visual Genome and page narrative are defined and before making image-generation calls. It covers coordinated environments, integrated heroes, textures, and isolated assets. The rendered website remains the acceptance target.

## Shared visual bible

Write one compact shared block before asset-specific prompts:

```text
Website promise: [single product or brand idea the journey must make believable].
Audience and desired action: [who, what they need, and the conversion].
Emotional arc: [opening feeling -> evidence/trust -> final action].
Visual Genome: [physical world; graphic language; display medium; motion grammar; primary/supporting image transformation].
Realism mode: [documentary, commercial photography, architectural editorial, high-end photoreal CG, or another explicit finish].
Physical-world thesis: [what exists, how it is built and supported, scale evidence, wear, and practical light].
Signature motif: [one recurring form, object, light, or framing device].
Continuity rules: [what remains consistent across sections and what deliberately changes].
Copy constraints: [approved wording, punctuation, fixed line groups, and no-orphan behavior].
Forbidden elements: [bundle reuse, transfers, fake UI/data, effects, or clichés that break product truth].
```

Reuse the block across related prompts, then add the section job and composition. Continuity comes from shared decisions, not repeated near-identical images.

## Reference hierarchy

Classify every supplied image before generation:

1. `primary-anchor`: strongest approved finish and compositional preference;
2. `secondary-anchor`: supporting environment, scale, or presentation language;
3. `supporting-reference`: one explicitly named transferable property;
4. `negative-reference`: failures that become forbidden elements.

Use local references through `referenced_image_paths` when the native tool supports them. State that they are visual-language references only. Do not transfer people, faces, bodies, costumes, logos, labels, text, measurements, social-media UI, layout, or unrelated objects unless separately requested and appropriate.

Extract only relevant signals: realism mode, contrast, black level, highlight roll-off, color temperature, material response, wear, camera distance, lens feel, framing, depth, practical light, atmosphere, and the boundary between realism and stylization.

## Asset manifest

Record one row per planned visual:

| Field | Meaning |
|---|---|
| `id` | Stable purpose-led identifier |
| `role` | Background scene, integrated hero, isolated object, transition, empty state, card art, texture, control icon, or another real UI role |
| `display_size` | Intended CSS size or responsive range |
| `interactive` | Whether it represents or changes state |
| `recolorable` | Whether theme or CSS recoloring is required |
| `backgrounds` | Light, dark, mixed, image, self-contained, or transparent surfaces |
| `section_job` | Narrative or conversion purpose |
| `text_safe_area` | Quiet region for real HTML at desktop and mobile |
| `continuity` | Motif, light, material, camera, or transition shared with neighbors |
| `semantics` | Meaningful with concise alt text, or decorative with empty alt text |
| `medium` | `vector`, `generated-raster`, or `compare` |
| `reason` | Why that medium fits the product |
| `key_color` | `none`, `green`, `blue`, or `magenta` for an isolated generated subject |
| `status` | `planned`, `pass`, `correctable`, `regenerate`, or `fallback` |

Do not generate decorative filler without a UI, narrative, or conversion role.

## Choose the medium deliberately

Choose `vector` or existing CSS/icon-library assets when the element is a familiar functional symbol, appears around `12-32px`, needs `currentColor`, multiple states, exact alignment, keyboard clarity, or theme recoloring.

Choose `generated-raster` when material, lighting, character, atmosphere, or worldbuilding carries real meaning and the asset is large enough for that information to survive rendering. Appropriate roles include environments, integrated heroes, section transitions, mascots, empty states, branded illustrations, textures, and product mockups.

Choose `compare` for a branded element, usually around `32-96px`, when neither route is clearly superior. Place candidates in a task-specific directory created with `mktemp -d`, render them in the real component at target sizes and backgrounds, and compare product specificity, clarity, edges, theming, state needs, semantics, and loading cost. Copy only the accepted candidate into the repo.

## Prompt compiler

For reference-led generation, assemble the prompt in this order:

1. `reference hierarchy`: identify primary, secondary, supporting, and negative references; visual language only;
2. `section job`: exact section, narrative purpose, CSS size, and conversion contribution;
3. `Visual Genome`: only the selected physical world, graphic language, local display treatment, and image transformation relevant to this asset;
4. `physical subject`: construction, support, gravity, scale cues, hardware, seams, routing, ventilation, wear, and use;
5. `surface and practical light`: material response, black/highlight behavior, motivated fixtures, and restrained accents;
6. `camera and composition`: aspect ratio, lens feel, height, focal region, text-safe region, and desktop/mobile crop tolerance;
7. `relationship to adjacent sections`: what continues and what changes;
8. `forbidden transfer`: people, identity, logos, text, measurements, UI, symbols, layouts, and unrelated objects;
9. `anti-AI rejection`: the subject-specific geometry, light, repetition, fake-text, and material failures that require rejection.

Do not use a generic style label such as `cyberpunk`, `Apple-like`, or `cinematic lighting` in place of physical, graphic, camera, and UI decisions.

## Role-specific prompting

### Background scene or integrated hero

```text
A [hero/section/footer] environmental scene for [specific website and section job].
Narrative purpose: [what the visitor understands or feels] and how it advances toward [conversion].
Visual Genome: [only the selected axes relevant to this scene].
Physical world: [buildable environment, subject, support, material, use evidence, and practical light].
Composition: target [aspect ratio and viewport], focal subject in [region], quiet text-safe region in [region] for real HTML [heading/copy/CTA].
Responsive crop: preserve [essential subject or horizon] across desktop and narrow mobile; keep critical detail away from fragile edges.
Continuity: [visual transition entering and leaving this scene].
No text, letters, logos, watermark, mock UI, fake controls, fake data, or decorative elements that imply nonexistent functionality.
The environment is intentional; do not use chroma key or transparency.
```

### Isolated object

Choose exactly one key color absent from the complete subject palette: pure green `#00FF00`, pure blue `#0000FF`, or pure magenta `#FF00FF`. Record it before generation.

```text
A single [asset subject] for [specific product and UI role].
Visual language: [product-specific material, shape, restrained palette, practical light, and perspective].
Target: approximately [CSS size] on [light/dark/mixed] UI surfaces.
Isolated and centered with generous clear padding; complete silhouette; no crop.
One subject only. No frame, card, mock interface, watermark, logo, text, floor, environment, or extra objects.
No cast shadow outside the subject unless the component explicitly requires one.
One perfectly uniform [green #00FF00 / blue #0000FF / magenta #FF00FF] background absent from the subject. No checkerboard, gradient, lighting falloff, studio sweep, or shadow on the key.
Preserve antialiased edges, fine hardware, internal gaps, and generous padding.
```

Direct transparent generation is a secondary route only after the current tool has demonstrated reliable real-alpha output. A visible checkerboard is ordinary baked pixels unless metadata proves alpha.

### Texture

Specify whether the texture tiles, its maximum usable contrast, intended surfaces, scale, transformation, and the content it must not compete with. A texture must derive from real product geometry, material, data, or brand structure rather than generic noise.

## Native image generation

Script paths below are relative to the skill directory; set `SKILL_DIR` once per session to wherever this skill is installed (`~/.claude/skills/openai-frontend-design` or `~/.codex/skills/openai-frontend-design`).

**On Codex (native tool)** — for a new asset, call `image_gen__imagegen` with the complete prompt and omit reference-image parameters. For an edit, inspect the local source with `view_image`, then pass only the required local paths through `referenced_image_paths`. Never provide both local paths and conversation-image references.

**On Claude Code (delegated route)** — generation runs through `scripts/codex-generate-image.sh`, which delegates one non-interactive turn to the bundled Codex CLI and its native `image_gen__imagegen` tool. Write the complete prompt yourself and pass it as a file so quoting and line structure survive intact.

```bash
"$SKILL_DIR/scripts/codex-generate-image.sh" --out assets/<role>.png --prompt-file <prompt.txt>
```

For an edit, name each local source with `--edit`; the wrapper grants the Codex sandbox read access to those directories and instructs it to inspect them before passing them as `referenced_image_paths`. Never mix local paths with conversation-image references, and state the invariants explicitly in the prompt: `change only X; keep Y unchanged`.

```bash
"$SKILL_DIR/scripts/codex-generate-image.sh" --out assets/<role>-v2.png --edit assets/<role>.png --prompt-file <edit-prompt.txt>
```

One asset per run, one new output path per run. The wrapper refuses to overwrite and leaves the Codex original under `~/.codex/generated_images/` as the preserved source.

On the delegated route, verify before accepting, in this order:

1. `VERIFIED_ON_DISK` — the wrapper confirmed the file itself; a `SAVED` line alone is the subagent's claim, not evidence.
2. `ASSUMPTIONS` — a subagent that reinterpreted subject, palette, background, or composition invalidates the asset even when a file exists. Rewrite the prompt and regenerate to a new path.
3. Read the file at intended size and judge it against the Visual Genome and the evaluation gates.

On either route, do not claim that an asset was saved locally unless the tool or wrapper actually confirms a usable file on disk. If no local output is available, report the integration blocker instead of inventing a filename or using an unrelated placeholder.

## Deterministic color-key removal

Use deterministic color-key removal only when the source uses one exact, uniform supported key that is absent from the subject. It removes external and enclosed key regions and performs color unmix/despill at antialiased edges.

```bash
"$SKILL_DIR/scripts/remove-color-key.swift" --key green input.png output-transparent.png
"$SKILL_DIR/scripts/remove-color-key.swift" --key blue input.png output-transparent.png
"$SKILL_DIR/scripts/remove-color-key.swift" --key magenta input.png output-transparent.png
"$SKILL_DIR/scripts/inspect-image-asset.sh" --require-alpha output-transparent.png
```

The legacy magenta route remains available for compatibility:

```bash
"$SKILL_DIR/scripts/remove-magenta-key.swift" input.png output-transparent.png
```

Do not use a key script for a gradient, shadowed key, mixed background, subject containing important key-colored detail, or unsupported color. Preserve the input and always choose a new output path.

## Semantic local matting

When the background is simple but is not an exact supported key, use the bundled macOS Vision route:

```bash
"$SKILL_DIR/scripts/remove-image-background.swift" input.png output-transparent.png
"$SKILL_DIR/scripts/inspect-image-asset.sh" --require-alpha output-transparent.png
```

The optional final `trim-radius` accepts `0` through `24`; begin with the default `3` and increase only when visual inspection proves a wider baked matte:

```bash
"$SKILL_DIR/scripts/remove-image-background.swift" input.png output-transparent.png 8
```

Semantic foreground masks may clean the outside while leaving key color inside brackets, cables, arrays, or other enclosed gaps. Do not treat a clean outer contour as proof of completion. Increasing erosion can also delete thin hardware; choose deterministic removal when the exact key is known.

## One-pass native removal edit

Use at most one native image edit when local deterministic or semantic methods cannot separate a materially ambiguous background:

```text
Keep the subject, silhouette, materials, colors, lighting, perspective, scale, padding, and composition unchanged.
Remove only the background and edge contamination. Do not redraw, restyle, add objects, add text, crop, or change the subject.
Return a transparent-background PNG with clean antialiased edges.
```

Reject a baked checkerboard immediately when metadata reports no alpha. Repeated edits tend to drift identity; if one edit fails, choose a vector/static fallback or mark the asset `Provisional` with the failed criterion.

## Alpha and edge QA

Run:

```bash
"$SKILL_DIR/scripts/inspect-image-asset.sh" --require-alpha path/to/asset.png
```

Preview the output on checkerboard, near-white, and near-black surfaces at master and intended CSS sizes. Reject clipped silhouettes, shadows outside the subject, key-colored internal gaps, fringe, transparent subject holes, lost hardware, hard stair-stepping, or detail that collapses at target size.

Generated raster geometry may differ from the placeholder SVG, numeral, or CSS shape it replaces. Recalculate mobile position, size, crop, and opacity; do not inherit placeholder geometry unchanged.

## Integration

- Follow existing asset naming, image-component, loading, and directory conventions.
- Preserve a transparent PNG master when alpha is required; do not convert formats without a tested repo pipeline.
- Provide intrinsic width/height and responsive `sizes`; follow the repo's LCP strategy for above-the-fold imagery and lazy-load non-critical art.
- Add deliberate overlays, contrast protection, focal positioning, and responsive crops for backgrounds.
- Keep essential labels, values, instructions, and localized copy in semantic HTML.
- Use `alt=""` for decorative imagery and concise functional alt text for meaningful imagery.
- Check light/dark contexts, high-density displays, mobile crop, reduced motion, loading/error states, layout stability, and horizontal overflow.
- Never use generated imagery as fake data, a fake chart, an unimplemented feature, or an accessible control.

## Implemented-page screenshot loop

1. Serve the real project through its normal local command.
2. Wait for fonts and images to load; capture representative desktop and narrow-mobile viewports.
3. Add full-page, ordered-section, first-load, scrolled, Safari, or CJK captures when the narrative or changed implementation needs them.
4. Inspect content and imagery together for text-safe space, contrast, focus, continuity, CTA, crop, intrinsic geometry, motion, and overflow.
5. Make one focused prompt, asset, overlay, layout, crop, scale, or responsive correction for each material issue.
6. Recapture the affected viewport and report final evidence. Do not retouch screenshots to hide defects.

## Failure states

- Native image tool unavailable: report the blocker; do not route to another model service.
- No local file returned: report that the asset cannot be integrated.
- Key or semantic matting fails: use a vector/static candidate or mark `Provisional` with the exact failed check.
- Generated detail fails at target size: prefer the clearer vector or static candidate.
- Generated art copies identity or implies nonexistent capability/data: reject it.
- Required third-party dependency is absent: present the verified capability and fallback, then wait for installation approval.
