---
name: windows-ui-automation
compat: [codex]
description: Windows desktop UI automation using the built-in Microsoft UI Automation API from PowerShell. Use when Codex needs to inspect, read, focus, click, invoke buttons, set edit fields, or automate native Windows, Win32, WPF, WinForms, Electron, Chromium, installer, launcher, or desktop application windows without a browser DOM tool. Especially useful for apps like Vortex, game launchers, installers, and dialogs where shell commands are not enough.
---

# Windows UI Automation

Use this skill to operate Windows desktop apps through the built-in Microsoft UI Automation API. Prefer semantic UIA actions over coordinate clicking: find a window, enumerate controls, then use `InvokePattern`, `ValuePattern`, or another supported pattern.

## Safety

- Use UIA only for user-requested desktop automation.
- Do not inspect password fields, saved credentials, cookies, browser profiles, or secret stores.
- Ask the user to complete login, 2FA, payment, or sensitive confirmation screens manually.
- Before closing windows, deleting data, or changing accounts/settings with lasting effects, confirm the specific action.
- Keep actions scoped to the target app and current task.

## Quick Workflow

1. Find the target process or window.
2. If the app is Electron/Chromium and exposes too few controls, restart it with accessibility enabled:

```powershell
Get-Process Vortex -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process "C:\Program Files\Vortex\Vortex.exe" -ArgumentList "--force-renderer-accessibility","--remote-debugging-port=9223"
```

3. Inspect controls:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\windows-ui-automation\scripts\find-ui.ps1" -WindowName "Vortex" -VisibleOnly
```

4. Invoke a button or set a field:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\windows-ui-automation\scripts\invoke-ui.ps1" -WindowName "Vortex" -Name "Games" -ControlType Button -Action Invoke
```

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\windows-ui-automation\scripts\invoke-ui.ps1" -WindowName "Vortex" -ControlType Edit -Index 0 -Action SetValue -Value "Baldur's Gate 3"
```

## Selection Heuristics

- Prefer `AutomationId` when available and stable.
- Otherwise use exact visible `Name` plus `ControlType`.
- Use `Index` only after inspecting current controls, because UI order can change.
- If a control has `InvokePattern`, use `Invoke` instead of a physical mouse click.
- If an edit field has `ValuePattern`, use `SetValue`; otherwise focus it and use keyboard input only when necessary.
- If UIA returns `Infinity` rectangles but the element supports `InvokePattern`, invoke it anyway.
- If no meaningful descendants appear for Electron/Chromium apps, relaunch with `--force-renderer-accessibility`.

## Common Patterns

Inspect buttons only:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\windows-ui-automation\scripts\find-ui.ps1" -WindowName "Vortex" -ControlType Button -VisibleOnly
```

Find text around a state or warning:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\windows-ui-automation\scripts\find-ui.ps1" -WindowName "Vortex" -NameContains ".NET 8"
```

Click a UIA element by native click fallback:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\windows-ui-automation\scripts\invoke-ui.ps1" -WindowName "Vortex" -Name "Deploy Mods" -ControlType Button -Action Click
```

## Troubleshooting

- If `FindAll` returns only a few panes for Electron apps, relaunch with accessibility flags.
- If a window is elevated and Codex is not, UIA may not access it. Ask the user or use non-elevated app mode where possible.
- If a control is offscreen, use search/filter fields or app navigation first; avoid blind coordinates.
- If a script cannot find a control, rerun `find-ui.ps1` and inspect the current screen state before retrying.
