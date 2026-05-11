# Game ModOps Workstation v1

## Target Stack

- Windows 11
- Codex CLI or Codex desktop
- PowerShell 7
- Python 3.11+
- pywinauto with UIA backend
- Wabbajack
- Mod Organizer 2
- LOOT
- BG3 Mod Manager
- LSLib Divine

## Example `paths.local.yaml`

```yaml
root: "D:/Games/game-modops"

tools:
  wabbajack: "D:/GameModOps/tools/wabbajack/Wabbajack.exe"
  mo2: "D:/GameModOps/tools/mo2/ModOrganizer.exe"
  loot: "D:/GameModOps/tools/loot/LOOT.exe"
  bg3mm: "D:/GameModOps/tools/bg3mm/BG3ModManager.exe"
  lslib_divine: "D:/GameModOps/tools/lslib/Divine.exe"

bg3:
  mods_dir: "%LOCALAPPDATA%/Larian Studios/Baldur's Gate 3/Mods"
  profile_dir: "%LOCALAPPDATA%/Larian Studios/Baldur's Gate 3/PlayerProfiles/Public"
  modsettings: "%LOCALAPPDATA%/Larian Studios/Baldur's Gate 3/PlayerProfiles/Public/modsettings.lsx"
  inbox: "D:/Games/game-modops/inbox/bg3"

skyrim:
  game_root: "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition"
  install_root: "D:/Modding/Skyrim"
  downloads: "D:/Modding/Skyrim/Downloads"
  mo2_profile: "Default"

nexus:
  mode: "free-tier-assisted"
  browser: "chrome"
  downloads_dir: "D:/Games/game-modops/downloads/nexus"

agent:
  gui_mode: "unattended_nexus"
  require_confirmation_for:
    - payment
    - captcha
    - account_settings
    - destructive_delete
```

## Script Deliverables

GUI primitives:

- `inspect-window.py`
- `wait-for-window.py`
- `click-by-title.py`
- `click-by-automation-id.py`
- `screenshot-state.py`

BG3:

- `scan-bg3-inbox.py`
- `install-bg3-paks.ps1`
- `backup-modsettings.ps1`
- `export-bg3mm.py`
- `verify-bg3-loadorder.py`

Wabbajack:

- `launch-wabbajack.py`
- `install-modlist-assisted.py`
- `monitor-wabbajack.py`

MO2/LOOT:

- `launch-mo2.py`
- `snapshot-profile.ps1`
- `run-loot-from-mo2.py`
- `verify-mo2-profile.py`

Nexus:

- `open-download-queue.py`
- `mark-downloaded.py`
- `audit-missing-files.py`

Orchestrators:

- `run-bg3-agent.ps1`
- `run-skyrim-agent.ps1`
- `run-wabbajack-assisted.ps1`

## Validation

- PowerShell scripts parse through `[System.Management.Automation.Language.Parser]::ParseFile`.
- Python scripts compile with `python -m py_compile`.
- Repo contains no payload binaries or archives.
- Generated reports do not get committed unless intentionally sanitized.
- Tool verification reports missing configured tools instead of guessing paths.
