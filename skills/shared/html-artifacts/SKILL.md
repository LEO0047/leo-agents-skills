---
name: html-artifacts
description: "Use when deciding whether an agent output should become a self-contained HTML artifact instead of Markdown, especially for long plans, PR reviews, architecture explanations, visual comparisons, reports, or one-off interactive editors."
compat: [claude-code, codex]
trigger: /html-artifacts
metadata:
  short-description: "Create rich HTML artifacts only when they materially improve review, comparison, visualization, or interaction."
tags: [html, artifacts, output-format, review, handoff]
---

# html-artifacts

Choose HTML only when it materially improves human review, comparison, visualization, handoff, or interaction. Keep Markdown as the default for short, durable, and human-edited text.

## Decision rule

Default to Markdown unless at least one condition is true:

- The output will likely exceed about 100 lines and needs navigation.
- The user needs to compare options side by side.
- The task is a PR review, annotated diff, risk map, module map, or architecture walkthrough.
- The content benefits from diagrams, timelines, tables with visual priority, color-coded severity, UI mockups, or design tokens.
- The user needs to tune, sort, triage, preview, or edit structured data interactively.
- The output is meant for handoff to another human or agent and needs evidence, risks, and next actions in one readable artifact.

Do not use HTML for:

- Short answers, status updates, ordinary final responses, or simple command output.
- README, AGENTS.md, SKILL.md, commit messages, PR descriptions, or other durable text expected to stay hand-editable.
- Simple patch summaries where Markdown is easier to diff.
- User requests that explicitly ask for Markdown, plain text, JSON, or another format.

## Artifact requirements

When producing an HTML artifact:

- Create one self-contained `.html` file with inline CSS and JavaScript.
- Do not use external CDNs, external fonts, hidden network calls, trackers, or remote assets unless the user explicitly asks.
- Make it readable on mobile and desktop; include print-friendly styles for reports.
- Include `TL;DR`, `Files read / evidence`, risks, verification, and A/B/C next directions when relevant.
- Use semantic sections, accessible labels, keyboard-friendly controls, and enough contrast.
- Keep generated HTML as an output artifact, not as the canonical source for long-term prose when Markdown would be easier to maintain.

## Interaction requirements

For one-off editors, dashboards, or tuners:

- Keep all sample data and logic inside the file.
- Provide Reset.
- Provide at least one export path: `Copy as markdown`, `Copy diff`, `Copy JSON`, or `Copy prompt`.
- Surface dependency conflicts, validation warnings, or risky choices inline.
- Make exported text suitable to paste back into Codex, Claude Code, a PR, or a planning doc.

## Recommended structures

Use these patterns when they fit:

- **Implementation plan**: TL;DR, milestones, data flow, mockups, key code, risk table, open questions, verification.
- **PR review**: summary, risk map, annotated diff, blocking/worth-a-look/nit findings, suggested fixes, test gaps.
- **Feature explainer**: files read, request path, config examples, gotchas, FAQ.
- **Design reference**: tokens, component variants, states, spacing, typography, copyable snippets.
- **Incident/status report**: headline metrics, timeline, root cause, impact, action items, sources.
- **Interactive editor**: editable state, warnings, preview, reset, export.

## Prompt skeleton

```text
Create a self-contained HTML artifact only if HTML materially improves this output.
If Markdown is sufficient, explain briefly and use Markdown instead.

When using HTML:
- inline all CSS/JS
- no external CDN or hidden network calls
- include TL;DR, Files read / evidence, risks, verification, and A/B/C next directions when relevant
- make it mobile-readable and print-friendly
- for interactive artifacts, include Reset and Copy as markdown / Copy diff / Copy prompt
```
