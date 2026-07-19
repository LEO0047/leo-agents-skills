# OpenAI Frontend Evaluation Gates

Use these gates on generated assets and on the implemented page. Evaluate the real rendered context at intended size; detail or beauty in an isolated source image is not sufficient.

## Result states

| State | Meaning |
|---|---|
| `pass` | No blocker or unresolved major issue remains; required evidence was inspected |
| `correctable` | The subject is valid and a bounded prompt, crop, overlay, layout, or implementation correction can resolve the issue |
| `regenerate` | Subject, geometry, lighting, reference transfer, or composition is fundamentally wrong |
| `fallback` | A vector, CSS, static image, video, existing component, or simpler direction better serves the product |

Use `已驗證` only for checks actually completed this turn. Use `Observed` for inspected evidence without full end-to-end proof, `Provisional` for a promising but unresolved result, `Uncertainty` for unavailable evidence, and `未執行` for checks not run.

## Severity

### Blocker — reject immediately

- Product truth is wrong, or the art implies fake data, controls, features, measurements, endorsements, or operational state.
- A reference's people, identity, logo, text, interface, product language, recognizable layout, or complete trade dress was copied without authorization.
- A realism-critical subject has impossible construction, broken gravity, melted or repeated hardware, invalid assembly, or light that contradicts the geometry.
- Essential text, navigation, CTA, focus, reading order, or control semantics are obscured or replaced by pixels.
- The desktop or mobile layout has clipping, unreadable content, horizontal overflow, severe overlap, or a crop that removes the subject's meaning.
- Motion carries essential meaning with no reduced-motion fallback, traps interaction, or prevents the page from functioning when effects fail.
- A dependency, remote upload, model router, or other action outside the authorization boundary is required but not approved.

Any blocker yields `regenerate` or `fallback`; do not hide it with an overlay or screenshot edit.

### Major — correction required

- Text-safe space, focal hierarchy, crop, contrast, or CTA visibility fails in one required viewport.
- The section image is attractive but does not perform its narrative or conversion job.
- Neighboring sections look like unrelated image prompts rather than one visual world.
- Practical light, depth of field, haze, reflection, bloom, or surface wear remains implausible at intended size.
- Display effects or motion are global, repetitive, state-independent, or exceed the effect budget without narrative value.
- Three or more visual dimensions repeat as a bundle from recent directions when comparison evidence is available.
- First-load fonts, intrinsic image dimensions, reveal animation, sticky containment, or WebKit behavior creates a collision absent from the settled screenshot.
- Alpha exists but internal gaps, fine hardware, antialiased edges, or target-size detail contain key color, fringe, holes, or stair-stepping.

A major issue yields `correctable` when the underlying subject is sound; otherwise use `regenerate` or `fallback`.

### Minor — polish before verified delivery

- Local rhythm, texture contrast, overlay strength, small crop balance, or one transition is slightly off without affecting truth or use.
- A decorative edge defect appears only at master size and is absent at target size, but still needs an explicit acceptance decision.
- A supporting motif, label, or motion beat is redundant but does not alter meaning.

Minor issues may remain only when the user explicitly accepts them and the result is not labeled production-ready. Otherwise make the focused correction.

## Physical-world and anti-AI gate

Before prompting a realism-critical asset, state:

- what was built and how it is supported;
- material, fasteners, seams, ventilation, cable routing, scale cues, and wear;
- practical light sources and their direction;
- camera height, lens feel, focus, exposure, temperature, grain, and flare restraint;
- ordinary evidence of use such as repair, residue, tooling, calibration, dust, or fingerprints;
- likely failure modes for this subject.

Prefer a real place with credible interventions over generic concept art. Saturated light is a local source, not an outline applied to every edge. Reject fake glyphs, illegible signage, arbitrary cables, ornamental HUDs, uniform glow, collectible-render staging, and poster symmetry that destroys real HTML text space.

## Screenshot-directed QA

Capture after fonts, images, and initial transitions have settled:

1. a representative desktop viewport;
2. a narrow mobile viewport;
3. full-page or ordered key sections when narrative progression matters;
4. first-load and scrolled states when reveal, sticky, fixed, filter, transform, or intrinsic media behavior can change geometry;
5. browser-specific, CJK, or accessibility-focused captures when the changed surface creates those risks.

Inspect story continuity, text contrast, focus order, density, crop, CTA visibility, image loading, layout shift, horizontal overflow, console errors, reduced motion, and the transition into the next section. Correct the website or source asset, then recapture; never retouch a screenshot to conceal an implementation defect.

## Safari, CJK, and hidden-label collision gate

Large CJK display type that works in a full-width hero can fail inside a narrow split-grid column. Safari/WebKit may also expose hidden labels or controls when fixed descendants sit inside sticky, transformed, filtered, or backdrop-filtered ancestors.

- Size display headings against the rendered grid column, not only the viewport.
- Wrap approved CJK line groups explicitly. Apply `white-space: nowrap` only after responsive sizing proves that each group fits.
- Inspect every deliberate wrapper with `Range.getClientRects()` or equivalent; also assert `scrollWidth <= clientWidth`.
- Keep the real skip link at the document root. Do not reuse a focus-revealed `.skip-link` class for persistent labels.
- Avoid unnecessary sticky toolbars. When required, reserve flow space and inspect the toolbar after scrolling.
- Assert a positive gap between heading and toolbar, no horizontal overflow, and no visible one-pixel accessibility artifacts.
- When Safari evidence conflicts with Chromium, treat the Safari capture as evidence for Safari. Correct DOM and containment structure rather than adding screenshot-specific offsets.

Use a dedicated visually-hidden utility for persistent accessible labels:

```css
.visually-hidden {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  clip-path: inset(50%) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
```

## Asset-specific checks

- Background scenes and integrated heroes: preserve focal subject and HTML text-safe regions across desktop and mobile crops; do not require alpha.
- Isolated objects: verify alpha metadata plus checkerboard, near-white, and near-black previews at master and target sizes.
- Textures: verify tiling if required, low enough contrast under content, and no false control or data implication.
- Small branded assets: compare generated and vector candidates in the actual component; target-size clarity, theming, state needs, loading cost, and semantics outrank master-image detail.
- Above-the-fold decorative heroes: provide intrinsic dimensions, `alt=""`, and the repo's established high-priority loading treatment.

## Scenario acceptance

- `Signal Workshop`: CRT or signal behavior appears only in inspection, process, or recorded-evidence surfaces.
- `Future Material Archive`: a light specimen-led solution must remain possible and must not inherit dark graphite or cyan-violet night defaults.
- Healthcare or government service: the brief overrides Leo Visual DNA; no engineering or mission language without a truthful task reason.
- Simple information page: no WebGL, shader, smooth-scroll, or motion dependency recommendation without a concrete capability gap.
- 3D product narrative: a WebGL route may be `Provisional`, but installation remains blocked until approved and a static fallback is defined.
- Anti-copy: three or more repeated dimensions require a revised Visual Genome axis; absent history yields `Uncertainty`, not invented evidence.

## Delivery checklist

Report:

- selected Visual Genome and routing reason;
- anti-copy result;
- per-asset `pass`, `correctable`, `regenerate`, or `fallback` decision;
- exact blocker, major, and minor findings;
- correction made and recaptured evidence;
- alpha and edge evidence where relevant;
- desktop/mobile and additional targeted screenshots;
- accessibility, reduced-motion, browser, lint, typecheck, test, and build status;
- remaining `Provisional`, `Uncertainty`, and `未執行` items.
