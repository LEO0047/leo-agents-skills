# Frontend Delivery Quality Gate

Apply this gate when implementing or materially reshaping a frontend. For a quick concept-only exploration, state which verification steps were not run.

## Before implementation

- Read the closest repo instructions and inspect the existing design system, tokens, components, content, and interaction patterns before changing the UI.
- Define the audience, the screen's single job, the design thesis, and one signature element. Prefer real product content; do not invent data, capabilities, charts, or states that imply nonexistent functionality.
- Preserve product logic unless the user explicitly requests behavior changes. Use existing utilities, components, and tokens where they fit.

## During implementation

- Spend visual boldness in one justified place. Keep surrounding typography, hierarchy, spacing, alignment, and motion disciplined.
- Cover the states relevant to the changed surface: default, hover, focus, active, disabled, loading, empty, and error. Do not add irrelevant states solely to satisfy this list.
- Maintain semantic HTML, visible keyboard focus, usable contrast, reduced-motion behavior, and responsive layouts.

## Visual verification

- When the environment supports it, run the UI and inspect screenshots at representative desktop and mobile sizes. Use the repo's established targets; otherwise start with approximately `1440x900` and `390x844`.
- Perform at least one critique-and-correction pass after seeing the rendered result. Check product fit, hierarchy, typography, spacing, alignment, responsive behavior, interaction clarity, and unnecessary decoration.
- Run the smallest relevant lint, typecheck, test, or build command after the visual pass.
- Report screenshot review, responsive review, and automated checks separately. Never call an uninspected implementation visually verified.

## Routing

- Use the repo or global routing rules for specialized review skills such as `web-design-guidelines`, `ui-density-reduction`, `visual-reference-implementation`, and `vercel-react-best-practices`; do not duplicate their full guidance here.
