param(
  [string]$WindowName,
  [string]$ProcessName,
  [string]$NameContains,
  [ValidateSet("Button","Edit","Text","Hyperlink","ComboBox","TabItem","ListItem","DataItem","Pane","Document","Window")]
  [string]$ControlType,
  [switch]$VisibleOnly,
  [int]$Max = 200
)

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes

function Convert-Rect($rect) {
  if ([double]::IsInfinity($rect.X) -or [double]::IsInfinity($rect.Width)) {
    return @{ x = $null; y = $null; width = $null; height = $null }
  }
  return @{ x = [int]$rect.X; y = [int]$rect.Y; width = [int]$rect.Width; height = [int]$rect.Height }
}

function Get-ControlType($name) {
  if (-not $name) { return $null }
  return [System.Windows.Automation.ControlType]::$name
}

$root = [System.Windows.Automation.AutomationElement]::RootElement
$windows = New-Object System.Collections.Generic.List[object]

if ($WindowName) {
  $cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty,
    $WindowName
  )
  $found = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
  for ($i = 0; $i -lt $found.Count; $i++) { $windows.Add($found.Item($i)) }
} elseif ($ProcessName) {
  $procs = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
  foreach ($proc in $procs) {
    $cond = New-Object System.Windows.Automation.PropertyCondition(
      [System.Windows.Automation.AutomationElement]::ProcessIdProperty,
      $proc.Id
    )
    $found = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
    for ($i = 0; $i -lt $found.Count; $i++) { $windows.Add($found.Item($i)) }
  }
} else {
  $found = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
  for ($i = 0; $i -lt $found.Count; $i++) { $windows.Add($found.Item($i)) }
}

$typeObj = Get-ControlType $ControlType
$rows = New-Object System.Collections.Generic.List[object]

foreach ($window in $windows) {
  $desc = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  for ($i = 0; $i -lt $desc.Count; $i++) {
    $e = $desc.Item($i)
    if ($typeObj -and $e.Current.ControlType -ne $typeObj) { continue }
    if ($NameContains -and (($e.Current.Name -as [string]) -notlike "*$NameContains*")) { continue }
    if ($VisibleOnly -and $e.Current.IsOffscreen) { continue }
    $rect = Convert-Rect $e.Current.BoundingRectangle
    $patterns = @()
    foreach ($p in $e.GetSupportedPatterns()) { $patterns += $p.ProgrammaticName }
    $rows.Add([pscustomobject]@{
      index = $rows.Count
      window = $window.Current.Name
      processId = $e.Current.ProcessId
      controlType = ($e.Current.ControlType.ProgrammaticName -replace '^ControlType\.','')
      name = $e.Current.Name
      automationId = $e.Current.AutomationId
      className = $e.Current.ClassName
      enabled = $e.Current.IsEnabled
      offscreen = $e.Current.IsOffscreen
      rect = $rect
      patterns = $patterns
    })
    if ($rows.Count -ge $Max) { break }
  }
  if ($rows.Count -ge $Max) { break }
}

$rows | ConvertTo-Json -Depth 6
