---
name: game-mod-management
compat: [codex]
description: Use when working on a game mod management repository or local mod workflow, especially Baldur's Gate 3 save recovery, missing mod UUIDs, Vortex/BG3 Mod Manager workflows, manifests, source links, expected files, load order notes, backups, scan/install verification, reports, and safe local mod operations without redistributing third-party mod payloads.
---

# Game Mod Management

Use this skill for repositories and local workflows that manage game mods through manifests, scripts, reports, and backup points. BG3 is the first target, but keep the structure expandable for Skyrim, Cyberpunk 2077, Stalker, Kenshi, and other mod-heavy games.

For Nexus Mods browser automation, Vortex download queueing, Vortex download monitoring, archive inspection, duplicate quarantine, or generic Nexus/Vortex reports, use `$nexus-mod-automation` first. Return here only for game-specific manifests, verified metadata, install rules, save recovery, or load-order handoff.

## Core Principle

Treat the repository as a management blueprint, not a modpack payload.

- The repo stores process: manifests, links, expected filenames, UUIDs or hashes when known, load order notes, backup scripts, install scripts, verification reports, and local automation.
- The user's machine stores mod payloads.
- Nexus Mods, Mod.io, Steam Workshop, GitHub releases, author pages, or original mod pages remain the source of truth for downloadable assets.
- Never turn the repo into an unauthorized redistributed modpack.

## Hard Guardrails

- Do not commit third-party mod payloads: `.pak`, `.zip`, `.7z`, `.rar`, model files, textures, audio, or extracted mod assets.
- Do not commit executables or downloaded scripts from mod archives: `.exe`, `.dll`, `.bat`, `.cmd`, `.msi`, unknown `.ps1`.
- Project-owned scripts under repo script folders may be committed when they are authored for this repo and are safe by design.
- Do not bypass Nexus Mods, Mod.io, Steam Workshop, Patreon, adult-content gates, paid downloads, login gates, or rate limits.
- Do not guess UUIDs, hashes, dependency rules, compatibility, or load order constraints.
- Do not overwrite existing mod setups without a timestamped backup.
- Do not delete or disable existing mods unless the user explicitly approves.
- Do not install loose files into a game directory unless the mod instructions clearly require it and the user approves.
- Do not mix Vortex, BG3 Mod Manager, and manual flows on one profile without documenting which tool owns the profile.
- Do not commit private local paths, tokens, cookies, account data, or adult-content payloads.

## Default Repo Shape

Prefer this layout unless the repo already has a clear convention:

```text
game-mod-management/
|- README.md
|- games/
|  `- bg3/
|     |- README.md
|     |- manifest/
|     |  |- mods.yml
|     |  |- collections.yml
|     |  |- known-uuids.yml
|     |  `- load-order.yml
|     |- scripts/
|     |  |- backup-bg3.ps1
|     |  |- scan-downloads.ps1
|     |  |- install-paks.ps1
|     |  |- verify-bg3-mods.ps1
|     |  `- rollback-bg3.ps1
|     |- reports/
|     |  `- .gitkeep
|     `- downloads-inbox/
|        `- .gitkeep
|- docs/
|  |- safety-rules.md
|  |- bg3-manual-install.md
|  `- vortex-vs-bg3mm.md
`- .gitignore
```

Add future games as siblings under `games/`, such as `games/skyrim-se/`, `games/cyberpunk-2077/`, `games/stalker/`, and `games/kenshi/`.

## Required `.gitignore` Policy

Ensure payloads, local caches, and generated reports are ignored before creating inbox or cache folders:

```gitignore
# Mod payloads and unknown binaries
*.pak
*.zip
*.7z
*.rar
*.exe
*.dll
*.bat
*.cmd
*.msi

# Downloaded scripts and local caches
downloads-inbox/*.ps1
downloads-inbox/**/*.ps1
downloads-inbox/*
mods-cache/*
extracted/*
backups/*
temp/*
tmp/*

# Generated reports
reports/*.json
reports/*.html
reports/*.log
games/*/reports/*.json
games/*/reports/*.html
games/*/reports/*.log

# Keep empty folders
!downloads-inbox/.gitkeep
!reports/.gitkeep
!games/*/downloads-inbox/.gitkeep
!games/*/reports/.gitkeep
```

## BG3 Defaults

On Windows, BG3 paths are usually:

```text
%LOCALAPPDATA%\Larian Studios\Baldur's Gate 3\Mods
%LOCALAPPDATA%\Larian Studios\Baldur's Gate 3\PlayerProfiles\Public\modsettings.lsx
```

- Prefer BG3 Mod Manager for small to medium manual `.pak` workflows.
- Prefer Vortex for Nexus Collections, especially large collections.
- Avoid letting Vortex and BG3 Mod Manager fight over the same profile.
- Manual `.pak` install means download from the original source, extract locally, identify `.pak` files, copy only `.pak` files to the BG3 Mods folder, then use BG3 Mod Manager to activate/export load order.
- When GUI interaction is required, tell the user what to do or use an appropriate desktop UI automation skill only when explicitly requested. Do not fake GUI results.

## BG3 Save Recovery

When a BG3 save reports missing mods or missing UUIDs, use [references/bg3-save-recovery.md](references/bg3-save-recovery.md). Prefer the bundled scripts before rewriting ad hoc PowerShell:

- `scripts/verify-bg3-downloads.ps1`: scan downloads/Mods, inspect `.pak/.zip/.rar/.7z`, verify UUIDs with LSLib/Divine when available, and install matching `.pak` files.
- `scripts/write-bg3-modsettings.ps1`: rebuild `%LOCALAPPDATA%\Larian Studios\Baldur's Gate 3\PlayerProfiles\Public\modsettings.lsx` from a save-derived ordered mod list, backing up the old file first.

Before writing `modsettings.lsx`, confirm that every save UUID is present in installed pak metadata or has an explicit, documented fallback. After writing, validate both counts: installed UUID matches and `modsettings.lsx` UUID coverage.

## Manifest Conventions

Prefer `mods.yml` for human-readable mod records and `collections.yml` for Nexus or other collections. Use `known-uuids.yml` and `load-order.yml` when the repo has enough verified data to justify separate files.

Common `mods.yml` fields:

```yaml
profile: bg3-personal-modlist
game: "Baldur's Gate 3"
manager: "BG3 Mod Manager"
install_mode: "manual_pak"
payload_policy: "local_only"
mods:
  - name: "Example Mod"
    source: "nexus"
    url: "https://www.nexusmods.com/baldursgate3/mods/example"
    required: true
    expected_type: "pak"
    expected_files:
      - "ExampleMod.pak"
    uuid: null
    version: null
    load_order_group: "core"
    install_notes:
      - "Download manually from original source."
      - "Install via BG3 Mod Manager."
    status: "planned"
```

Use these status values unless the repo defines its own: `planned`, `downloaded`, `installed`, `verified`, `disabled`, `removed`, `blocked`, `unknown`.

## Safe Workflows

### Repo Initialization

Create the safe structure, add `.gitignore` first, add README and safety docs, add empty manifests, add dry-run-first scripts, and add `.gitkeep` files for empty local folders. Do not add payload files.

### Manual BG3 `.pak` Install

1. Inspect the repo structure and current manifests.
2. Confirm `.gitignore` blocks payloads.
3. Add or update manifest records.
4. Create a timestamped backup before touching BG3 files.
5. Scan the downloads inbox without executing downloads.
6. Identify direct `.pak` files and archives containing `.pak` files.
7. Copy only `.pak` files after backup and explicit approval.
8. Have the user open BG3 Mod Manager to activate/export load order when needed.
9. Produce an install report with installed, skipped, blocked, backup, warnings, and next test steps.

### Nexus Collections

Use Vortex as the native installer for large Nexus Collections. Do not manually recreate a large collection unless the user explicitly accepts the maintenance burden. The repo should document the collection URL, manager, profile notes, backup points, risks, and verification reports, without mirroring payloads.

### Scripts

Scripts should be defensive, readable, and reversible.

- `backup-bg3.ps1`: detect BG3 local app data, create timestamped backup, save `.pak` file list, back up `modsettings.lsx` if present, never delete.
- `scan-downloads.ps1`: classify direct `.pak`, archives containing `.pak`, loose files, suspicious executables, and unknown files; never execute downloads.
- `install-paks.ps1`: default to `-DryRun` or require confirmation, copy only `.pak`, avoid subfolders in the BG3 Mods folder, preserve existing files, report duplicates.
- `verify-bg3-mods.ps1`: compare installed `.pak` files against `mods.yml`, report missing, extra, duplicate, and unknown files without claiming full compatibility.
- `rollback-bg3.ps1`: restore from an explicit timestamped backup, confirm before overwriting current files, never guess when multiple backups exist.

## When to Ask

Ask before installing or removing files, touching the game directory, changing `modsettings.lsx`, running unknown executables, adding or switching mod managers, committing local reports with personal paths, or changing a repo from local-only to public-ready.

Do not ask before creating draft manifests, documentation, dry-run scripts, safe `.gitignore` rules, or reports.

## Reporting Style

Use concise sections:

```markdown
## Summary

## Changed

## Not Changed

## Safety Notes

## Next Steps
```

A successful task leaves no redistributed payloads in Git, a clear manifest, a safe backup point, dry-run capable scan/install workflows, a readable report, and clear next steps for BG3 Mod Manager or Vortex.
