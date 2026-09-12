# Image assets with GPT Image

Read this after the direction is approved and before the first generation call. It covers the shared visual bible, the element manifest, choosing between illustration and vector, prompt compilation, the platform routes, matting, the contact sheet, and placing images in the page. The rendered page is the acceptance target.

## Shared visual bible

Write one compact block once and reuse it at the top of every prompt. Continuity comes from shared decisions, not from near-identical images.

```text
Website promise: [the single idea the page makes believable].
Audience and desired action: [who, what they need, the conversion].
Emotional arc: [opening feeling -> evidence and trust -> final action].
Visual Genome: [physical world; graphic language; display medium; motion grammar; image transformation].
Illustration style: [medium and finish, line and edge quality, light, color density, detail level, how figures and objects are drawn].
Realism mode: [documentary, commercial photography, editorial illustration, stylized 3D, or another explicit finish].
Physical-world thesis: [what exists, how it is built and supported, scale evidence, wear, practical light].
Signature motif: [one recurring form, object, light, or framing device].
Continuity rules: [what stays constant across sections and what deliberately changes].
Copy constraints: [approved wording, fixed line groups, no-orphan behavior; the image itself carries no text].
Steer away from: [references' failures, clichés, and effects that would break product truth].
```

## Reference hierarchy

Classify every supplied image before generation:

1. `primary-anchor`: the strongest approved finish and compositional preference;
2. `secondary-anchor`: supporting environment, scale, or presentation language;
3. `supporting-reference`: one explicitly named transferable property;
4. `negative-reference`: failures that become steer-away notes.

Make local references visible to the tool before prompting: on Codex open them with `view_image` (or attach them); on Claude Code pass each one with `--edit`. Say in the prompt that they are visual-language references. Extract the signals that transfer (realism mode, contrast, black level, highlight roll-off, temperature, material response, wear, camera distance, lens feel, framing, depth, practical light, atmosphere) and leave people, faces, bodies, costumes, logos, labels, text, measurements, UI, layout, and unrelated objects with the reference.

## Element manifest

One row per planned visual, kept in the direction document:

| Field | Meaning |
|---|---|
| `id` | Stable purpose-led identifier |
| `role` | Background scene, integrated hero, spot illustration, self-backed illustration, isolated object, transition, empty state, card art, texture, control icon |
| `section` | Where it sits on the page |
| `rendered_size` | The CSS size it occupies, desktop and mobile when they differ |
| `interactive` | Whether it represents or changes state |
| `backgrounds` | Light, dark, mixed, image, or self-contained surfaces |
| `section_job` | The narrative or conversion purpose |
| `text_safe_area` | Quiet region reserved for real HTML |
| `continuity` | Motif, light, material, camera, or transition shared with neighbors |
| `semantics` | Meaningful with concise alt text, or decorative with empty alt text |
| `medium` | `vector`, `generated-raster`, or `compare` |
| `alpha_route` | `none` for scenes, textures, and self-backed illustrations; `transparent` (real alpha, verified) or a key color `green`, `blue`, `magenta` for an isolated subject |
| `status` | `planned`, `pass`, `correctable`, `regenerate`, or `fallback` |

Every row has a job. Filler with no UI, narrative, or conversion role is left out.

## Illustration or vector

The choice follows the rendered size and the kind of information the element carries.

- **Vector or CSS** for functional symbols, anything around 12 to 32px, pieces that need `currentColor`, multiple states, exact alignment, keyboard clarity, or theme recoloring. GPT Image draws these well and mats them badly; thin lines, cutouts, and small lettering blur at that size.
- **Generated raster** where material, light, character, atmosphere, or worldbuilding carry meaning and the element is large enough for that information to survive: environments, integrated heroes, spot illustrations, section transitions, mascots, empty states, branded illustration, textures, product mockups.
- **Compare** for a branded piece around 32 to 96px when neither route is clearly better. Render both candidates in the real component at target sizes and backgrounds, in a scratch directory from `mktemp -d`, and copy only the winner into the repo.

Three habits that make generated illustration sit well in a page:

- **Large canvas, CSS scale.** One subject filling seven to eight tenths of a 1024-plus canvas with clear padding mats cleanly and stays sharp when scaled down. Generating at final size loses both.
- **Spot illustration over scattered cutouts.** Several small ornaments composed into one scene mat once, share one light, and read as designed. Separate cutouts rarely agree with each other.
- **Self-backed when the layout allows.** An illustration that carries its own color field, card, or environment needs no matting and often looks more intentional than a floating cutout.

## Prompt compiler

Assemble each prompt in this order:

1. shared visual bible;
2. reference hierarchy, visual language only;
3. section job: exact section, narrative purpose, rendered size, conversion contribution;
4. the Visual Genome axes relevant to this element;
5. physical subject: construction, support, scale cues, hardware, seams, wear, use;
6. surface and practical light: material response, black and highlight behavior, motivated fixtures, restrained accents;
7. camera and composition: aspect ratio, lens feel, height, focal region, text-safe region, desktop and mobile crop tolerance;
8. relationship to adjacent sections: what continues, what changes;
9. what stays with the references: people, identity, logos, text, measurements, UI, symbols, layouts, unrelated objects;
10. the subject-specific failure modes you will reject: geometry, light, repetition, fake text, material.

Physical, graphic, camera, and UI decisions replace style labels such as `cyberpunk`, `Apple-like`, or `cinematic lighting`.

## Role templates

### Background scene or integrated hero

```text
A [hero/section/footer] environmental scene for [specific website and section job].
Narrative purpose: [what the visitor understands or feels] and how it advances toward [conversion].
Visual Genome: [only the axes relevant to this scene].
Physical world: [buildable environment, subject, support, material, use evidence, practical light].
Composition: target [aspect ratio and viewport], focal subject in [region], quiet text-safe region in [region] for real HTML [heading/copy/CTA].
Responsive crop: preserve [essential subject or horizon] across desktop and narrow mobile; keep critical detail away from fragile edges.
Continuity: [visual transition entering and leaving this scene].
The environment is intentional and fills the frame; the image carries no text, letters, logos, watermark, mock UI, or fake data.
```

### Spot illustration

```text
A single composed spot illustration for [specific product and section], showing [the small group of objects or the small scene] as one unit.
Illustration style: [from the bible: medium, line, light, color density, detail].
Everything in the scene shares one light source and one ground or none; objects touch or overlap deliberately so the group reads as one silhouette.
Target: approximately [CSS size] on [light/dark] UI surfaces; generous clear padding around the whole group; complete silhouette, nothing cropped.
Background: a genuinely transparent background with real alpha | one perfectly uniform [green #00FF00 / blue #0000FF / magenta #FF00FF] background absent from the subject.
No frame, card, text, watermark, or extra objects outside the group.
```

### Self-backed illustration

```text
A [card / panel / vignette] illustration for [specific product and section], where the picture carries its own [color field / rounded card / environment] as part of the design.
Illustration style: [from the bible].
The backing shape is [shape, corner radius or edge treatment, color from the palette]; the subject sits [placement] with [padding] inside it.
Composition for [CSS size]; the backing edge is clean and straight so the image can be placed flush in the layout without matting.
No text, watermark, or mock UI.
```

### Isolated object

Two alpha routes. Ask for `transparent` first: the built-in tool can return real alpha. Verify with `inspect-image-asset.sh --require-alpha`; `hasAlpha: no` under a visible checkerboard means baked pixels, so the next attempt uses a key color absent from the subject palette: pure green `#00FF00`, pure blue `#0000FF`, or pure magenta `#FF00FF`.

```text
A single [asset subject] for [specific product and UI role].
Visual language: [product-specific material, shape, restrained palette, practical light, perspective].
Target: approximately [CSS size] on [light/dark/mixed] UI surfaces.
Isolated and centered with generous clear padding; complete silhouette, nothing cropped. One subject only.
Background: [transparent route] a genuinely transparent background with real alpha | [key route] one perfectly uniform [green #00FF00 / blue #0000FF / magenta #FF00FF] background absent from the subject, with no gradient, lighting falloff, studio sweep, or shadow on the key.
Preserve antialiased edges, fine hardware, internal gaps, and padding. No frame, card, mock interface, watermark, logo, text, floor, or extra objects; no cast shadow outside the subject unless the component needs one.
```

### Texture

State whether it tiles, its maximum usable contrast, the surfaces it sits under, its scale and transformation, and the content it must stay quiet beneath. A texture derives from real product geometry, material, data, or brand structure.

## Native image generation

Script paths are relative to the skill directory; set `SKILL_DIR` once per session to the directory this skill's `SKILL.md` was loaded from (for example `~/.codex/skills/openai-frontend-design`). Invoke scripts through `bash` and `swift`.

**On Codex (built-in tool)**: for a new asset, call `image_gen` with the complete prompt. For an edit, open each local source with `view_image` first so it is visible in the conversation, then run the edit against it; the tool edits what it can see. Outputs land under `$CODEX_HOME/generated_images/`; copy the accepted file into `design/assets/generated/` (or the repo's asset folder) at a new path.

**On Claude Code (delegated route)**: generation runs through `scripts/codex-generate-image.sh`, which delegates one non-interactive turn to the bundled Codex CLI and its built-in `image_gen` tool. Write the complete prompt yourself and pass it as a file so quoting and line structure survive.

```bash
bash "$SKILL_DIR/scripts/codex-generate-image.sh" --out design/assets/generated/<id>.png --prompt-file <prompt.txt>
```

For an edit, name each local source with `--edit`; the wrapper attaches it to the turn so the built-in tool can see it. State invariants explicitly: `change only X; keep Y unchanged`, and repeat them on every iteration.

```bash
bash "$SKILL_DIR/scripts/codex-generate-image.sh" --out design/assets/generated/<id>-v2.png --edit design/assets/generated/<id>.png --prompt-file <edit-prompt.txt>
```

One asset per run, one new output path per run. The wrapper refuses to overwrite, enforces its own timeout (default 600 s, exit 124), and leaves the Codex original under `~/.codex/generated_images/`.

On the delegated route, accept in this order:

1. `VERIFIED_ON_DISK`: the wrapper confirmed the file itself; a `SAVED` line alone is the subagent's claim.
2. `ASSUMPTIONS`: a subagent that reinterpreted subject, palette, background, or composition means a rewritten prompt and a new path.
3. Look at the file at rendered size and judge it against the direction and `design-critique.md`.

An asset counts as saved only when the tool or wrapper confirms a usable file on disk. With no local output, report the blocker.

## Matting

### Deterministic color-key removal

For a source with one exact, uniform supported key absent from the subject. Removes external and enclosed key regions and unmixes the key at antialiased edges.

```bash
swift "$SKILL_DIR/scripts/remove-color-key.swift" --key green input.png output-transparent.png
swift "$SKILL_DIR/scripts/remove-color-key.swift" --key blue input.png output-transparent.png
swift "$SKILL_DIR/scripts/remove-color-key.swift" --key magenta input.png output-transparent.png
bash "$SKILL_DIR/scripts/inspect-image-asset.sh" --require-alpha output-transparent.png
```

A gradient, shadowed key, mixed background, subject with important key-colored detail, or unsupported color calls for semantic matting or a one-pass native edit instead. The input stays; the output is a new path.

### Semantic matting

For a simple background that is not an exact key, the bundled macOS Vision route:

```bash
swift "$SKILL_DIR/scripts/remove-image-background.swift" input.png output-transparent.png
bash "$SKILL_DIR/scripts/inspect-image-asset.sh" --require-alpha output-transparent.png
```

The optional trailing `trim-radius` (0 to 24, default 3) erodes the matte; raise it only when inspection shows a baked halo, since erosion also eats thin hardware:

```bash
swift "$SKILL_DIR/scripts/remove-image-background.swift" input.png output-transparent.png 8
```

Semantic masks can clean the outer contour while leaving key color inside brackets, cables, or enclosed gaps; inspect the interior, not just the silhouette.

### One-pass native removal edit

When the transparent route, key removal, and semantic matting all fail on a materially ambiguous background, spend at most one native edit:

```text
Keep the subject, silhouette, materials, colors, lighting, perspective, scale, padding, and composition unchanged.
Remove only the background and edge contamination.
Return a transparent-background PNG with clean antialiased edges.
```

A baked checkerboard with no alpha in metadata is rejected. Repeated edits drift identity; after one failed edit, choose a self-backed version, a vector, or mark the element `Provisional` with the failed check.

### Alpha and edge check

```bash
bash "$SKILL_DIR/scripts/inspect-image-asset.sh" --require-alpha path/to/asset.png
```

Then look at the element on checkerboard, near-white, and near-black at master and rendered sizes. Clipped silhouettes, shadows outside the subject, key-colored gaps, fringe, holes, lost hardware, stair-stepping, and detail that collapses at rendered size are what you are looking for.

## Contact sheet

Lay the whole set out at rendered size on three backgrounds, with dimensions and alpha beside each:

```bash
bash "$SKILL_DIR/scripts/contact-sheet.sh" design/assets/generated design/assets/sizes.tsv
```

`sizes.tsv` is optional: lines of `<id or filename><TAB><css width>`; unlisted files render at 320px. Open the resulting `contact-sheet.html` in a browser (or screenshot it with the browser tool) to judge the set as one family before layout.

## Placing images in the page

- Follow existing asset naming, image-component, loading, and directory conventions.
- Keep a transparent PNG master when alpha is required; convert formats only through a tested repo pipeline.
- Give every image intrinsic width and height and responsive `sizes`; follow the repo's LCP strategy for above-the-fold imagery and lazy-load the rest.
- Backgrounds get deliberate overlays, contrast protection, focal positioning, and responsive crops.
- Essential labels, values, instructions, and localized copy stay in semantic HTML; `alt=""` for decorative imagery, concise alt text for meaningful imagery.
- Generated geometry differs from the placeholder it replaces; recalculate mobile position, size, crop, and opacity rather than inheriting them.
- Check light and dark contexts, high-density displays, mobile crop, reduced motion, loading and error states, layout stability, and horizontal overflow.

## Implemented-page screenshot loop

1. Serve the project through its normal local command.
2. Wait for fonts and images; capture desktop and narrow mobile.
3. Add full-page, first-load, scrolled, Safari, or CJK captures when the narrative or the changed implementation needs them.
4. Read content and imagery together using `design-critique.md`.
5. Make one focused prompt, asset, overlay, layout, crop, scale, or responsive correction per finding.
6. Recapture the affected viewport and report the evidence.

## Failure states

- Native tool unavailable: report the blocker; no other model service is used.
- No local file returned: the element cannot be placed; report it.
- Matting fails: self-backed version, vector or static candidate, or `Provisional` with the exact failed check.
- Detail fails at rendered size: the clearer vector or static candidate wins.
- The element copies identity or implies nonexistent capability: rejected.
- A dependency would be needed: present the verified capability and fallback, then wait for approval.
