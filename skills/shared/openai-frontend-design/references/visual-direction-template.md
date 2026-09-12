# Visual direction template

Copy this skeleton to `design/visual-direction.md` (or the repo's equivalent) and fill it in during the direction pass. Keep it compact: a designer's brief to themself, not a specification. Every section below is filled before the checkpoint; the element list is what the user approves.

```markdown
# <Page name> visual direction

## What this page is
Subject: <one sentence>
Audience: <one sentence, who and what they need>
Single job: <one sentence, what the page must make happen>

## Design thesis
<Two or three sentences: the idea the page makes believable, and the feeling it opens with and ends on.>
Signature: <the one memorable element this page will be remembered by, and why it belongs to this subject>

## Visual Genome
physical_world: <one buildable or photographable world, or none>
graphic_language:
  primary: <one>
  contrast: <zero or one>
display_medium: none | <one local treatment and where it appears>
motion_grammar: none | <one narrative motion logic>
image_transformation:
  primary: <one>
  supporting: <zero or one>

## Palette and type leanings
Palette: <4 to 6 named hex values with their roles>
Display face: <family or character, used where>
Body face: <family or character>
Utility face: <optional, captions or data>

## Illustration style
<One paragraph: medium and finish (painted, cut paper, photoreal, 3D clay, ink...), line and edge quality, light, color density, level of detail, how people or objects are drawn, what stays consistent across every element.>
Realism mode: <documentary | commercial photography | editorial illustration | stylized 3D | ...>
Continuity: <the motif, light, or framing that repeats>

## References
primary-anchor: <what it is, which quality transfers>
secondary-anchor: <...>
supporting-reference: <one named transferable property>
negative-reference: <what to steer away from>
Anti-copy note: <which of the last directions this one differs from and how, or "Uncertainty: no recent direction evidence available">

## Elements
| id | role | section | rendered_size | alpha_route | medium | prompt_draft | status |
|---|---|---|---|---|---|---|---|
| hero-scene | background scene | hero | full-bleed, 1440x720 desktop / 390x600 mobile crop | none | generated-raster | <one line> | planned |
| feature-spot-1 | spot illustration | features | 480px wide | transparent | generated-raster | <one line> | planned |
| step-icons | control icons | how it works | 24px | none | vector | (SVG, not generated) | planned |

## Deliberately not generated
- <element>: <why SVG, CSS, or nothing serves it better>

## Questions for the user
- <anything that would change the direction or the element list>
```

Field notes:

- `rendered_size` is the CSS size the element actually occupies, with the mobile size when it differs. It drives the medium decision: small or finely detailed pieces lean vector.
- `alpha_route` is `none` for scenes, textures, and self-backed illustrations; `transparent` for an isolated subject the tool should return with real alpha; a key color (`green`, `blue`, `magenta`) when transparent output did not come back real.
- `medium` is `vector`, `generated-raster`, or `compare` when a branded piece around 32 to 96px could go either way.
- `status` moves from `planned` to `pass`, `correctable`, `regenerate`, or `fallback` during the element pass.
