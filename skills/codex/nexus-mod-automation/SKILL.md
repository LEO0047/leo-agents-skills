---
name: nexus-mod-automation
compat: [codex]
description: Automate safe Nexus Mods and Vortex workflows for game mod recovery or setup. Use when Codex needs to queue Nexus downloads through Chrome/Vortex, monitor Vortex downloads, inspect mod archives, identify install candidates, quarantine duplicates or extras, prepare reports, or hand off load order work to a game-specific adapter without redistributing third-party mod payloads.
---

# Nexus Mod Automation

Use this skill for generic Nexus Mods + Vortex automation. Keep it game-agnostic: the core workflow queues downloads, monitors Vortex, inspects archives, and reports candidates. Put game-specific validation in adapters such as metadata checks, plugin checks, or load-order tools.

## Safety Rules

- Use the user's browser session for Nexus pages only when the user has requested browser automation or the Chrome plugin is already the right tool.
- Do not bypass Nexus login, adult-content gates, paid access, Cloudflare, rate limits, or author download restrictions.
- Do not redistribute downloaded payloads. Keep archives and extracted mod files local.
- Do not execute downloaded scripts, installers, DLLs, EXEs, BAT/CMD files, or unknown binaries.
- Do not delete payloads by default. Move extras to a timestamped quarantine folder when cleanup is requested.
- Do not claim compatibility unless a game-specific adapter verifies it.

## Workflow

Read [references/workflow.md](references/workflow.md) for the full operational flow.

1. Discover source pages and exact Nexus file IDs.
2. Queue downloads in Chrome by clicking `Mod manager download`, accepting the Nexus requirements popup, then clicking `Slow download`.
3. Monitor `%APPDATA%\Vortex\downloads\<game-id>` with `scripts/scan-vortex-downloads.ps1`.
4. Inspect downloaded archives with `scripts/inspect-mod-archives.ps1`.
5. Pass candidates to the game-specific adapter for metadata, hash, manifest, plugin, or load-order validation.
6. Install or quarantine only after the adapter and user request make the action safe.
7. Produce a short report: queued, downloaded, pending/locked, verified, installed, quarantined, blocked, and warnings.

## Chrome/Nexus Handling

Prefer semantic browser actions:

- Open `https://www.nexusmods.com/<game>/mods/<mod-id>?tab=files&file_id=<file-id>`.
- Click `Mod manager download` or navigate to the `nmm=1` requirements popup URL.
- If the page shows `Additional files required`, click `Download`.
- Click `Slow download`.
- Wait a few seconds, then continue with the next file.

If Chrome automation cannot access a Nexus page because of browser policy, login, age gate, or Cloudflare, stop and report the exact blocker. Do not work around the gate.

## Vortex Monitoring

Use:

```powershell
powershell -ExecutionPolicy Bypass -File "$skillRoot\scripts\scan-vortex-downloads.ps1" -GameId "<game-id>" -Json
```

The script is read-only. It reports file size, last write time, locked state, and whether the file size is stable across a short sample interval.

## Archive Inspection

Use:

```powershell
powershell -ExecutionPolicy Bypass -File "$skillRoot\scripts\inspect-mod-archives.ps1" -ScanPath "$env:APPDATA\Vortex\downloads\<game-id>" -Json
```

The script lists archive contents without extracting into the game directory. It detects common mod payload types such as `.pak`, `.esp`, `.esm`, `.esl`, loose files, executables, DLLs, and scripts.

## Game Adapters

Read [references/game-adapters.md](references/game-adapters.md) before making game-specific claims or writing load orders. Use the adapter to verify archive candidates against the target game's metadata, plugin, manifest, hash, folder, or load-order conventions.

The generic Nexus/Vortex workflow ends at safe candidates and reports. Installation, loose-file placement, and load-order exports belong to the game adapter.
