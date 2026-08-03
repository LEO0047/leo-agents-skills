---
name: raid-shadow-legends-ops
compat: [codex]
description: Use when operating RAID Shadow Legends through Computer Use, especially Traditional Chinese UI champion naming, dungeon/event farming, campaign or dungeon progression, champion equipment, artifact upgrades, food/low-level champion leveling, fast click coordinates, and safe stop rules.
metadata:
  short-description: RAID Shadow Legends fast ops
---

# RAID Shadow Legends Ops

Use this skill for `RAID: Shadow Legends` live gameplay tasks. The user's UI is Traditional Chinese, so user-facing reports must use Traditional Chinese champion and mode names such as `凱爾`, `菲恩`, `歸魂納爾瑪`, `流浪者愛麗絲`, `副本`, `靈魂城堡`, and `奧術城堡`.

## Safety Contract

- Do not buy packs, spend real money, use red gems, refill energy, confirm paid prompts, or modify account/payment settings.
- Stop on purchase, refill, resource shortage, account, login, or irreversible confirmation prompts.
- Do not sacrifice/eat champions, change Great Hall, or perform rank-up/ascension unless the user explicitly asks.
- If the user adjusts a team manually, preserve that team and continue from it.
- If a battle fails or the team clearly cannot progress, stop and report the stage.

## Fast Operating Pattern

Prefer direct macOS `CGEvent` clicks for repeatable RAID UI targets after one `Computer Use` screenshot confirms state. `Computer Use` coordinate clicks are sometimes slower or less reliable.

Default to fast reaction:

- Load this skill before doing RAID gameplay work.
- Use one screenshot/state read to confirm the screen, then act with known fast coordinates when safe.
- Avoid repeated explanatory pauses during farming; give short progress updates only at meaningful checkpoints, failures, prompts, or user interruptions.
- Preserve user-adjusted teams and continue from the current screen whenever possible.
- Do not browse the web during live gameplay unless the user asks for strategy research or a decision depends on current event/rules data.

Use this one-click Swift pattern, changing only `x` and `y`:

```bash
swift -e 'import Cocoa
let loc = CGPoint(x: 1338, y: 900)
let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: loc, mouseButton: .left)
let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: loc, mouseButton: .left)
down?.post(tap: .cghidEventTap); usleep(90000); up?.post(tap: .cghidEventTap)'
```

Before a click sequence, check the current app state once:

```text
mcp__computer_use__.get_app_state app="com.plarium.raidlegends"
```

Known window shape during this run: macOS window roughly `1512 x 949`, positioned around `(0, 33)`. Re-check with `osascript` if coordinates drift.

## Known Fast Coordinates

These are Swift screen coordinates for the current Mac/window layout. Verify visually before relying on them after relaunch or resize.

- Battle/result `繼續`: `(1338, 900)`.
- Stage battle/start button on the right: usually `(1337, 902)`; stage list row 2 battle button `(1336, 299)`, row 3 `(1337, 445)`.
- Top-right close/back from team screen: `(1450, 61)`.
- Main city bottom `戰鬥`: `(1370, 893)`.
- Main city bottom `英雄`: `(1160, 925)`.
- Artifact upgrade right-bottom blue `升級`: `(1085, 903)`. Use this for controlled +1 upgrades; avoid yellow instant/auto upgrade unless explicitly asked.
- Common team-grid champion slots on the left: top-left `(214, 266)`, top-right `(353, 301)`, mid-left `(214, 450)`, mid-right `(353, 450)`, leader `(498, 349)`.
- Bottom roster visible slots: row1 col1 `(68, 737)`, row1 col2 `(143, 737)`, row2 col1 `(68, 829)`, row2 col2 `(143, 829)`, row3 col1 `(68, 927)`, row3 col2 `(143, 927)`.

## Dungeon Progression

When the user says to run timed/event dungeons or "打到打不過":

1. Use visible timed/event dungeons first, such as castles with countdown timers.
2. Start from the next available stage and use `繼續` after each win.
3. If the game returns to team selection, keep the current user-approved team and press `開始`/`繼續`.
4. Use low-level but valuable champions as experience passengers when the user wants leveling efficiency.
5. Track the last cleared stage, visible energy, and notable level-ups.
6. Stop on defeat, payment/resource prompts, or user interruption.

## Session Checkpoints

Before resuming an interrupted RAID session, check for the latest RAID handoff/checkpoint notes in:

```text
~/.codex/memories/extensions/ad_hoc/notes/
```

Look for filenames matching `*raid*checkpoint*.md`, `*raid*session*.md`, or `*raid*maintenance*.md`. Treat the newest relevant note as the current temporary gameplay state. These notes may contain last cleared stages, failed stages, maintenance status, visible resources, and user-adjusted team constraints.

Known current checkpoint file from this workflow:

```text
~/.codex/memories/extensions/ad_hoc/notes/20260519-191242-raid-maintenance-session-checkpoint.md
```

Do not commit these ad-hoc checkpoint notes to the skill repo. They are local session memory, while this skill stores durable operating rules.

Current remembered RAID priorities from this account:

- Core carry: `流浪者愛麗絲`.
- Useful core/support/damage: `歸魂納爾瑪`, `菲恩`.
- Early long-term leveling target: `凱爾`.
- Avoid wasting experience on champions already capped at 30 when a safe low-level passenger can ride along.

## Team Editing Heuristic

- Keep the carry and survival core unless the user changes them.
- If a slot is occupied by a capped 30-level non-core champion, it can be swapped for `凱爾` or another under-30 training target.
- Explain swaps briefly if asked; do not repeatedly change team composition once the user has adjusted it.

## Update Rule

This skill should improve itself during RAID work. When a faster or more reliable RAID method is discovered, update this skill in the same working session when doing so is safe and does not interrupt urgent gameplay.

Autonomous learning loop:

1. Notice friction: slow clicks, repeated tool timeouts, coordinate drift, unnecessary screen reads, team reset behavior, or new UI prompts.
2. Test the faster method on a low-risk action or after confirming the current screen.
3. If reliable, record it in this skill with the exact UI context and coordinate/workflow.
4. If the improvement should persist across sessions, add a short ad-hoc memory note under `~/.codex/memories/extensions/ad_hoc/notes/`.
5. If the improvement changes ownership between skills, update the delegating skill such as `game-modops-agent`.
6. Mention the update in the final report, including whether it was committed.

Record updates with:

- the exact UI context,
- the new coordinate or workflow,
- the stop condition it respects,
- whether it supersedes an older method.

Automatic learning must stay inside the safety contract: never learn a shortcut that bypasses purchase confirmations, spends red gems, sacrifices champions, or weakens the user's stop rules.
