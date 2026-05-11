param(
    [string]$GameId,
    [string]$DownloadsRoot = "$env:APPDATA\Vortex\downloads",
    [string]$Path,
    [int]$SampleSeconds = 3,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-DownloadPath {
    if ($Path) { return $Path }
    if (-not $GameId) { throw "Provide -GameId or -Path" }
    return Join-Path $DownloadsRoot $GameId
}

function Test-Locked {
    param([string]$FilePath)
    try {
        $stream = [System.IO.File]::Open($FilePath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::None)
        $stream.Dispose()
        return $false
    }
    catch {
        return $true
    }
}

$target = Resolve-DownloadPath
if (-not (Test-Path -LiteralPath $target)) {
    $result = [pscustomobject]@{
        Path = $target
        Status = "MissingFolder"
        Files = @()
    }
    if ($Json) { $result | ConvertTo-Json -Depth 6 } else { $result }
    exit 0
}

$first = @{}
foreach ($file in Get-ChildItem -LiteralPath $target -File -Recurse -ErrorAction SilentlyContinue) {
    $first[$file.FullName] = $file.Length
}

if ($SampleSeconds -gt 0) { Start-Sleep -Seconds $SampleSeconds }

$files = foreach ($file in Get-ChildItem -LiteralPath $target -File -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending) {
    $oldLength = if ($first.ContainsKey($file.FullName)) { [int64]$first[$file.FullName] } else { -1 }
    $locked = Test-Locked -FilePath $file.FullName
    $stable = ($oldLength -eq $file.Length)
    $state = if ($locked) { "Locked" } elseif (-not $stable) { "Pending" } else { "Ready" }

    [pscustomobject]@{
        Name = $file.Name
        FullName = $file.FullName
        Extension = $file.Extension.ToLowerInvariant()
        Length = $file.Length
        PreviousLength = $oldLength
        Stable = $stable
        Locked = $locked
        State = $state
        LastWriteTime = $file.LastWriteTime
    }
}

$summary = [pscustomobject]@{
    Path = (Resolve-Path -LiteralPath $target).Path
    SampleSeconds = $SampleSeconds
    FileCount = @($files).Count
    ReadyCount = @($files | Where-Object { $_.State -eq "Ready" }).Count
    PendingCount = @($files | Where-Object { $_.State -eq "Pending" }).Count
    LockedCount = @($files | Where-Object { $_.State -eq "Locked" }).Count
    Files = @($files)
}

if ($Json) {
    $summary | ConvertTo-Json -Depth 8
}
else {
    $summary.Files | Select-Object State, Name, Length, LastWriteTime, FullName | Format-Table -AutoSize
    ""
    "Ready: $($summary.ReadyCount)  Pending: $($summary.PendingCount)  Locked: $($summary.LockedCount)"
}
