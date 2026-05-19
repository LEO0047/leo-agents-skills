---
name: game-modops-agent
compat: [codex]
description: Use when building or operating the Game ModOps v3 Windows control tower for Nexus/Vortex, Wabbajack, MO2, LOOT, BG3 Mod Manager, BG3, Skyrim, manifests, backups, reports, safe local payload handling, GUI automation, and write-gated manager operations.
metadata:
  short-description: Game ModOps v3 control tower
---

# Game ModOps Agent

Use this as the primary skill for `D:\Games\game-modops`. It is the v3 mother skill for Windows-first mod operations across Nexus/Vortex, Wabbajack, MO2, LOOT, BG3 Mod Manager, Skyrim, and Baldur's Gate 3.

`nexus-mod-automation` remains the helper skill for Nexus/Vortex download queues, Vortex download monitoring, and archive inspection. `game-mod-management` remains the helper skill for BG3 UUID, save recovery, manifests, and load-order notes. This skill is the final authority for workspace safety, owner-tool decisions, backups, previews, confirmations, and write gates.

## Core Contract

Treat the workspace as a ModOps control tower, not a modpack and not a replacement mod manager.

- Main workspace: `D:\Games\game-modops`.
- Canonical Wabbajack path: `C:\Wabbajack\Wabbajack.exe`.
- Nexus API key source: Windows User environment variable `NEXUS_API_KEY`.
- Vortex, MO2, and BG3 Mod Manager are the authoritative install/deploy tools.
- Codex coordinates scripts, Nexus intelligence, GUI automation, manager operations, monitoring, backups, and reports.
- Keep downloaded mod payloads local-only and ignored by Git.
- Treat Chrome default Downloads (`$HOME\Downloads`) as a temporary inbox; completed Nexus/browser downloads should be automatically organized into the ownerTool-appropriate local payload location, not left for manual cleanup.
- Do not commit `.pak`, archives, plugins, third-party executables, downloaded DLLs, downloaded scripts, models, textures, audio, secrets, cookies, account data, or manager state payloads.
- Do not rewrite Vortex, MO2, or BG3MM behavior in ad hoc scripts when the manager should own the action.

## RAID: Shadow Legends Language Policy

When operating or advising on `RAID: Shadow Legends`, match the user's Chinese game UI.

- Use Traditional Chinese champion names in user-facing recommendations and action reports, for example `凱爾`, `菲恩`, `歸魂納爾瑪`, and `流浪者愛麗絲`.
- Keep English champion names only when needed for web searches, source citation, disambiguation, or one-time parenthetical mapping.
- If an English guide name is discovered first, map it back to the visible Chinese UI name before telling the user who to train, equip, upgrade, or skip.
- Do not ask the user to identify a champion by English name when the visible UI is Chinese; use screenshots or visible Chinese names instead.

## Codex Integration Policy

This is a Codex-first workflow. Do not add other assistant desktop configuration as the operating path for this workspace.

- Use `game-modops-agent` as the Codex mother skill.
- Codex skill material belongs under `C:\Users\leo04\.codex\skills\...` for existing global skills or `D:\Games\game-modops\.agents\skills\...` for repo-scoped helper wrappers.
- Do not create or rely on `.claude/settings.json` for this workspace.
- If a third-party tool is branded for another assistant, treat that branding as upstream packaging only; wrap or document it as a Codex helper before use.
- Local wrapper names should prefer Codex-neutral or Codex-specific names such as `skyrim-codex-toolkit`.

## Tool Responsibilities

Use existing tools as the execution layer. Do not replace them with ad hoc deployment logic.

- Vortex: Nexus Collection main installer/deployer. Skyrim archive downloader and staging only — must not install, enable, disable, deploy, or set load order for Skyrim profiles.
- MO2: Skyrim ownerTool. All Skyrim install, enable, disable, deploy, and load-order actions go through MO2.
- BG3MM: BG3 `.pak`, load order, and `modsettings.lsx` owner.
- Wabbajack: modlist installer launched from `C:\Wabbajack\Wabbajack.exe`.
- LOOT: Skyrim load-order assistance after profile/tool paths are verified.
- `mo2-invoke.ps1`: read-first MO2 CLI wrapper. Skyrim ownerTool only. Write-like actions are dry-run by default and do not switch profiles or remove mods.
- `loot-invoke.ps1`: LOOT sort wrapper. Suggest is L0 and writes a report only; Apply requires `-LlmReviewed` and backs up `plugins.txt` first.
- `detect-animation-conflict.ps1`: report-only Skyrim animation engine mismatch scan for Pandora/Nemesis/FNIS signatures.
- `validate-plugin-masters.ps1`: report-only Skyrim plugin master-chain validation through Spooky's AutoMod Toolkit.
- `scan-esl-candidates.ps1`: report-only ESL candidate scan. It must not set ESL flags or compact FormIDs.
- `scan-mo2-file-conflicts.ps1`: report-only MO2 left-pane file conflict scan with FaceGen and character asset emphasis.
- `backup-profile.ps1`: MO2 profile backup helper that writes only under `D:\Games\game-modops\backups\`.
- `skyrim-health-check.ps1`: Phase D Skyrim validation dashboard orchestrating report-only checks; backup is opt-in with `-IncludeBackup`.
- Nexus REST v1: stable metadata, games, mods, files, version info, download links, and user validation.
- Nexus GraphQL or richer API clients: approved metadata/search/dependency enhancement only.
- Skyrim Modding Toolkit: optional engine-layer diagnostics for ESP/BSA/NIF/save inspection under L0/L1 only; it must not write manager deployment paths or replace LOOT/Vortex/MO2 decisions.
- Nexus MCP Server: optional standard Nexus interface; use read-only, REST v1 first when enough, key from `NEXUS_API_KEY`, GraphQL metadata/search/dependency tools approved.
- Vortex MCP Bridge: Phase C auto-write for manager write tools because the user explicitly approved opening them.
- Custom MCP: only after the user approves a later phase because scripts or existing bridges are insufficient.

## MO2 CLI Reference

Use PowerShell and the configured local MO2 executable:

```powershell
$MO2 = "C:\Modding\SkyrimSE\MO2\ModOrganizer.exe"
$INSTANCE = "Skyrim Special Edition"
$PROFILE = "SkyrimSE-AE-1170-OldSave-Recovery"
```

Common CLI forms:

- `& $MO2 --help`: show supported CLI options.
- `& $MO2 --pick`: open the MO2 instance picker.
- `& $MO2 -i $INSTANCE`: open the named instance.
- `& $MO2 -i $INSTANCE -p $PROFILE`: open the named profile.
- `& $MO2 --logs`: mirror MO2 logs to stdout.
- `& $MO2 -i $INSTANCE -p $PROFILE run -e "SKSE"`: run an MO2 configured executable through VFS.
- `& $MO2 -i $INSTANCE -p $PROFILE run -e "LOOT"`: run LOOT through the selected MO2 profile VFS.
- `& $MO2 -i $INSTANCE -p $PROFILE run -e "SSEEdit"`: run a configured SSEEdit executable through VFS.
- `& $MO2 -i $INSTANCE -p $PROFILE run "D:\Tools\SSEEdit\SSEEdit.exe"`: run an external executable through VFS.
- `& $MO2 -i $INSTANCE -p $PROFILE run --arguments "-quickautoclean" "D:\Tools\SSEEdit\SSEEdit.exe"`: pass arguments to an external executable.
- `& $MO2 -i $INSTANCE -p $PROFILE run -e --arguments "-forcesteamloader" "SKSE"`: pass arguments to a configured executable.
- `& $MO2 -i $INSTANCE -p $PROFILE run --cwd "D:\Tools\SSEEdit" "D:\Tools\SSEEdit\SSEEdit.exe"`: override working directory.
- `& $MO2 refresh`: refresh MO2, equivalent to F5.
- `& $MO2 download "https://example.com/mod.7z"`: hand an HTTPS download to MO2.
- `& $MO2 download -g "Skyrim Special Edition" -n "SkyUI.7z" -m "SkyUI" -v "5.2" -s "Nexus" "https://example.com/SkyUI.7z"`: download with metadata.
- `& $MO2 "nxm://skyrimspecialedition/mods/12604/files/35407"`: hand an NXM link to MO2.
- `& $MO2 crashdump --type mini`: write a dump for a running MO2 process; supported types include `mini`, `data`, and `full`.
- `& $MO2 reload-plugin "plugin.dll"`: reload an MO2 plugin; development use only.

The most common automation commands are `run -e "SKSE"`, `run -e "LOOT"`, and `refresh`, always with the intended instance/profile verified first.

MO2 CLI can launch tools, select instance/profile, run through VFS, hand off downloads, refresh MO2, and emit logs. It is not a complete unattended mod installer and should not be treated as capable of resolving every FOMOD option, sorting load order, or repairing conflicts automatically.

## Skyrim CLI Toolchain Reference

Use MO2 as the VFS launcher for Skyrim tools whenever possible:

```powershell
$MO2 = "C:\Modding\SkyrimSE\MO2\ModOrganizer.exe"
$INSTANCE = "Skyrim Special Edition"
$PROFILE = "SkyrimSE-AE-1170-OldSave-Recovery"
$GAME = "C:\SteamLibrary\steamapps\common\Skyrim Special Edition"
```

Common tool commands and automation posture:

| Tool | CLI Status | Example | Use |
| --- | --- | --- | --- |
| SKSE64 | runnable | `& $MO2 -i $INSTANCE -p $PROFILE run -e "SKSE"` | Launch the game through MO2 VFS. |
| LOOT | automatable with review boundary | `& $MO2 -i $INSTANCE -p $PROFILE run -e --arguments '--game="Skyrim Special Edition" --auto-sort' "LOOT"` | Sort plugin/load order. Prefer `loot-invoke.ps1`; Apply still requires review and backup. |
| SSEEdit / xEdit | parameterized | `& $MO2 -i $INSTANCE -p $PROFILE run --arguments '-sse' "D:\Tools\xEdit\SSEEdit.exe"` | Inspect conflicts, records, and plugins. Editing remains write-gated. |
| SSEEdit Quick Auto Clean | semi-automated | `& $MO2 -i $INSTANCE -p $PROFILE run --arguments '-sse -quickautoclean' "D:\Tools\xEdit\SSEEdit.exe"` | Clean dirty edits. Treat plugin choice/output as reviewed work. |
| xEdit Conflict Scan | parameterized | `& $MO2 -i $INSTANCE -p $PROFILE run --arguments '-sse -veryquickshowconflicts' "D:\Tools\xEdit\SSEEdit.exe"` | Fast conflict inspection. |
| DynDOLOD | parameterized, not fully unattended | `& $MO2 -i $INSTANCE -p $PROFILE run --arguments '-sse -o:"C:\Modding\SkyrimSE\MO2\mods\DynDOLOD Output\"' "D:\Tools\DynDOLOD\DynDOLODx64.exe"` | Generate distant LOD. Settings/output require review. |
| TexGen | parameterized, not fully unattended | `& $MO2 -i $INSTANCE -p $PROFILE run --arguments '-sse -o:"C:\Modding\SkyrimSE\MO2\mods\TexGen Output\"' "D:\Tools\DynDOLOD\TexGenx64.exe"` | Generate LOD textures. |
| xLODGen / SSELODGen | parameterized | `& $MO2 -i $INSTANCE -p $PROFILE run --arguments '-sse -o:"C:\Modding\SkyrimSE\MO2\mods\xLODGen Output\"' "D:\Tools\xLODGen\SSELODGenx64.exe"` | Generate terrain LOD. |
| Pandora Behaviour Engine+ | automatable | `& $MO2 -i $INSTANCE -p $PROFILE run --arguments '--auto_run --auto_close -o "C:\Modding\SkyrimSE\MO2\mods\Pandora Output"' "D:\Tools\Pandora\Pandora Behaviour Engine.exe"` | Behavior patch generation. Prefer over Nemesis for automation when profile-compatible. |
| Nemesis | mostly GUI | `& $MO2 -i $INSTANCE -p $PROFILE run -e "Nemesis"` | Behavior patch generation; usually requires manual Update/Launch steps. |
| FNIS | semi-GUI | `& $MO2 -i $INSTANCE -p $PROFILE run -e "FNIS SE"` | Legacy animation behavior generation. |
| Wrye Bash | CLI exists, mostly GUI | `& "D:\Tools\Wrye Bash\Mopy\Wrye Bash.exe" --no-uac` | Bashed Patch, BAIN, leveled lists. Use cautiously. |
| Wabbajack CLI | CLI | `wabbajack-cli install -m "Some/List" -o "D:\Modlists\List" -d "D:\Modlists\Downloads"` | Install, compile, or verify modlists. |
| BSArch | CLI | `bsarch.exe "D:\ExtractedMod" "D:\Output\MyMod.bsa" -sse -z` | Pack or unpack BSA/BA2 archives. |
| Bethesda Archive Extractor | mostly GUI | `& "D:\Tools\BAE\bae.exe"` | BSA/BA2 extraction; not a comfortable CLI target. |
| PapyrusCompiler.exe | CLI | `& "$GAME\Papyrus Compiler\PapyrusCompiler.exe" "MyScript.psc" -i="$GAME\Data\Scripts\Source" -o="$GAME\Data\Scripts" -f="TESV_Papyrus_Flags.flg"` | Compile `.psc` to `.pex`. |

Toolchain priority for agent workflows: MO2 CLI, LOOT, xEdit/SSEEdit, Pandora, DynDOLOD/TexGen/xLODGen, Wabbajack CLI, then BSArch/7-Zip.

Fully CLI-friendly tools include MO2, LOOT, xEdit, Pandora, DynDOLOD-family tools, Wabbajack, BSArch, and PapyrusCompiler. Nemesis, FNIS, BodySlide, Wrye Bash, and Creation Kit GUI should be treated as semi-automated or attended workflows.

## Workspace Shape

Prefer and preserve the `D:\Games\game-modops` control-tower layout:

```text
D:\Games\game-modops
  config\
  manifests\
  scripts\
    nexus\
    vortex\
    mo2\
    bg3\
    skyrim\
    backup\
    reports\
  reports\
  backups\
  logs\
  secrets\
  AGENTS.md
  SKILL.md
```

Local payload folders, secrets, caches, raw logs, and generated reports must stay ignored unless the user explicitly asks for sanitized tracking.

## Default Mode

Use `agent-controlled, write-gated` mode.

## Protected Automation Policy

Do not weaken, remove, or rewrite the high-automation positioning unless the user explicitly asks to change this protected policy. Future edits must preserve that Nexus-assisted download flows, GUI monitoring, manager operations, state reads, local scanning, and report generation are automatable under the write-gated safety model.

This policy protects the user's intended operating model: high agent autonomy for investigation, download assistance, GUI monitoring, manager assistance, state checks, and reporting; explicit confirmation for high-risk writes and account/payment/rate-limit boundaries.

## Permission Levels

- L0 Read-only: API queries, scans, manager state reads, metadata cache reads, reports. No confirmation needed.
- L1 Prepare: install plans, backup preparation, diff/preview generation, download assistance, queue management. Confirmation may be needed at account/payment/rate-limit boundaries.
- L2 Write-gated: install, enable, disable, deploy, copy `.pak`, write load order, write `modsettings.lsx`, restore backup. Requires ownerTool, target profile, backup, preview, explicit confirmation, validation, and report.
- L3 Forbidden: destructive bulk deletes, bypassing paid access or rate limits, redistributing payloads, committing secrets or payloads, executing unknown downloaded binaries/scripts.

## State Machine

Use this state flow for ModOps tasks:

```text
DISCOVER
BUILD_PLAN
SCAN_LOCAL
PRECHECK
REPORT_ONLY
APPLY_PENDING_BACKUP
APPLY_INSTALL
VALIDATE_INSTALL
DEPLOY_PENDING_BACKUP
DEPLOY
POST_DEPLOY_VALIDATE
FINAL_REPORT
```

`REPORT_ONLY` is the default resting point unless the user explicitly requests apply/deploy/write and the write gate is satisfied.

## Workflow-State Mapping

Use this compact mapping when translating game-specific workflows into the state machine:

| State | BG3 mapping | Skyrim/Wabbajack/Vortex/MO2 mapping | Helper handoff |
| --- | --- | --- | --- |
| `DISCOVER` | identify BG3 target/profile | identify collection/modlist/profile | `game-modops-agent` |
| `BUILD_PLAN` | draft `.pak` / UUID / load-order plan | draft Nexus/modlist/install plan | `game-mod-management` for BG3 manifests; `nexus-mod-automation` or Nexus MCP Server for Nexus source/file data |
| `SCAN_LOCAL` | scan inbox, Mods folder, `modsettings.lsx` | scan downloads, archives, MO2/Vortex state, ESP/BSA/NIF/save diagnostics | `nexus-mod-automation` for archives/downloads; Skyrim Modding Toolkit for engine diagnostics |
| `PRECHECK` | check ownerTool, paths, backup need | check ownerTool, paths, disk/tool readiness, Vortex Bridge readonly mode | `game-modops-agent` |
| `REPORT_ONLY` | write dry-run report and stop by default | write preflight report and stop by default | `game-modops-agent` |
| `APPLY_PENDING_BACKUP` | back up Mods listing and `modsettings.lsx` | snapshot MO2/Vortex/profile state | `game-modops-agent` |
| `APPLY_INSTALL` | copy `.pak` or drive BG3MM only after confirmation | manager install/enable only after confirmation; Vortex Bridge write only after Phase C approval | manager-owned action |
| `VALIDATE_INSTALL` | verify UUID coverage and file presence | verify installed state/plugins/files; use Skyrim Modding Toolkit diagnostics when available | game adapter |
| `DEPLOY_PENDING_BACKUP` | preview/export load-order impact | preview deploy/load-order impact | `game-modops-agent` |
| `DEPLOY` | BG3MM export or controlled write after confirmation | Vortex deploy or LOOT-assisted flow after confirmation | manager-owned action |
| `POST_DEPLOY_VALIDATE` | re-read `modsettings.lsx` and active mods | re-read deployed/active manager state | game adapter |
| `FINAL_REPORT` | sanitized final report | sanitized final report | `game-modops-agent` |

## Nexus API Usage Contract

Use Nexus API as the intelligence layer, not as a replacement for Vortex, MO2, or BG3MM.

- Read the key only from Windows User environment variable `NEXUS_API_KEY`.
- Never print, log, commit, report, or echo the full API key.
- It is safe to report only `present`, `missing`, or a short redacted preview when explicitly useful.
- Send Nexus requests to `https://api.nexusmods.com` with the API key header and application identification headers: `Application-Name` and `Application-Version`.
- Use `users/validate` as the first API health check before relying on the key.
- REST v1 is the stable default for games, mods, files, version info, download links, and user validation.
- GraphQL or richer API clients may be used only as optional enhancement when REST v1 does not provide the needed metadata.
- Treat HTTP 401/403 as blocked authentication/authorization, and HTTP 429 as a rate-limit stop.
- If Nexus `download_link.json` returns HTTP 403 with a message that direct API download links require visiting `nexusmods.com` or are for Premium users only, do not retry or treat it as a broken key. Use the approved Manual/Slow web flow plus ownerTool monitoring instead, and stop at login, password, 2FA, payment, subscription/Premium, account setting, rate-limit, or download-limit prompts.
- Do not brute-force retry, parallel-spam, or crawl Nexus pages/API endpoints.
- Use local metadata caches when doing repeated checks.
- Reports must redact API keys, tokens, cookies, account data, and sensitive local payload contents.
- Nexus API may guide install plans, but manager writes still require ownerTool, backup, preview, explicit confirmation, validation, and report.

## MCP Strategy

This is the authoritative MCP policy for this skill.

Do not build a custom MCP server first.

- Phase A: use scripts, Nexus API, local scanners, reports, Skyrim Modding Toolkit diagnostics when installed, and Nexus MCP Server in REST v1-only mode when installed.
- Phase B: test an existing Vortex MCP Bridge in read-only audit mode.
- Phase C: Vortex Bridge manager write tools are approved for auto-write operation.
- Phase D: build custom MCP only if the user approves it after existing scripts/bridges prove insufficient.

Allowed Vortex Bridge capabilities include profile/mod listing, mod info, update checks, conflict/status reads, and user-approved manager write tools such as install, remove, enable, disable, deploy, profile switching, rules, updates, and backup operations. Account/social tools such as endorse, abstain, track, and untrack remain blocked unless separately requested.

## Integration Roadmap

Adopt external integrations in this order:

- Phase A: strengthen read-only intelligence. Candidate tools are Skyrim Modding Toolkit for engine diagnostics and Nexus MCP Server in REST v1-only mode.
- Phase B: add Vortex MCP Bridge in read-only audit mode.
- Phase C: user-approved Vortex manager write tools are enabled for auto-write operation.
- Phase D: build custom MCP only if the user approves it after scripts and existing bridges prove insufficient.

Phase A tool boundaries:

- Skyrim Modding Toolkit may inspect ESP/BSA/NIF data, analyze saves, report orphan scripts, and produce plugin/conflict diagnostics.
- Skyrim Modding Toolkit must not write Vortex/MO2 deployment paths, modify `plugins.txt`, or replace LOOT/load-order decisions without write-gated confirmation.
- Nexus MCP Server may replace direct REST scripts gradually for metadata, game, mod, file, and update intelligence.
- Nexus MCP Server must read the key from `NEXUS_API_KEY`, validate with `users/validate`, prefer REST v1 when enough, use approved GraphQL metadata/search/dependency tools when useful, and stop on HTTP 429.

Phase B Vortex Bridge read-only allowlist:

- `list_profiles`
- `get_mod_info`
- `check_updates`
- `get_conflicts`
- `get_load_order`

Phase C Vortex Bridge auto-write tools approved by the user:

- `create_profile`
- `switch_profile`
- `install_mod`
- `enable_mod`
- `disable_mod`
- `deploy_mods`
- `remove_mod`
- `rename_mod`
- `update_mod`
- `update_all_mods`
- `set_load_order`
- `add_mod_rule`
- `remove_mod_rule`
- `cancel_download`
- `install_from_file`
- `backup_profile`

Account/social tools remain blocked unless separately requested: `endorse_mod`, `abstain_mod`, `track_mod`, and `untrack_mod`.

Phase C write tools are enabled for auto-write manager operations. `deploy_mods` and `remove_mod` must be logged as separate high-risk actions and must not be hidden inside unrelated work.

The agent may automate:

- Nexus-assisted download flows, including ordinary logged-in browser steps, already-configured content gates, wait timers, visible progress monitoring, and free/slow download steps only after confirming the page is not asking for payment, subscription changes, account setting changes, credentials, 2FA, or rate-limit handling.
- Free-tier Nexus slow/free downloads with max concurrency 5. Count active browser downloads and `.crdownload` files before starting another; if 5 are active, monitor and wait instead of opening more.
- Chrome default Downloads organization after completion. When a Nexus/browser download lands in `$HOME\Downloads`, wait until `.crdownload` disappears, then move/copy it to the ownerTool-appropriate local payload destination: Skyrim/MO2 archives to `C:\Modding\SkyrimSE\MO2\downloads\`; BG3 payloads to the configured BG3 staging/inbox path; unknown files to `D:\Games\game-modops\inbox\unclassified\` for report review. Do not overwrite existing files.
- FOMOD install flow through MO2 plus `windows-ui-automation`: launch/focus MO2, invoke the archive installer, inspect wizard text/options, select clearly safe/default/documented choices, enable the installed mod, run/assist LOOT through the verified MO2 profile/tool path, validate state, and report.
- Chrome/Nexus-assisted download fallback when API direct file download links are blocked with HTTP 403 for non-Premium/API-link reasons.
- Nexus API queries, metadata checks, file listing, download-link lookup, dependency/requirement checks, and rate-limit-aware reporting.
- GUI monitoring and low-risk manager UI operations after verifying window title, visible text, and control identity.
- Wabbajack, Vortex, MO2, LOOT, BG3MM, and related tool launch/monitor flows from configured local paths.
- Local file scanning, archive inspection, `.pak` classification, plugin detection, UUID checks, manager state reads, and report generation.

The user confirms high-risk checkpoints:

- Password entry, 2FA, payment, subscription, Premium prompts, account setting changes, rate-limit blocks, download-limit blocks, unknown destructive windows, FOMOD decisions that remain unclear after UIA inspection, profile/game writes, deploy, remove, restore, or any action that would overwrite existing state.

## Owner Tool Contract

Every target profile must have exactly one owner tool before writes are allowed.

Skyrim ownerTool for this workspace: **MO2**.
- MO2 path: `C:\Modding\SkyrimSE\MO2`
- MO2 downloads: `C:\Modding\SkyrimSE\MO2\downloads`
- Vortex role for Skyrim: `downloader_only`
- Vortex forbidden for Skyrim profiles: `install_mod`, `enable_mod`, `disable_mod`, `deploy_mods`, `set_load_order`, `switch_profile`, `install_from_file`

Skyrim download flow:
- Premium: use `nexus_get_download_links` (Nexus MCP Server) → download directly to `C:\Modding\SkyrimSE\MO2\downloads\` → MO2 installs from archive. No browser or Vortex required.
- Free: use Nexus Manual/Slow browser download only. Do not use `nmm=1`, `nxm://`, "Mod Manager Download", or OS protocol-handler paths for Skyrim/MO2, because this machine may route them to Vortex or the wrong game context. Completed archives go to `C:\Modding\SkyrimSE\MO2\downloads\`, then MO2 installs from archive.
- If Vortex opens from a Skyrim Nexus link, cancel the Vortex prompt/download/install path immediately. Do not continue through Vortex for Skyrim.
- Nexus API `download_link.json` may return HTTP 403 for non-Premium direct file links; this is expected. Use Manual/Slow web flow instead, not Vortex/NXM.
- If Manual/Slow produces a signed `files.nexus-cdn.com` or `supporter-files.nexus-cdn.com` URL, Codex may save that already-authorized URL to the ownerTool downloads folder with PowerShell or `curl.exe`, but must never print/report the full signed URL.
- If Chrome shows `ERR_BLOCKED_BY_CLIENT` for Nexus CDN files, stop and report the browser blocker. Only disable or adjust a blocking extension after explicit user approval, and re-enable it after the batch.
- Free-tier slow/free browser downloads may run concurrently up to 5 active downloads, but must still stop on login, password entry, 2FA, payment, subscription/Premium handling, account setting changes, rate-limit, or download-limit prompts.
- If a Skyrim archive lands in Chrome's default `$HOME\Downloads`, automatically organize it to `C:\Modding\SkyrimSE\MO2\downloads\` after completion verification. If the archive identity is uncertain, stage it under `D:\Games\game-modops\inbox\skyrim\` or `D:\Games\game-modops\inbox\unclassified\` and report for LLM review.

Skyrim MO2 FOMOD/UI install flow:
- FOMOD archives are not manual-only. Use `windows-ui-automation` to operate MO2 installer dialogs and LOOT windows after the archive is staged in `C:\Modding\SkyrimSE\MO2\downloads\`.
- Default FOMOD memory source: before any Skyrim/MO2 FOMOD install, reinstall, compatibility patch, or option review, read `D:\Games\game-modops\manifests\skyrim\fomod-decisions-current.json` and treat it as the current profile's applied decision record. Also consult `D:\Games\game-modops\reports\skyrim-fomod-decisions-current-20260509.md` when a human-readable summary is useful.
- Use the recorded choices as defaults for this profile unless the user explicitly changes the route. Current defaults include Pandora/OStim route, no FNIS, no Nemesis alongside Pandora, XPMSSE Basic/HDT rig/no extra animation replacers, Precision `Compatibility = None`, BnP as active male skin winner, and Lux Via Patch Hub patch selection = none unless a matching installed/enabled mod is detected.
- For future compatibility patches, compare the patch target against the current MO2 enabled modlist, the FOMOD decisions manifest, and the relevant requirements/conflict reports. If the target mod is not installed and enabled, skip the patch or write a blocked report instead of selecting it speculatively.
- When a FOMOD is rerun or a compatibility patch is added, update `fomod-decisions-current.json` and write a matching report under `D:\Games\game-modops\reports\` with the selected step/group/plugin choices, skipped options, reason, backup path, and validation results.
- Before install, snapshot the active MO2 profile and verify ownerTool/profile paths.
- During FOMOD, inspect visible text/options on each page. Select clearly safe/default/recommended/required options when documented by the wizard or install plan. Stop only when choices are unclear after UIA inspection, preference-only, destructive, incompatible with Pandora/MO2, or require user-specific taste.
- After install, enable the intended mod in MO2, run or assist LOOT through the verified MO2 profile/tool path when appropriate, re-read MO2 state and plugin/load-order files, rerun requirements scan when useful, and write a sanitized report.

Skyrim MO2 requirements gap scan:
- Use `D:\Games\game-modops\scripts\skyrim\scan-mo2-requirements.ps1` as the read-only dependency audit playbook.
- Default to `-Depth 1`; use deeper scans only when transitive requirements are explicitly needed.
- The scan reads MO2 `modlist.txt`, local `meta.ini`, and Nexus GraphQL requirements, writes a sanitized report, and must not install, enable, disable, deploy, edit MO2 profiles, or use Vortex for Skyrim.

Skyrim MO2 metadata patch LLM review gate:
- Use `D:\Games\game-modops\scripts\skyrim\patch-mo2-meta-ids.ps1` only after dry-run preview.
- Every run output must be reviewed by the LLM before it is treated as actionable.
- `-Apply` must include `-LlmReviewed` after that review.
- Search-derived candidates are preview-only; only verified/manual mappings may write `meta.ini` `modID`.
- This script must not edit `modlist.txt`, `plugins.txt`, load order, deployed files, or game folders.

BG3 ownerTool: BG3MM.

If `ownerTool` is missing, unclear, or conflicting, stop at report/blocked mode. Do not mix Vortex, MO2, BG3MM, and manual flows on one profile without documenting which tool owns the profile.

## Manifest Contract

Profile and install-plan manifests should answer:

- target game or game domain
- display name
- `ownerTool`
- target profile
- mode such as `report-only` or `write-gated`
- expected files, plugins, `.pak` files, UUIDs, or other outputs
- safety flags for backup, profile writes, deploy, preview, and confirmation
- source URLs, Nexus game domain, mod ID, file ID, version, and notes when known
- confidence level and blocked reasons when data is incomplete

If paths are unknown, keep them `null` or report missing setup. Do not invent local paths, compatibility, UUIDs, hashes, dependencies, or load-order rules.

Minimal profile manifest skeleton:

```json
{
  "game": "skyrimspecialedition",
  "displayName": "Skyrim Special Edition",
  "ownerTool": "mo2",
  "profile": "default",
  "mode": "report-only",
  "paths": {
    "gameRoot": null,
    "managerProfile": "C:\\Modding\\SkyrimSE\\MO2\\profiles\\<profile>",
    "downloads": "C:\\Modding\\SkyrimSE\\MO2\\downloads"
  },
  "mods": [
    {
      "source": "nexus",
      "gameDomain": "skyrimspecialedition",
      "modId": null,
      "fileId": null,
      "version": null,
      "expectedOutputs": [],
      "required": true,
      "notes": ""
    }
  ],
  "safety": {
    "requireBackupBeforeWrite": true,
    "requirePreviewBeforeWrite": true,
    "requireExplicitConfirmation": true,
    "allowProfileWrite": false,
    "allowDeploy": false
  },
  "confidenceLevel": "unknown",
  "blockedReasons": []
}
```

For BG3, use `game: "baldursgate3"`, `ownerTool: "bg3mm"`, and put `.pak`, UUID, and `modsettings.lsx` expectations in `expectedOutputs` or game-specific fields. Do not reuse Skyrim plugin/load-order assumptions for BG3.

## Write Gate

All profile/game write actions require:

1. Owner tool locked.
2. Target profile selected.
3. Timestamped backup created or verified.
4. Change preview or diff produced.
5. Use the user's Phase C auto-write approval for Vortex manager write tools unless a stop condition appears.
6. Execution only through the configured manager bridge/tool/path.
7. Post-action validation.
8. Sanitized final report.

Treat `remove`, `restore backup`, and `deploy` as high-risk write actions. Vortex `remove_mod` and `deploy_mods` are Phase C approved, must be logged separately, and must not be hidden inside unrelated work. Restore backup still requires explicit confirmation.

## Payload and Git Rules

Never commit or move into tracked history:

- `.pak`
- `.esp`, `.esm`, `.esl`
- `.bsa`, `.ba2`
- archives such as `.zip`, `.7z`, `.rar`, `.tar`, `.gz`
- DLL, EXE, BAT, CMD, MSI, unknown PS1 files
- mod scripts, game files, manager state payloads
- cookies, tokens, API keys, passwords, account data
- raw logs or reports that may leak secrets, account data, or private paths

Backups should record timestamp, source path, destination path, and checksum when practical. Commit backup notes only when sanitized; keep actual payload backups local-only.

## GUI Automation Rules

- Prefer UI Automation control names, automation IDs, and verified window titles over coordinates.
- Use `windows-ui-automation` for Vortex, Wabbajack, MO2, LOOT, BG3MM, installers, and manager dialogs when shell/API state is insufficient.
- Use screenshots only for evidence and diagnosis.
- Before clicking, inspect active window text and visible controls for payment, account settings, destructive prompts, mismatch, or unknown state.
- If a reliable control cannot be found, capture context and stop.
- Never turn fallback coordinates into the primary strategy.
- Never execute downloaded scripts, installers, DLLs, EXEs, BAT/CMD files, MSI files, or unknown binaries.

## Workflow Map

BG3:

1. Validate setup and owner tool.
2. Scan `inbox/bg3` and BG3 Mods state.
3. Classify direct `.pak` files and archives.
4. Inspect UUIDs and `modsettings.lsx` read-only.
5. Build a plan and preview.
6. Back up `modsettings.lsx` and current Mods listing before writes.
7. Copy `.pak` files or export through BG3MM only after explicit apply/confirmation.
8. Verify `modsettings.lsx`, installed UUID coverage, and write a report.

Helper handoff: use `game-mod-management` for BG3 UUID, save recovery, manifest, and load-order reasoning; use `game-modops-agent` for ownerTool, backup, preview, confirmation, and actual write gates.

Skyrim/Wabbajack/MO2:

1. Validate setup: ownerTool = MO2. Confirm Vortex is not managing any Skyrim profile.
2. Use `C:\Wabbajack\Wabbajack.exe` as the canonical Wabbajack path.
3. Read MO2 profile/modlist/plugin state from `C:\Modding\SkyrimSE\MO2`.
4. Download flow — choose one:
   - Premium: `nexus_get_download_links` → download directly to `C:\Modding\SkyrimSE\MO2\downloads\`.
   - Free: Nexus Manual/Slow browser download only → organize archive to `C:\Modding\SkyrimSE\MO2\downloads\`.
   - Never use `nmm=1`, `nxm://`, "Mod Manager Download", or Vortex install/deploy for Skyrim.
5. Query Nexus metadata and scan downloads/archives.
6. Use Skyrim Modding Toolkit for ESP/BSA/NIF/save diagnostics when installed.
7. Build a plan and preview.
8. Snapshot MO2 profile state before writes (`modlist.txt`, `plugins.txt`, profile folder).
9. Install/enable/deploy only through MO2. Do not call Vortex `install_mod`, `deploy_mods`, `set_load_order`, or `switch_profile` for Skyrim profiles.
10. For FOMOD archives, use `windows-ui-automation` to drive MO2 installer pages and stop only on unclear/preference/destructive/incompatible options.
11. Run or assist LOOT only after MO2 profile/tool paths are verified.
12. Write before/after reports.

Helper handoff: use `nexus-mod-automation` for Nexus/Vortex download queues, Vortex download monitoring, and archive inspection; use Skyrim Modding Toolkit for engine-layer diagnostics; use `game-modops-agent` for Wabbajack/MO2/Vortex ownerTool decisions, backups, previews, and write gates.

Nexus:

1. Maintain queue manifests with source URL, game domain, mod ID, file ID, expected filename, and status.
2. Use Nexus API or Nexus MCP Server REST v1 for metadata intelligence and browser/Vortex flows for downloads when appropriate.
3. Monitor local downloads and update reports. Free-tier slow/free downloads may run concurrently up to 5 active downloads.
4. If Chrome saves completed downloads to `$HOME\Downloads`, automatically organize them to the ownerTool-appropriate local payload location, while never writing directly into game install folders, deployed `Data`, BG3 `Mods`, `modsettings.lsx`, `plugins.txt`, or load-order files without the normal write gate.
5. Stop or request confirmation at payment, account settings, rate-limit, unknown destructive state, or write gate boundaries.

Helper handoff: use `nexus-mod-automation` for queue mechanics and download/archive reports, but keep Nexus MCP Server mode, API key handling, rate-limit stops, ownerTool decisions, and write gates under `game-modops-agent`.

## Validation and Regression Tests

Use setup and policy checks to prevent future drift.

- `D:\Games\game-modops\scripts\validate-setup.ps1` must verify configured tool paths and policy guardrails.
- `D:\Games\game-modops\scripts\setup\test-automation-policy.ps1` must fail if the protected high-automation policy or Nexus API usage contract is weakened.
- Wabbajack should validate as `C:\Wabbajack\Wabbajack.exe`.
- Missing MO2 path is a setup warning/blocker for MO2-specific tasks, not a reason to auto-install or auto-rewrite paths.
- Optional integration checks should report whether Skyrim Modding Toolkit, Nexus MCP Server, and Vortex MCP Bridge are installed, but must not execute unknown binaries without explicit approval.
- Tests should cover missing API key, API validation failure, HTTP 429, approved GraphQL metadata tools, Vortex Bridge Phase C auto-write mode, enabled `switch_profile`, enabled `install_mod`, enabled `deploy_mods`, account/social tools still blocked, missing ownerTool, manager conflict, missing backup, missing preview, redaction, and Skyrim/BG3 adapter split.

## Successful Local Playbooks

MO2 instance consolidation:

1. Identify the canonical MO2 by checking the running `ModOrganizer.exe` path, `portable.txt`, active profile path, and Start Menu shortcut target.
2. Treat `C:\Modding\SkyrimSE\MO2` as canonical only when it is the running portable instance and the selected profile is under `C:\Modding\SkyrimSE\MO2\profiles`.
3. Move old AppData instances or extracted MO2 leftovers to a timestamped backup/quarantine folder under `C:\Modding\SkyrimSE\backups` instead of deleting them.
4. Report what was moved, what was left untouched, and whether only one live `ModOrganizer.exe` remains outside backups.

MO2 manual Nexus archive install:

1. Snapshot the active MO2 profile before installing or enabling mods.
2. Preserve Nexus archives and `.meta` files in `C:\Modding\SkyrimSE\MO2\downloads` when available; missing `.meta` explains MO2 red warning icons but does not by itself prove the installed mod is broken.
3. Install into `C:\Modding\SkyrimSE\MO2\mods`, enable only the intended mod folders/plugins, then verify `modlist.txt`, `plugins.txt`, and expected files.
4. For translation chains, install and verify hard requirements first, then the translation/addon, and keep all payloads local-only.

Chrome-authenticated Nexus requirements audit:

1. Prefer the user's Chrome session through the Chrome plugin when Nexus pages require login, adult-content preferences, or existing cookies.
2. Open a temporary Chrome tab, visit the Nexus description page, read visible requirements and nearby description text, then close the temporary tab.
3. Do not change Nexus account settings, content preferences, subscriptions, or payment state while auditing.
4. If anonymous web output disagrees with Chrome, trust the logged-in Chrome page for adult/hidden Nexus pages and note that Chrome was the source.

Skyrim requirements triage:

1. Compare active `modlist.txt` and `plugins.txt` against Nexus requirements and local `mods\<name>\meta.ini` / `downloads\*.meta`.
2. Separate hard missing requirements from optional feature gaps.
3. Treat `Pandora Output` as generated behavior output. Regenerate it after adding or removing animation mods, and do not install FNIS/Nemesis alongside Pandora unless a page or user request makes the responsibility clear.
4. For broken NPC faces, inspect MO2 left-pane conflicts for `FaceGenData`; missing body/physics requirements usually explain body/outfit deformation more than facegen problems.
5. Prefer `scripts\skyrim\scan-mo2-requirements.ps1` for the automated read-only requirements gap report before any manual interpretation.
