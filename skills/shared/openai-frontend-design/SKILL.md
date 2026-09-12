---
name: openai-frontend-design
description: Design a web page the way a designer would, with GPT Image illustrations as a core material. Use when a brief wants OpenAI/GPT-generated illustration for a site, a landing page or hero that should feel designed rather than templated, or decorative imagery beyond plain HTML. Thinks the visual direction through first and stops for the user's confirmation, then generates the elements, lays out the real page, and critiques desktop and mobile screenshots.
compat: [claude-code, codex]
compatibility: macOS with sips (swift for matting). Codex - built-in image_gen tool and view_image. Claude Code - bundled Codex CLI through scripts/codex-generate-image.sh, the Read tool for image inspection, and a browser tool for page screenshots.
metadata:
  short-description: Designer-led web pages illustrated with GPT Image
---

# OpenAI Frontend Design

Work like a designer who has taken on this page. Understand what it is for, decide on the one visual direction that fits this subject right now, make the illustrations that direction needs, and build the page around them. Generated imagery is a design material, chosen and placed with the same care as type and spacing. A picture dropped into a slot to fill it is the outcome this skill exists to avoid.

No direction is preset. The brief, the real content, the existing design system, and approved references decide; where they leave an axis free, choose what serves this page best today.

## Foundation and routing

Read both sibling files before the direction pass: [`../frontend-design/SKILL.md`](../frontend-design/SKILL.md) for the design lead's method, the plan-then-critique passes, and the three AI-default looks to steer around; [`../frontend-design/QUALITY_GATE.md`](../frontend-design/QUALITY_GATE.md) for implementation and verification evidence.

Then read by branch:

| When | Read |
|---|---|
| Writing the direction | [`references/visual-direction-template.md`](references/visual-direction-template.md) for the document skeleton, [`references/visual-genome.md`](references/visual-genome.md) for the five axes and the anti-copy comparison |
| Generating, editing, matting, or placing an image | [`references/openai-image-assets.md`](references/openai-image-assets.md) |
| Critiquing an element or the built page | [`references/design-critique.md`](references/design-critique.md) |

## The six passes

**1. Understand.** Read the brief, the real content, the audience, and the existing tokens, components, and assets. You are ready when you can say the subject, the audience, and the page's single job, each in one sentence.

**2. Direction.** Write `design/visual-direction.md` from the template, following the repo's own conventions where it has them: the design thesis and one signature, the five Visual Genome axes, palette and type leanings, the illustration style, the reference hierarchy, and the element list. Each element gets a role, a section, a rendered size, an alpha route, and a prompt draft. Decide here which pieces are illustration and which stay SVG or CSS.

**Checkpoint.** Stop. Give the user the direction as a short summary in their language: the thesis, the illustration style, the element list, and any open question. Wait for their reply before generating any image. They may redirect, cut, or add elements; update the document, then continue.

**3. Elements.** Generate one asset per run through the platform route below, with the prompt you compiled from the direction. Verify each on disk, read its assumptions, look at it at rendered size, then follow its alpha route. An element that misses the direction gets a rewritten prompt and a new path; one that resists matting becomes a spot illustration, a self-backed illustration, or vector. Assets live in `design/assets/generated/`. The contact sheet script lays the whole set out at rendered size on light, dark, and checkerboard so the set can be judged together.

**4. Layout.** Build the real page: semantic HTML, the type scale and palette from the direction, real copy, and the illustrations placed with intrinsic dimensions, responsive crops, and deliberate overlays. Type, spacing, hierarchy, and motion are designed together with the images, following the base skill.

**5. Critique.** Screenshot a representative desktop and a narrow mobile viewport after fonts and images load, resizing between captures. Look with a designer's eye, guided by `design-critique.md`: does the page read as one world, does each illustration earn its place, are edges clean at rendered size, does the mobile crop keep the meaning. Fix what you find and recapture.

**6. Deliver.** The direction document, the asset folder with each element's status, the page, the screenshots, and a plain list of the checks you did not run.

## What works with GPT Image

Designer's notes from practice, to be weighed rather than obeyed:

- Generate on a large canvas and scale down in CSS. One subject filling seven to eight tenths of a 1024-plus canvas with clear padding mats cleanly; a subject generated at its final small size does not.
- Small rendered sizes, thin lines, cutouts, and fine lettering blur when matted. Those pieces are usually better as SVG or CSS.
- Several small ornaments read better as one spot illustration, a single composed scene, than as separate cutouts. It also mats once instead of five times.
- When the layout allows, a self-backed illustration, where the picture carries its own color field, card, or environment, needs no matting at all and often looks more designed.
- Ask the tool for a transparent background first and check `hasAlpha` with `sips`. Reach for the key-color or semantic matting scripts when real alpha did not come back.

## Image generation route

**Codex.** Call the built-in `image_gen` tool directly and inspect results with `view_image`. Codex's bundled `imagegen` system skill governs that tool: an edit source must be visible in the conversation first (attached, or opened with `view_image`), and outputs land under `$CODEX_HOME/generated_images/` until you copy the accepted file into the project.

**Claude Code.** There is no built-in image tool. Delegate one non-interactive turn to the bundled Codex CLI through the wrapper; it owns `image_gen` and reuses the ChatGPT login, so no API key is involved.

`SKILL_DIR` is the directory this SKILL.md was loaded from; every `scripts/` and `references/` path is relative to it. Invoke scripts through `bash` and `swift` so a copy without an executable bit still runs.

```bash
SKILL_DIR="$HOME/.codex/skills/openai-frontend-design"   # wherever this SKILL.md lives
bash "$SKILL_DIR/scripts/codex-generate-image.sh" --out design/assets/generated/hero-scene.png --prompt-file /tmp/hero-prompt.txt
bash "$SKILL_DIR/scripts/codex-generate-image.sh" --out design/assets/generated/hero-scene-v2.png --edit design/assets/generated/hero-scene.png --prompt-file /tmp/hero-edit.txt
bash "$SKILL_DIR/scripts/contact-sheet.sh" design/assets/generated
```

The wrapper attaches each `--edit` source to the turn, refuses to overwrite an existing `--out`, keeps the Codex original under `~/.codex/generated_images/`, enforces `--timeout` itself (default 600 s), and confirms the result from the filesystem. It prints the subagent's `SAVED`, `ORIGINAL`, `METADATA`, `ASSUMPTIONS`, then its own `VERIFIED_ON_DISK` and `sips` metadata.

The delegated turn is a generator, not a design partner. You write the complete prompt from the direction. `VERIFIED_ON_DISK` is the evidence that a file exists; `ASSUMPTIONS` tells you whether the subagent changed the subject, palette, background, or composition, which means a rewritten prompt and a new path. Look at every file before accepting it. When no file lands, report the blocker.

## Guardrails

- **Authorization.** Invoking this skill, or asking for OpenAI/GPT-generated frontend imagery, authorizes generation through the route above, new local image assets, and non-destructive matting to new paths inside the stated scope. Other model routers, dependency installation, overwriting or deleting existing assets, remote uploads, commit, push, publish, deploy, a wider Codex sandbox than `workspace-write`, and `--dangerously-bypass-approvals-and-sandbox` each need separate approval.
- **Model identity.** The built-in tool exposes no trustworthy model ID and the delegated route adds a second hop. Name an exact model only when the tool proves it; otherwise write `OpenAI native image generation / model ID unverified` (plus `via delegated Codex turn` on Claude Code). The Codex model from `-m` or `config.toml` drives the turn and is not the image model.
- **Product truth.** Real copy, data, labels, and controls live in HTML. Illustrations set the mood and tell the story; they never stand in for data, controls, or features that do not exist.

## Delivery evidence

Report per the checklist in `design-critique.md`, labeling each claim `已驗證`, `Observed`, `Provisional`, `Uncertainty`, or `未執行`. An element or a page is called finished only after you have looked at it.
