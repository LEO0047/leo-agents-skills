param(
    [string[]]$ScanPath,
    [string]$SevenZipPath,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-SevenZip {
    param([string]$Preferred)
    $candidates = @()
    if ($Preferred) { $candidates += $Preferred }
    $candidates += @(
        "$env:ProgramFiles\Vortex\resources\app.asar.unpacked\node_modules\7z-bin\win32\7z.exe",
        "$env:ProgramFiles\7-Zip\7z.exe",
        "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    $cmd = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
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

function Invoke-ProcessText {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.Arguments = ($Arguments | ForEach-Object {
        if ([string]::IsNullOrEmpty($_)) { '""' }
        elseif ($_ -match '[\s"]') { '"' + ($_.Replace('"', '\"')) + '"' }
        else { $_ }
    }) -join " "
    $process = [System.Diagnostics.Process]::Start($psi)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    return [pscustomobject]@{
        ExitCode = $process.ExitCode
        StdOut = $stdout
        StdErr = $stderr
    }
}

function Get-ArchiveEntries {
    param(
        [string]$ArchivePath,
        [string]$SevenZip
    )
    $run = Invoke-ProcessText -FilePath $SevenZip -Arguments @("l", "-slt", $ArchivePath)
    if ($run.ExitCode -ne 0) {
        throw (($run.StdErr + "`n" + $run.StdOut).Trim())
    }
    $entries = New-Object System.Collections.ArrayList
    foreach ($line in ($run.StdOut -split "`r?`n")) {
        if ($line -like "Path = *") {
            $value = $line.Substring(7)
            if ($value -and $value -ne $ArchivePath -and ($value -notmatch '^[A-Z]:\\')) {
                [void]$entries.Add($value)
            }
        }
    }
    return @($entries | Sort-Object -Unique)
}

function Get-PayloadSummary {
    param([string[]]$Entries)
    $payloadExtensions = @(".pak", ".esp", ".esm", ".esl")
    $binaryExtensions = @(".exe", ".dll", ".msi")
    $scriptExtensions = @(".bat", ".cmd", ".ps1", ".vbs", ".js")
    $archiveExtensions = @(".zip", ".7z", ".rar")

    $files = @($Entries | Where-Object { $_ -match '\.[^\\/]+$' })
    $payloads = @($files | Where-Object { $payloadExtensions -contains ([System.IO.Path]::GetExtension($_).ToLowerInvariant()) })
    $binaries = @($files | Where-Object { $binaryExtensions -contains ([System.IO.Path]::GetExtension($_).ToLowerInvariant()) })
    $scripts = @($files | Where-Object { $scriptExtensions -contains ([System.IO.Path]::GetExtension($_).ToLowerInvariant()) })
    $nestedArchives = @($files | Where-Object { $archiveExtensions -contains ([System.IO.Path]::GetExtension($_).ToLowerInvariant()) })
    $loose = @($files | Where-Object {
        $ext = [System.IO.Path]::GetExtension($_).ToLowerInvariant()
        -not (($payloadExtensions + $binaryExtensions + $scriptExtensions + $archiveExtensions + @(".txt", ".md", ".json", ".xml", ".ini", ".toml", ".yaml", ".yml")) -contains $ext)
    })

    [pscustomobject]@{
        EntryCount = $Entries.Count
        Payloads = $payloads
        Binaries = $binaries
        Scripts = $scripts
        NestedArchives = $nestedArchives
        LooseFileCount = $loose.Count
        LooseFileSamples = @($loose | Select-Object -First 20)
        HasInstallablePayload = $payloads.Count -gt 0
        HasUnsafeExecutable = ($binaries.Count + $scripts.Count) -gt 0
        RequiresGameAdapter = ($payloads.Count -gt 0 -or $loose.Count -gt 0)
    }
}

if (-not $ScanPath -or $ScanPath.Count -eq 0) {
    throw "Provide at least one -ScanPath"
}

$sevenZip = Resolve-SevenZip -Preferred $SevenZipPath
$files = New-Object System.Collections.ArrayList
foreach ($path in $ScanPath) {
    if (-not (Test-Path -LiteralPath $path)) { continue }
    $item = Get-Item -LiteralPath $path
    if ($item.PSIsContainer) {
        Get-ChildItem -LiteralPath $item.FullName -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension.ToLowerInvariant() -in @(".zip", ".7z", ".rar", ".pak") } |
            ForEach-Object { [void]$files.Add($_) }
    }
    else {
        [void]$files.Add($item)
    }
}

$results = foreach ($file in ($files | Sort-Object FullName -Unique)) {
    $extension = $file.Extension.ToLowerInvariant()
    $locked = Test-Locked -FilePath $file.FullName
    $entries = @()
    $errorText = $null

    if ($extension -eq ".pak") {
        $entries = @($file.Name)
    }
    elseif ($extension -in @(".zip", ".7z", ".rar")) {
        if (-not $sevenZip) {
            $errorText = "7z.exe not found"
        }
        elseif ($locked) {
            $errorText = "Locked"
        }
        else {
            try { $entries = @(Get-ArchiveEntries -ArchivePath $file.FullName -SevenZip $sevenZip) }
            catch { $errorText = $_.Exception.Message }
        }
    }
    else {
        $errorText = "Unsupported extension"
    }

    $summary = Get-PayloadSummary -Entries $entries
    [pscustomobject]@{
        Name = $file.Name
        FullName = $file.FullName
        Extension = $extension
        Length = $file.Length
        LastWriteTime = $file.LastWriteTime
        Locked = $locked
        Status = if ($errorText) { "Blocked" } else { "Inspected" }
        Error = $errorText
        EntryCount = $summary.EntryCount
        Payloads = $summary.Payloads
        Binaries = $summary.Binaries
        Scripts = $summary.Scripts
        NestedArchives = $summary.NestedArchives
        LooseFileCount = $summary.LooseFileCount
        LooseFileSamples = $summary.LooseFileSamples
        HasInstallablePayload = $summary.HasInstallablePayload
        HasUnsafeExecutable = $summary.HasUnsafeExecutable
        RequiresGameAdapter = $summary.RequiresGameAdapter
    }
}

$output = [pscustomobject]@{
    SevenZipPath = $sevenZip
    ScannedCount = @($results).Count
    Results = @($results)
}

if ($Json) {
    $output | ConvertTo-Json -Depth 8
}
else {
    $output.Results | Select-Object Status, Name, Extension, EntryCount, HasInstallablePayload, HasUnsafeExecutable, LooseFileCount, Error | Format-Table -AutoSize
}
