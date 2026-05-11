param(
  [Parameter(Mandatory=$true)][string]$WindowName,
  [string]$Name,
  [string]$NameContains,
  [string]$AutomationId,
  [ValidateSet("Button","Edit","Text","Hyperlink","ComboBox","TabItem","ListItem","DataItem","Pane","Document","Window")]
  [string]$ControlType,
  [int]$Index = 0,
  [ValidateSet("Invoke","SetValue","Click","Focus")]
  [string]$Action = "Invoke",
  [string]$Value
)

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes

$mouseSource = @"
using System;
using System.Runtime.InteropServices;
public static class NativeMouse {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);
  public const uint LEFTDOWN = 0x0002;
  public const uint LEFTUP = 0x0004;
}
"@
Add-Type -TypeDefinition $mouseSource -ErrorAction SilentlyContinue

function Get-ControlType($name) {
  if (-not $name) { return $null }
  return [System.Windows.Automation.ControlType]::$name
}

$root = [System.Windows.Automation.AutomationElement]::RootElement
$windowCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::NameProperty,
  $WindowName
)
$window = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $windowCond)
if (-not $window) { throw "Window not found: $WindowName" }

$typeObj = Get-ControlType $ControlType
$matches = New-Object System.Collections.Generic.List[object]
$desc = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)

for ($i = 0; $i -lt $desc.Count; $i++) {
  $e = $desc.Item($i)
  if ($typeObj -and $e.Current.ControlType -ne $typeObj) { continue }
  if ($AutomationId -and $e.Current.AutomationId -ne $AutomationId) { continue }
  if ($Name -and $e.Current.Name -ne $Name) { continue }
  if ($NameContains -and (($e.Current.Name -as [string]) -notlike "*$NameContains*")) { continue }
  $matches.Add($e)
}

if ($matches.Count -eq 0) { throw "No matching UI element found" }
if ($Index -lt 0 -or $Index -ge $matches.Count) { throw "Index $Index out of range; matches: $($matches.Count)" }

$target = $matches.Item($Index)

switch ($Action) {
  "Invoke" {
    $pattern = $target.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
    $pattern.Invoke()
  }
  "SetValue" {
    if ($null -eq $Value) { throw "SetValue requires -Value" }
    $pattern = $target.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    $pattern.SetValue($Value)
  }
  "Focus" {
    $target.SetFocus()
  }
  "Click" {
    $rect = $target.Current.BoundingRectangle
    if ([double]::IsInfinity($rect.X) -or [double]::IsInfinity($rect.Width)) {
      throw "Element has no usable screen rectangle; try -Action Invoke"
    }
    $x = [int]($rect.X + ($rect.Width / 2))
    $y = [int]($rect.Y + ($rect.Height / 2))
    [NativeMouse]::SetCursorPos($x, $y) | Out-Null
    [NativeMouse]::mouse_event([NativeMouse]::LEFTDOWN, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 80
    [NativeMouse]::mouse_event([NativeMouse]::LEFTUP, 0, 0, 0, [UIntPtr]::Zero)
  }
}

[pscustomobject]@{
  action = $Action
  matched = $matches.Count
  usedIndex = $Index
  controlType = ($target.Current.ControlType.ProgrammaticName -replace '^ControlType\.','')
  name = $target.Current.Name
  automationId = $target.Current.AutomationId
  className = $target.Current.ClassName
} | ConvertTo-Json -Depth 4
