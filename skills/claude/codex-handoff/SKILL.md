---
name: codex-handoff
description: Convert the approved Opus plan or implementation context below into a short, trust-first Codex rescue handoff prompt.
compat: [claude-code]
argument-hint: "[approved plan/context]"
disable-model-invocation: true
---

Convert the approved Opus plan or implementation context below into a short Codex rescue handoff prompt.

Input:
$ARGUMENTS

Treat Codex as a senior peer engineer. Hand over the goal and the *why*, then get out of the way. Codex decides scope, files, Git workflow, verification, and tradeoffs. Your job is to brief, not to contract.

Output only the final paste-ready handoff prompt — no commentary before or after. The output goes after:

/codex:rescue --background

Use this structure. Keep it short. If a section has nothing meaningful to add, write a one-liner or skip it.

## Goal

1–3 bullets. What does "done" look like, in user-visible or behavior-visible terms.

## Why it matters

One short paragraph or 2 bullets. Product intent, the bug's blast radius, or the design direction Codex needs to honor. Skip if obvious from Goal.

## What you should know

Only non-obvious context Codex cannot read from the repo:
- Prior incidents worth knowing (e.g. "v3.2 broke deploy by removing static export")
- Architectural invariants that must hold (e.g. "API stays in `functions/api/*`, no Next route handlers")
- Stakeholder/deadline constraints
- Anything sensitive (secrets policy, data handling)

If there is nothing of the sort, write "Read the repo — nothing non-obvious here."

## Ground rules

Keep this short. Default to two lines:

- Don't fabricate facts, dates, policy text, or migration data — verify or ask.
- Confirm with the user before pushing to remote, opening PRs, or anything externally visible/irreversible.

Add task-specific rules **only** if the input plan demands them (e.g. a hard architectural rule). Do not pad with generic "no broad refactors / no formatting churn" — trust Codex.

## Report when done

- What changed (`git diff --stat` or branch name is fine)
- Why this approach, briefly
- What you ran to verify, with key output
- Anything uncertain, risky, or worth a follow-up
- Any deviation from this brief, and your reasoning

## Rules for writing the handoff

- Do not execute Codex, modify files, or run tools while writing this prompt.
- Convert any branch/commit/push/PR steps from the input into "user follow-up" notes — do not preserve them as Codex tasks unless the input plan explicitly says Codex should do them.
- Do not invent constraints (file scopes, prohibitions, architectural rules) the input plan didn't mention.
- Do not pad. A 15-line handoff is better than a 60-line one. If "What you should know" is empty, say so in one line.
- If the input is vague, ask Codex to clarify in the report rather than guessing constraints into existence.
