Convert the approved Opus plan or implementation context below into a constrained Codex rescue handoff prompt.

Input:
$ARGUMENTS

Output only the final paste-ready handoff prompt.

Do not:
- Do not execute Codex.
- Do not modify files.
- Do not run tools.
- Do not include commentary before or after the handoff prompt.
- Do not ask Codex to "do the plan" without constraints.

The output must be ready to paste after:

/codex:rescue --background

Use this exact structure:

## Goal
## Context
## Git / execution preconditions
## Allowed scope
## Do not
## Implementation constraints
## After implementation
## Verification steps
## Risks / follow-up

Strict requirements:
- Prefer smallest safe patch.
- Stay within allowed scope.
- Do not perform broad refactors.
- Do not redesign unrelated UI.
- Do not add dependencies unless unavoidable.
- Do not invent facts, policy dates, fake freshness data, or fake migration information.
- Do not push, open PRs, or write to remote services.
- Do not ask Codex to create branches, switch branches, stage files, commit, stash, reset, merge, rebase, push, open PRs, or manipulate `.git/index.lock`.
- If the approved plan includes Git write steps, convert them into user/outer-Claude preconditions or follow-up notes, not Codex tasks.
- Allow only read-only Git verification commands such as `git status --short`, `git diff --stat`, `git diff --name-only`, and `git diff --check`.
- If the repo is on the wrong branch or Git write access is blocked, Codex must stop and report the blocker instead of trying to fix Git state.
