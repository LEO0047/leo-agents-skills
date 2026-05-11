# BG3 Save Mod Recovery

Use this reference when a Baldur's Gate 3 save reports missing mods, missing UUIDs, or a broken load order.

## Workflow

1. Identify the newest or requested `.lsv` save and extract `meta.lsx` with LSLib/Divine.
2. Parse the save's mod list in order: name, folder, UUID, and publish handle when present.
3. Compare save UUIDs against installed `.pak` metadata in:
   `%LOCALAPPDATA%\Larian Studios\Baldur's Gate 3\Mods`
4. Download missing mods from original sources only. Prefer Nexus/Vortex for Nexus files, mod.io for official in-game mods, CurseForge/GitHub only when the mod's own page points there or the UUID can be verified.
5. Verify every candidate archive by extracting or reading `.pak` `meta.lsx`; do not trust filenames alone when a UUID can be read.
6. Install only matching `.pak` files into the BG3 Mods folder.
7. For Unique Tav, install the `.pak` in Mods and manually extract the `Generated` loose files into the BG3 game `Data` directory when the archive clearly contains `Generated\Public\Shared\Assets\unique_tav`.
8. Back up `modsettings.lsx`, then rebuild it from the save order and installed pak metadata.
9. Recheck that every save UUID exists in installed pak metadata and in `modsettings.lsx`.

## Bundled Scripts

Use `scripts/verify-bg3-downloads.ps1` to scan downloads and installed Mods for UUID matches. It supports `.pak`, `.zip`, `.rar`, and `.7z` if `7z.exe` is available.

Typical scan:

```powershell
powershell -ExecutionPolicy Bypass -File "$skillRoot\scripts\verify-bg3-downloads.ps1" -Json
```

Install verified matches:

```powershell
powershell -ExecutionPolicy Bypass -File "$skillRoot\scripts\verify-bg3-downloads.ps1" -Install
```

Use `scripts/write-bg3-modsettings.ps1` only after all expected UUIDs are present in the Mods folder. It backs up the current `modsettings.lsx` before writing.

```powershell
powershell -ExecutionPolicy Bypass -File "$skillRoot\scripts\write-bg3-modsettings.ps1"
```

## Important Cautions

- Do not redistribute downloaded mod payloads.
- Do not guess missing UUIDs for gameplay mods. For localization-only pak files, changing `meta.lsx` identity may be a last resort only when the content source is known and the goal is matching an old save UUID.
- Do not extract loose files into the game `Data` directory unless the mod's instructions require it.
- Do not let BG3 Mod Manager and Vortex both rewrite the same profile without documenting which tool owns the final load order.
- Keep broken or incomplete downloads out of verification decisions.
