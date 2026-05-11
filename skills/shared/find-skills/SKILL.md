---
name: find-skills
description: Helps discover and install agent skills when a capability may already exist as a reusable skill.
compat: [claude-code, codex]
trigger: /find-skills
metadata:
  short-description: Find and install reusable skills from the skills ecosystem
---

# Find Skills

Use this skill when someone asks:

- "有沒有這種 skill"
- "幫我找可以做 X 的 skill"
- "能不能擴充這個 agent 的能力"
- "這需求是不是已經有人做成 skill 了"

## Search

```bash
npx skills find "query"
```

Examples:

```bash
npx skills find "react performance"
npx skills find "pr review"
npx skills find "telegram automation"
```

## Install

```bash
npx skills add <owner/repo@skill>
npx skills add <owner/repo@skill> -g -y
```

## Notes

- Browse at `https://skills.sh/`
- Prefer specific search terms
- If nothing relevant exists, implement directly instead of forcing a poor skill match
