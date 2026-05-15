# Output Format Policy

This file is the agent-facing source of truth for choosing between HTML artifacts and Markdown outputs for Leo's local workflows.

## Core rule

- Use self-contained `.html` for long-form outputs that Leo is meant to read, compare, revisit, or hand off visually.
- Use `.md` for agent-facing rules, memory notes, skills, commands, handoff prompts, operating instructions, and durable docs that another agent should parse or edit.
- Keep short chat replies and ordinary status updates as Markdown in the conversation.

## Use HTML for Leo-facing artifacts

Prefer HTML when the output is mainly for Leo to read or review:

- Long reports, comparisons, audits, tuning notes, and model/runtime status pages.
- Handoff pages that benefit from sections, cards, tables, risk labels, verification, or next-step options.
- Dashboards, interactive references, one-off editors, and visual summaries.
- Content that will be opened repeatedly as a readable local reference.

When creating local HTML on this machine, follow the style currently exemplified by `C:\Users\leo04\OneDrive\桌面\LLM模型設定.html`. Treat that file as an example, not a required dependency; if it is missing later, use the extracted style spec below:

- Dark operational dashboard.
- Compact cards and tables.
- Clear section headings.
- Evidence, verification, and A/B/C next directions.
- Self-contained CSS/JS with no external CDN or hidden network calls.

## Use Markdown for agent-facing material

Prefer `.md` when the output is mainly for agents, tools, or future maintenance:

- `AGENTS.md`, `SKILL.md`, README files, command docs, memory notes, and handoff prompts.
- Implementation plans meant to be pasted into Codex or Claude Code.
- Durable operating rules that should remain easy to diff and edit.
- Commit messages, PR descriptions, and other text expected to stay plain.

## Do not convert unrelated files

Do not rewrite these just to satisfy the HTML preference:

- Third-party README files.
- Hugging Face model cards.
- Generated transcripts.
- Reasoning logs.
- Civitai reproducible parameter notes.
- External tool documentation.

## Default delivery pattern

For substantial work:

- Produce the full user-facing artifact as HTML when it materially improves reading.
- Include a short Markdown summary in chat.
- Keep or create a compact `.md` source/policy/handoff when another agent will need to continue the work.
