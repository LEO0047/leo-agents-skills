# Frontend Visual Technology Capability Map

Use technology only after the narrative, layout, Visual Genome, real content, and signature interaction are defined. A package is an implementation route, not an aesthetic identity or proof of quality.

## Selection contract

For every non-trivial technology recommendation, record:

```text
Capability needed: [the concrete visual or interaction problem].
Trigger evidence: [why the current design cannot express it well with the existing stack].
Candidate: [existing repo capability or verified package].
Current verification: [maintenance, compatibility, license, and stack evidence checked this turn].
Cost: [dependency, bundle, rendering, authoring, and maintenance impact].
Accessibility/performance fallback: [what users receive without the effect].
Authorization: [already present | approval required before installation].
```

If the capability is unnecessary, use the existing stack. Do not recommend a package to make a straightforward information page appear more advanced.

## Capability routes

| Capability | Think of | Trigger | Do not use when | Fallback |
|---|---|---|---|---|
| UI motion and layout rhythm | Motion or the repo's existing motion layer | Gestures, springs, layout transitions, scroll-linked reveal, or state choreography materially clarifies hierarchy | Every element would animate independently, CSS already covers the state, or motion becomes the signature without subject meaning | CSS transitions/keyframes or static hierarchy |
| High-fidelity authored scene | Theatre.js or an existing timeline system | A verified 3D/HTML/SVG hero needs designed camera, light, assembly, or parameter choreography | The public project status, framework compatibility, authoring workflow, or maintenance cost is uncertain | Motion, a small custom timeline, video, or image sequence |
| 3D product and DOM synchronization | Three.js/React Three Fiber with r3f-scroll-rig when compatible | The product is genuinely spatial and WebGL objects must align with real DOM content during scroll | 3D is decorative, accessible HTML would be replaced, the project is not React-compatible, or mobile cost is unjustified | High-quality 2D, video, image sequence, or static model views |
| Signal, CRT, optical, or state postprocessing | pmndrs/postprocessing or a verified shader path | A specific display medium, recorded source, error, or transition needs scanline, noise, glitch, color, or optical behavior | The effect would cover the whole site, reduce text clarity, ignore state, or substitute for art direction | CSS blend/overlay, pre-rendered asset, or no effect |
| Fast local effect prototype | React Bits or an equivalent existing component | One text, image, or background event needs rapid exploration before a hand-built final choice | Multiple unrelated components would be assembled across the page or licensing/stack implications are unclear | Implement the selected effect directly with existing utilities |
| Product-specific generative pattern | CSS Doodle | A pattern can be derived from real geometry, fabrication data, material grain, or brand structure | It becomes random decoration or introduces a custom runtime for a static result | SVG, CSS background, or exported static asset |
| Lightweight shader surface | Paper Shaders or a verified local shader | A masked texture or surface behavior adds subject-specific meaning and device support is acceptable | A static image is enough, readability suffers, or a pre-1.0 dependency is not pinned | Static raster/video, CSS gradient, or existing Canvas/WebGL code |
| Smooth-scroll synchronization | Lenis or the repo's existing scroll layer | A long-form narrative or WebGL scene requires one coordinated scroll loop | Native scroll already works, anchors/sticky behavior would become fragile, or the page is simple | Native scrolling |
| Sci-fi UI language study | Arwes as reference only | Studying framing, sequential reveal, sound, or information rhythm | Choosing a production component framework or copying an entire sci-fi control-panel identity | Reimplement only the justified language in the existing design system |

Official research starting points:

- [pmndrs/postprocessing](https://github.com/pmndrs/postprocessing)
- [DavidHDev/react-bits](https://github.com/DavidHDev/react-bits)
- [motiondivision/motion](https://github.com/motiondivision/motion)
- [theatre-js/theatre](https://github.com/theatre-js/theatre)
- [14islands/r3f-scroll-rig](https://github.com/14islands/r3f-scroll-rig)
- [css-doodle/css-doodle](https://github.com/css-doodle/css-doodle)
- [paper-design/shaders](https://github.com/paper-design/shaders)
- [arwes/arwes](https://github.com/arwes/arwes)
- [darkroomengineering/lenis](https://github.com/darkroomengineering/lenis)

These links are discovery starting points, not timeless endorsements. Recheck the official repository and documentation during the task. As of the 2026-07-20 research snapshot, special caution was required for Theatre.js public-development visibility, Paper Shaders pre-1.0 version pinning, and Arwes production readiness. Treat that snapshot as potentially stale.

## Effect budget

Per page, default to:

- one primary motion grammar;
- one background effect;
- one signature microinteraction.

An effect that is reused as part of the same grammar does not count as a new language. A visually unrelated animation does. If the page exceeds the budget, document the narrative job and fallback for every additional effect, then remove any effect that does not encode meaning.

CRT, VHS, glitch, chromatic aberration, scanlines, noise, dithering, and bloom must attach to a display medium, content source, transition, or state. Never apply them globally because they looked successful in another project.

## Live verification gate

Before naming a third-party tool as the implementation choice:

1. Inspect the repo's current framework, runtime, dependencies, rendering boundary, motion utilities, and browser targets.
2. Verify the candidate's current official documentation, maintenance state, license, peer dependencies, framework compatibility, server/client constraints, accessibility implications, and fallback path.
3. Prefer an existing project dependency or native browser capability when it can meet the same design job.
4. Estimate loading, GPU, mobile, reduced-motion, and authoring costs in proportion to the feature.
5. Obtain explicit approval before adding, removing, or upgrading a dependency or changing a lockfile.

If live verification cannot be completed, mark the candidate `Provisional` and plan the fallback instead of presenting it as the selected production route.

## Accessibility and performance

- Keep content, controls, focus order, navigation, labels, and essential state in semantic HTML.
- Provide a static reduced-motion route that preserves hierarchy and product meaning.
- Do not block scroll, focus, text selection, anchor links, or reading order for a visual effect.
- Pause or reduce expensive work when offscreen, backgrounded, on constrained devices, or under reduced motion when the repo supports such policies.
- Test first load, resize, orientation, mobile GPU behavior, image completion, layout stability, horizontal overflow, and browser-console errors.
- When a WebGL or Canvas surface fails, its HTML neighbor must still communicate the section job and conversion path.
