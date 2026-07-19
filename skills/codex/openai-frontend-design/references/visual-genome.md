# Visual Genome and Leo Visual DNA

Use this reference before choosing a palette, image prompt, motion library, or named aesthetic. A Visual Genome separates the project's physical world, graphic language, display treatment, motion, and image processing so a prior project's complete look cannot silently become the next project's theme.

## Required contract

Record the following compactly before implementation:

```yaml
aesthetic_profile: brief-native | leo-visual-dna | named-genome | custom-reference-led
profile_reason: "Why this direction serves the audience and page job"
physical_world: "exactly one buildable or photographable world"
graphic_language:
  primary: "exactly one"
  contrast: "zero or one"
display_medium: none | "one local viewing or state treatment"
motion_grammar: none | "one narrative motion logic"
image_transformation:
  primary: "exactly one"
  supporting: "zero or one"
signature_interaction: none | "one subject-specific interaction"
forbidden_elements:
  - "bundle reuse or cliché that would break product truth"
text_safe_areas:
  desktop: "quiet region for real HTML"
  mobile: "quiet region or alternate crop"
reduced_motion_fallback: "static hierarchy and state behavior"
```

`none` is a deliberate choice. Never add CRT, WebGL, smooth scrolling, animation, or image processing just to fill a field.

## Five independent axes

### 1. Physical world

Choose one world that could be constructed, photographed, or consistently illustrated. It controls material, support, gravity, wear, environmental scale, and practical light.

Examples include a clean product studio, industrial test lab, archive and technical publication room, street repair shop, material library, consumer-electronics display space, underground broadcast studio, or humid urban workshop. These are prompts for reasoning, not a closed vocabulary.

Do not combine several environments merely to increase visual detail. If a section needs contrast, change camera distance, light intensity, or information density before changing worlds.

### 2. Graphic language

Choose one primary system for type, grids, rules, labels, and density. A contrasting secondary language is allowed only when it serves a clear narrative boundary.

Examples include industrial editorial, product catalogue, maintenance manual, computer magazine, fashion editorial, scientific publication, street fabrication marks, or archival finding aids. Structural devices must encode something true; do not add numbers, coordinates, warnings, or diagrams as decoration.

### 3. Display medium

Choose zero or one local viewing treatment such as monochrome CRT, amber terminal, color CRT, industrial LCD, e-paper, thermal paper, projection, oscilloscope, or no display device.

The display medium applies only to selected surfaces, scenes, or states. CRT is a camera or signal layer, not a skin. Do not apply global scanlines, terminal typography, chromatic aberration, glow, phosphor green, or glitch merely because a prior direction used them.

### 4. Motion grammar

Choose one motion logic derived from the subject: assembly, signal startup, camera tracking, print registration, scanning and measurement, tape search, CNC toolpath, disassembly and reconstruction, or `none`.

Use that grammar for the few transitions that matter. A stable page with one story turn is stronger than a page where every element floats, fades, or glitches independently.

### 5. Image transformation

Choose one primary treatment and at most one supporting treatment. Examples include product photography, dithering, halftone, ASCII, wireframe, thermal imaging, X-ray or material section, CRT/VHS, photocopy contrast, color registration shift, depth mapping, or lens refraction.

The transformation must reveal product meaning, material evidence, state, or narrative time. Do not use it as a generic surface filter.

## Leo Visual DNA

Use `leo-visual-dna` only when the brief and existing design system leave meaningful art-direction choices open. It is a preference for judgment, not a mandatory look.

| Gene | Transferable behavior | It does not require |
|---|---|---|
| `content_order` | One clear idea per screen, deliberate whitespace, stable hierarchy, product-first composition | White backgrounds, one font family, familiar device mockups, or copied layouts |
| `product_drama` | Contextual reveal, large but controlled imagery, concise stakes, and selective contrast | Black pages, constant video, cinematic haze, or oversized text everywhere |
| `mission_scale` | Milestones, sequence, operational clarity, genuine scale, and consequential progress | Rockets, countdowns, fake coordinates, mission numbers without real meaning, or militarized copy |
| `engineering_signature` | Credible materials, assembly, manufacturing evidence, measurement, calibration, and signal behavior | Wood, CRT, cyberpunk, cyan light, dark mode, or decorative technical labels |

### Mode routing

| Mode | Use when | Planning weight | Default restraint |
|---|---|---|---|
| `Product Reveal` | A product, object, portfolio piece, furniture item, or release needs a controlled unveiling | `60 / 30 / 10` content order / product drama / engineering signature | Minimal display effects; engineering evidence appears only where it explains the object |
| `Mission Launch` | A program, AI initiative, future concept, or long-term roadmap needs stakes and sequential progress | `30 / 55 / 15` content order / product drama plus mission scale / engineering signature | Use real milestones and dates only; no fake telemetry or ornamental control-room UI |
| `Signal Workshop` | Craft, prototyping, manufacturing, repair, R&D, or process is central to the value | `35 / 20 / 45` content order / product drama / engineering signature | Display treatments stay inside inspection, process, or recorded-evidence surfaces |

Weights express emphasis only. Do not map them to literal CSS percentages, color coverage, component counts, or prompt word counts.

If the product is healthcare, government service, education, children, finance, safety-critical, or another domain where the default genes could reduce trust or clarity, start from `brief-native`. Add a Leo gene only when it concretely improves the task.

## Named assembled genomes

These are examples of coherent combinations, not global presets. Rebuild or reject them when the brief conflicts.

### material-nocturne

- Profile: optional `Signal Workshop` variant.
- Physical world: humid Taiwan night workshop or material room.
- Graphic language: archival or research-publication discipline.
- Display medium: none by default; local industrial LCD or CRT only for evidence surfaces.
- Motion grammar: calibration, measurement, or assembly.
- Image transformation: physically credible product/environment photography with restrained signal treatment.
- Materials: near-black graphite, dark walnut or layered birch when the real subject uses them, blackened steel, anodized metal, smoked resin, restrained brass, believable wear and fingerprints.
- Light: motivated cyan or violet practical light with sparse accent color; neutral materials and shadows remain neutral.
- Forbidden: global neon edging, ornamental HUDs, fake glyphs, sterile collectible renders, excessive bloom, or transferring unrelated subjects from a reference.

### Industrial Signal Lab

- Physical world: real product or fabrication test lab.
- Graphic language: industrial editorial plus truthful machining drawings.
- Display medium: local amber terminal or measurement display.
- Motion grammar: measure, cut, calibrate.
- Image transformation: clear product photography with limited dither for process evidence.

### Pirate Fabrication Broadcast

- Physical world: underground studio and independent broadcast room.
- Graphic language: tape labels, repair notes, and photocopied cultural ephemera.
- Display medium: color CRT or VHS only for recorded segments.
- Motion grammar: tune, search, interrupt.
- Image transformation: low-resolution recorded material contrasted with high-resolution product close-ups.
- Forbidden: using degraded video where material detail or purchasing decisions require clarity.

### Future Material Archive

- Physical world: bright material archive or future-facing museum store.
- Graphic language: scientific publication and specimen catalogue.
- Display medium: e-paper with optional local monitoring display.
- Motion grammar: file expansion and sectional analysis.
- Image transformation: large material macro photography with one depth, X-ray, or cross-section treatment.
- Default: light surfaces are valid and preferred when they improve specimen reading; do not fall back to dark mode.

### Kinetic Assembly

- Physical world: minimal product presentation space.
- Graphic language: premium product catalogue.
- Display medium: none until a truthful final inspection state requires one.
- Motion grammar: assembly and disassembly.
- Image transformation: real material photography or a verified 3D model.
- Default: scroll progression carries the manufacturing story; avoid unrelated background effects.

## Research provenance and transfer boundary

The Leo Visual DNA genes were informed by public research into product clarity, launch storytelling, mission sequence, and engineering presentation. Source examples may include official public material from Apple, Tesla, SpaceX, and industrial-design references, but those brands are provenance, not prompt commands.

Research starting points from the 2026-07-20 review:

- [Apple Events](https://www.apple.com/apple-events/) and [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Tesla We, Robot](https://www.tesla.com/zh_tw/we-robot)
- [SpaceX launches](https://www.spacex.com/launches/)

Revisit the official sources when current claims matter. Do not treat a dated research snapshot as proof of a current page, product, or design system.

Translate references into content order, contrast, camera behavior, scale, sequencing, material response, and interaction principles. Never copy brand navigation, layouts, identity, slogans, product language, typography, icons, page sequence, or complete visual trade dress.

## Anti-copy check

Use only safe evidence already available in the current task, workspace, or explicitly provided memory. Never create or update durable memory as part of this check.

Compare the proposed direction with up to three recent completed directions across:

1. dominant palette;
2. display-type character;
3. layout skeleton;
4. hero composition;
5. motion grammar;
6. image treatment;
7. signature interaction.

If three or more repeat as a bundle, change at least one Visual Genome axis and state what changed. Repeating one justified gene such as content order is acceptable; repeating a full visual package is not.

When evidence is unavailable, write:

```text
Uncertainty: recent visual-direction evidence unavailable.
Fallback check: compared against the base frontend skill's generic AI-design defaults and revised any matching bundle.
```

## Scenario routing checks

- A fabrication workshop may route to `Signal Workshop`; CRT remains inside inspection or process evidence.
- A bright archive may route to `Future Material Archive`; the direction must not revert to black graphite or cyan-violet night lighting.
- A healthcare or government service begins `brief-native`; engineering signature stays absent unless it explains a real operational task.
- A simple information page can use `motion_grammar: none`, `display_medium: none`, and no third-party visual package.
- A three-dimensional product story may use `Kinetic Assembly`, but the need for 3D does not authorize dependency installation.
