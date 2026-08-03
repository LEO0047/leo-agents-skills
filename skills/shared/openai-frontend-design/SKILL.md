---
name: openai-frontend-design
description: Direct and implement narrative-led frontend experiences with OpenAI-generated imagery. Use for GPT/OpenAI-generated website visuals, image-first art direction, or custom frontend assets. Construct a project-specific Visual Genome, integrate accepted imagery into the real interface, and verify desktop and mobile screenshots without turning one prior aesthetic or one technical effect into a global template.
compat: [claude-code, codex]
compatibility: Requires macOS with sips (and swift for matting). On Codex, requires the native image_gen__imagegen tool for generation or editing and view_image for local visual inspection. On Claude Code, requires the bundled Codex CLI reached through scripts/codex-generate-image.sh for generation or editing, the Read tool for local visual inspection, and a browser tool for implemented-page screenshots.
metadata:
  short-description: Design frontend UI with OpenAI-generated visual assets
---

# OpenAI Frontend Design

Use OpenAI image generation as a frontend art-direction and visual-storytelling instrument, not as a substitute for product truth, interaction design, accessible HTML, or a project-specific visual thesis. Generated imagery must support the site's audience journey, section sequence, and conversion goal. Judge it inside the implemented website, not only in an image viewer.

No palette, material system, layout skeleton, display treatment, motion grammar, or prior aesthetic profile is globally mandatory. The brief, closest repo instructions, existing design system, approved references, and real content remain authoritative.

## Required foundation and routing

Before planning or editing a frontend, read and follow both sibling files completely:

- [`../frontend-design/SKILL.md`](../frontend-design/SKILL.md) for core design direction.
- [`../frontend-design/QUALITY_GATE.md`](../frontend-design/QUALITY_GATE.md) for implementation and visual verification.

Then route to these references:

- Read [`references/visual-genome.md`](references/visual-genome.md) for every new or materially revised visual direction.
- Read [`references/openai-image-assets.md`](references/openai-image-assets.md) before generating, comparing, editing, matting, or integrating image assets.
- Read [`references/technology-capability-map.md`](references/technology-capability-map.md) before proposing advanced motion, WebGL, shaders, smooth scrolling, or a third-party visual package.
- Read [`references/evaluation-gates.md`](references/evaluation-gates.md) before accepting visual assets or reporting a frontend as visually verified.

## Image generation route

Pick the route that matches the running platform:

**On Codex** — call the native `image_gen__imagegen` tool directly and inspect results with `view_image`. No wrapper is involved.

**On Claude Code** — this agent has no built-in image generation tool. OpenAI image generation is reached by delegating one non-interactive turn to the bundled Codex CLI, which owns the native `image_gen__imagegen` tool and reuses the existing ChatGPT login. No API key is involved.

Always go through the wrapper rather than composing a Codex invocation by hand. Every `scripts/` and `references/` path in this skill is relative to the skill directory, not the project working directory; set `SKILL_DIR` once per session to wherever this skill is installed (for example `~/.claude/skills/openai-frontend-design` or `~/.codex/skills/openai-frontend-design`) and use it:

```bash
SKILL_DIR="$HOME/.claude/skills/openai-frontend-design"
"$SKILL_DIR/scripts/codex-generate-image.sh" --out assets/hero-subject.png --prompt-file /tmp/hero-prompt.txt
"$SKILL_DIR/scripts/codex-generate-image.sh" --out assets/hero-v2.png --edit assets/hero-subject.png --prompt-file /tmp/hero-edit.txt
```

The wrapper refuses to overwrite an existing output path, keeps the Codex original under `~/.codex/generated_images/`, and confirms the result from the filesystem rather than from the subagent's own claim. It prints `SAVED`, `ORIGINAL`, `METADATA`, `ASSUMPTIONS`, and `VERIFIED_ON_DISK`.

On the delegated route, treat the delegated turn as an untrusted generator, not a design partner:

- Write the complete image prompt yourself from the Visual Genome. Never delegate art direction, subject choice, or palette decisions.
- Read `ASSUMPTIONS` on every run. A subagent that reinterpreted the subject invalidates the asset even when a file exists.
- Inspect the returned file with the Read tool before accepting it. A `SAVED` line is not evidence of a usable image.
- Report an integration blocker rather than inventing a filename if no file lands on disk.

## Authorization boundary

An explicit invocation of `openai-frontend-design`, or an explicit request for OpenAI/GPT-generated frontend assets, authorizes image generation through the platform route above (native `image_gen__imagegen` calls on Codex; `scripts/codex-generate-image.sh` runs on Claude Code), creation of new local image assets, and non-destructive local background matting within the stated frontend scope. Preserve generated originals and write edited or transparent results to new paths.

It does not authorize RunComfy or another external model router, dependency installation, overwriting or deleting existing assets, unrelated imagery, remote uploads, commit, push, PR, publish, or deploy. A technology recommendation is not installation permission. Widening the Codex sandbox beyond the wrapper's `workspace-write` scope, or passing `--dangerously-bypass-approvals-and-sandbox`, is outside this skill.

## Model identity and provenance

Treat a ChatGPT product label, an API model ID, and the Codex tool route as separate facts. The native `image_gen__imagegen` tool does not expose a trustworthy model selector or model ID in this skill's contract, and on the delegated route the extra hop adds a second unverified layer.

- Never claim `gpt-image-2` or another exact model unless the tool or an explicitly authorized API response proves it.
- The Codex model reported by `-m` or `~/.codex/config.toml` is the driving agent, not the image model. Never present it as the image model.
- If hard model pinning is required, report native routing as unverified.
- When provenance matters, describe the result as `OpenAI native image generation / model ID unverified` (append `via delegated Codex turn` on the delegated route).

## Required Visual Genome contract

Before implementation or image generation, record a compact direction with these fields:

| Field | Contract |
|---|---|
| `aesthetic_profile` | `brief-native`, `leo-visual-dna`, a named assembled genome, or a custom reference-led direction |
| `profile_reason` | Why the selected profile fits the subject, audience, and page job |
| `physical_world` | Exactly one buildable or photographable world |
| `graphic_language` | Exactly one primary language and at most one contrasting secondary language |
| `display_medium` | Zero or one display treatment; `none` is valid |
| `motion_grammar` | One narrative motion logic, or `none` when motion adds no value |
| `image_transformation` | One primary transformation and at most one supporting transformation |
| `signature_interaction` | Zero or one memorable interaction tied to the subject |
| `forbidden_elements` | Specific bundle reuse, clichés, transfers, or effects that would break product truth |
| `text_safe_areas` | Desktop and mobile regions reserved for real HTML content |
| `reduced_motion_fallback` | How meaning and hierarchy survive without motion |

Do not begin generation until these choices are internally compatible and the site's actual subject remains dominant.

## Leo Visual DNA routing

When the brief does not establish a stronger direction, use `leo-visual-dna` as a decision framework, not a fixed theme. It contains four transferable genes:

- `content_order`: clarity, deliberate whitespace, stable hierarchy, and product-first composition;
- `product_drama`: contextual reveal, image scale, and restrained visual tension;
- `mission_scale`: milestones, sequence, operational language, and a sense of consequential progress;
- `engineering_signature`: credible materials, manufacturing evidence, measurement, calibration, or signal behavior used with restraint.

Select one mode by subject:

- `Product Reveal` — planning weight `60 / 30 / 10`: content order / product drama / engineering signature.
- `Mission Launch` — planning weight `30 / 55 / 15`: content order / product drama plus mission scale / engineering signature.
- `Signal Workshop` — planning weight `35 / 20 / 45`: content order / product drama / engineering signature.

These numbers express design emphasis only. Never convert them into literal color percentages, component counts, fixed palettes, or mandatory layout proportions. A conflicting brief, reference, accessibility need, or design system overrides this routing.

Brand research may inform transferable principles, but do not copy another company's layout, identity, wording, product language, or complete visual trade dress. Keep brand names out of active prompt style commands unless the user explicitly requests a lawful reference comparison; describe the relevant visual properties instead.

## Reference hierarchy and anti-copy check

Rank supplied references before prompting:

1. `primary-anchor`: the user's strongest approved preference;
2. `secondary-anchor`: a supporting direction;
3. `supporting-reference`: one named transferable property;
4. `negative-reference`: a result or example whose failures must be forbidden.

References provide visual language only unless the user separately authorizes their real subject matter. Forbid accidental transfer of people, faces, bodies, costumes, logos, labels, measurements, text, UI, symbols, or unrelated objects.

When safe evidence for the last three completed visual directions is available in the workspace, current conversation, or explicitly provided memory, compare:

- dominant palette;
- display-type character;
- layout skeleton;
- hero composition;
- motion grammar;
- image treatment;
- signature interaction.

If three or more repeat together, revise at least one Visual Genome axis before implementation. If history is unavailable, record `Uncertainty: recent visual-direction evidence unavailable`; do not invent history or write durable memory automatically.

## Workflow

1. Inspect the product, audience, page job, real content, existing tokens, components, asset conventions, interactions, and responsive behavior.
2. Define the design thesis, conversion goal, emotional arc, and one justified signature element using the base frontend skill.
3. Write the Visual Genome contract and perform the anti-copy check.
4. Rank references and record approved copy, punctuation, fixed-line, and no-orphan constraints.
5. Map each major section to its story job, visual intensity, text-safe region, transition, and relationship to the conversion path.
6. Write an asset manifest and choose `vector`, `generated-raster`, or `compare` for every planned visual role.
7. Establish a shared visual bible: realism mode, palette, materials, practical-light behavior, camera language, depth, texture, recurring motif, copy rhythm, and forbidden elements.
8. Generate only assets that materially support the plan, one generation run per asset through the platform route, with a prompt you wrote from the Visual Genome. Keep small functional controls vector-based.
9. Inspect every returned file (and its `ASSUMPTIONS` line on the delegated route) at intended size against the reference hierarchy, physical-world thesis, neighboring content, and evaluation gates.
10. Integrate accepted assets with real HTML copy, controls, overlays, responsive crops, intrinsic dimensions, loading behavior, and accessible semantics.
11. Capture the implemented page at representative desktop and narrow-mobile viewports after fonts and images load, resizing between captures rather than assuming one size generalizes. Add full-page, key-section, first-load, scrolled, Safari, or CJK captures when the changed surface requires them. If the available browser tool is Chromium-only, report a required Safari or WebKit check as `未執行` instead of implying it was run.
12. Complete at least one focused correction pass for any material issue, rerun relevant checks, and report only the evidence actually inspected.

## Non-negotiable gates

- Product truth, accessible controls, readable content, responsive behavior, and reduced-motion meaning outrank visual spectacle.
- A display medium such as CRT, LCD, e-paper, projection, or oscilloscope is a local viewing or state language, not the site's total aesthetic direction.
- Per page, default to at most one primary motion grammar, one background effect, and one signature microinteraction. Justify each exception through narrative value.
- For realism-critical imagery, define construction, support, gravity, practical light, scale evidence, wear, camera behavior, and likely synthetic failure modes before prompting.
- Reject fake text, fake data, fake controls, copied brand identity, impossible construction, unmotivated light, or imagery that implies nonexistent functionality.
- Do not recommend WebGL, smooth scrolling, shaders, or a package merely to make a simple information page feel more advanced.
- Keep approved localized copy and exact line groups in HTML. Verify fixed lines and CJK wrappers at desktop and mobile after a cold-style reload.

## Delivery evidence

Report separately:

- the selected Visual Genome and why it fits;
- anti-copy evidence or the explicit `Uncertainty` state;
- generated, edited, selected, rejected, and vector-retained assets;
- provenance, alpha metadata, and light/dark target-size edge inspection where relevant;
- desktop, mobile, and any required full-page, key-section, CJK, first-load, or scrolled screenshot review, plus any Safari/WebKit check left unrun;
- the focused correction pass and its result;
- relevant lint, typecheck, test, or build results;
- technology recommendations, live-verification status, fallbacks, and any unapproved dependency blocker.

Use `已驗證`, `Observed`, `Provisional`, `Uncertainty`, and `未執行` accurately. Never call an uninspected generated asset or implementation production-ready.
