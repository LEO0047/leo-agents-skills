---
name: openai-frontend-design
description: Design and implement distinctive frontend interfaces with OpenAI-generated visual assets. Use this skill whenever the user explicitly invokes openai-frontend-design, asks for GPT/OpenAI-generated UI imagery, wants image-first frontend art direction, prefers generated artwork over generic SVG decoration, or requests custom transparent UI assets such as heroes, empty states, mascots, card illustrations, branded category icons, textures, or product mockups. Keep small functional controls vector-based while using native OpenAI image generation where imagery materially improves the product.
compat: [codex]
compatibility: Requires the native image_gen__imagegen tool for generation or editing, view_image for local visual inspection, and macOS sips for deterministic image metadata checks.
metadata:
  short-description: Design frontend UI with OpenAI-generated visual assets
---

# OpenAI Frontend Design

Use OpenAI image generation as a frontend art-direction instrument, not as a replacement for sound interaction design. Generated imagery should make the product more specific, expressive, and memorable while functional controls remain clear, responsive, themeable, and accessible.

## Required foundation

Before planning or editing a frontend, read and follow both sibling files completely:

- [`../frontend-design/SKILL.md`](../frontend-design/SKILL.md) for the core design process.
- [`../frontend-design/QUALITY_GATE.md`](../frontend-design/QUALITY_GATE.md) for implementation and visual verification.

Then read [`references/openai-image-assets.md`](references/openai-image-assets.md) whenever the task may generate, compare, edit, or integrate image assets.

Repo-local instructions, the existing design system, and the user's current brief remain authoritative. “OpenAI” identifies the image-generation path; it does not impose OpenAI's brand style.

## Authorization boundary

An explicit invocation of `$openai-frontend-design`, or an explicit request for OpenAI/GPT-generated frontend assets, authorizes native `image_gen__imagegen` calls and creation of new local image assets within that frontend task's stated scope.

It does not authorize RunComfy or another external model router, dependency installation, overwriting or deleting existing assets, unrelated generated imagery, remote uploads, commit, push, PR, publish, or deploy. Follow higher-priority instructions if they narrow this boundary.

## Workflow

1. Inspect the product context, current asset conventions, design tokens, components, responsive behavior, and the real content to be presented.
2. Define the design thesis and one signature element using the base skill.
3. Write a compact asset manifest before generating anything.
4. Classify each requested or proposed element as `vector`, `generated-raster`, or `compare`.
5. Generate only the manifest items that benefit from imagery. Use the native OpenAI image tool; do not route to RunComfy unless the user separately requests it.
6. Inspect every result, verify transparency when required, and perform at most one background-removal edit.
7. Integrate only accepted assets using the repo's existing image component and asset directory conventions.
8. Render the real UI, inspect desktop and mobile screenshots, compare ambiguous candidates in context, and complete one critique-and-correction pass.

## Asset manifest

Record one row per visual asset:

| Field | Meaning |
|---|---|
| `id` | Short stable purpose-led identifier |
| `role` | Hero, empty state, mascot, card art, category icon, texture, control icon, or other real UI role |
| `display_size` | Intended CSS width and height or responsive range |
| `interactive` | Whether it represents or changes state |
| `recolorable` | Whether CSS/theme color changes are required |
| `backgrounds` | Light, dark, mixed, image, or transparent surfaces it must survive |
| `semantics` | Meaningful with concise alt text, or decorative with empty alt text |
| `medium` | `vector`, `generated-raster`, or `compare` |
| `reason` | One sentence explaining why the medium fits the product |

Do not turn the manifest into a long design document. Its purpose is to prevent decorative image generation without a real UI role.

## Choose the medium deliberately

Prefer existing vector icons, an established icon library, or simple CSS for small functional glyphs such as search, close, back, warning, disclosure, checkbox, radio, menu, and loading controls. These elements need exact alignment, current-color theming, state changes, keyboard clarity, and crisp rendering at small sizes.

Prefer OpenAI-generated raster assets for heroes, mascots, empty states, feature or card illustrations, branded category imagery, atmospheric textures, product mockups, and other visuals whose material, lighting, character, or narrative contributes meaning.

Use `compare` for ambiguous branded elements, normally in the `32–96px` range. Put a generated candidate and a vector/icon-library candidate in a task-specific temporary directory created with `mktemp -d`. Render both in the actual component at target sizes and on required backgrounds. Choose the one with better product fit, legibility, edge quality, hierarchy, theme compatibility, and loading cost. Copy only the selected candidate into the repo; never use the repo as a candidate dump.

## Native image generation

For a brand-new asset, call `image_gen__imagegen` with the complete prompt and omit reference-image parameters. For an edit, first inspect the local source with `view_image`, then pass only the required local paths through `referenced_image_paths`. Never provide both local reference paths and conversation-image references.

Prompts should describe the product-specific subject, visual language, material, palette, lighting, camera or perspective, intended UI scale, and composition. For isolated UI assets, request generous clear padding, no crop, one subject, no frame, no background, no watermark, no extra objects, no baked UI, and a transparent PNG. Keep essential labels, instructions, values, and localized copy in HTML rather than inside generated pixels.

Do not claim that an asset was saved locally unless the tool actually provides or saves a local file. If no usable local output is available, report the integration blocker instead of substituting an invented filename or unrelated placeholder.

## Transparency and background removal

1. Request a transparent background in the first generation.
2. Inspect the result visually and run `scripts/inspect-image-asset.sh --require-alpha <asset.png>`.
3. Preview it against checkerboard, light, and dark surfaces. An alpha channel alone does not prove clean edges.
4. If the asset is opaque or has an obvious matte/halo, make exactly one native OpenAI edit: preserve the subject, materials, lighting, scale, padding, and composition; remove only the background and edge contamination; return a transparent PNG.
5. Re-run metadata and visual checks. If it still fails, do not install `rembg` or another dependency. Use the vector candidate when one exists; otherwise report the asset as `Provisional` and explain the failed criterion.

## Frontend integration

- Preserve a transparent PNG master when transparency is required. Do not convert formats unless the repo already has a tested image pipeline.
- Use the existing framework image component and asset directory. Supply intrinsic dimensions and responsive `sizes`; lazy-load non-critical imagery and follow the repo's LCP strategy for heroes.
- Use `alt=""` for decorative imagery. Give meaningful assets concise alt text that communicates their function or content without describing irrelevant visual style.
- Check light and dark surfaces, high-density displays, mobile crops, reduced-motion behavior, loading and error states, and layout stability.
- Do not use generated imagery as fake data, a fake chart, an unimplemented feature, or a substitute for accessible controls.

## Delivery evidence

Report separately:

- Which assets were generated, edited, selected, or rejected.
- Which elements remained vector and why.
- Alpha metadata and light/dark edge inspection results.
- Desktop and mobile screenshot review.
- Relevant lint, typecheck, test, or build results.

Use `已驗證`, `Observed`, `Provisional`, and `未執行` accurately. Never describe an uninspected generated asset as production-ready.
