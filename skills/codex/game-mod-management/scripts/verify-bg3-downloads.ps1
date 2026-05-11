param(
    [switch]$Install,
    [switch]$Force,
    [switch]$Json,
    [string]$StatusPath = "D:\Games\BG3_mod_fix_status.txt",
    [string]$ModsPath = "$env:LOCALAPPDATA\Larian Studios\Baldur's Gate 3\Mods",
    [string[]]$ScanPath = @(
        "$env:USERPROFILE\Downloads",
        "D:\Games\BG3ModDownloads",
        "$env:APPDATA\Vortex\downloads\baldursgate3"
    ),
    [string]$DivinePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Resolve-ExistingPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    if (Test-Path -LiteralPath $Path) {
        return (Resolve-Path -LiteralPath $Path).Path
    }
    return $null
}

function Find-Divine {
    param([string]$PreferredPath)

    $candidates = @()
    if ($PreferredPath) { $candidates += $PreferredPath }
    $candidates += @(
        "$env:LOCALAPPDATA\Temp\codex-lslib\Packed\Tools\Divine.exe",
        "$env:LOCALAPPDATA\Temp\codex-lslib-1187\ExportTool-v1.18.7\Tools\divine.exe",
        "D:\Games\BG3ModDownloads\ExportTool-v1.20.4\Tools\Divine.exe",
        "D:\Games\BG3ModDownloads\github\ExportTool-v1.20.4\Tools\Divine.exe"
    )

    foreach ($candidate in $candidates) {
        $resolved = Resolve-ExistingPath $candidate
        if ($resolved) { return $resolved }
    }

    return $null
}

function Find-SevenZip {
    $candidates = @(
        "$env:ProgramFiles\Vortex\resources\app.asar.unpacked\node_modules\7z-bin\win32\7z.exe",
        "$env:ProgramFiles\7-Zip\7z.exe",
        "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
    )

    foreach ($candidate in $candidates) {
        $resolved = Resolve-ExistingPath $candidate
        if ($resolved) { return $resolved }
    }

    $command = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }

    return $null
}

function Invoke-ExternalProcess {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.Arguments = ($Arguments | ForEach-Object {
        if ([string]::IsNullOrEmpty($_)) {
            '""'
        }
        elseif ($_ -match '[\s"]') {
            '"' + ($_.Replace('"', '\"')) + '"'
        }
        else {
            $_
        }
    }) -join " "

    $process = [System.Diagnostics.Process]::Start($psi)
    $process.WaitForExit()
    return $process.ExitCode
}

function Get-MissingMods {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing status file: $Path"
    }

    $mods = [ordered]@{}
    $linePattern = '^- (?<Name>.+?) \| Folder: (?<Folder>.+?) \| UUID: (?<UUID>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\s*$'

    foreach ($line in Get-Content -LiteralPath $Path) {
        $match = [regex]::Match($line, $linePattern)
        if ($match.Success) {
            $uuid = $match.Groups["UUID"].Value.ToLowerInvariant()
            $mods[$uuid] = [pscustomobject]@{
                Name   = $match.Groups["Name"].Value.Trim()
                Folder = $match.Groups["Folder"].Value.Trim()
                UUID   = $uuid
            }
        }
    }

    if ($mods.Count -eq 0) {
        throw "No missing mod UUIDs found in: $Path"
    }

    return $mods
}

function Get-MatchesFromText {
    param(
        [string]$Text,
        [hashtable]$Missing,
        [string]$Evidence
    )

    $matches = New-Object System.Collections.ArrayList
    if ([string]::IsNullOrWhiteSpace($Text)) { return $matches }

    $uuidPattern = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    foreach ($match in [regex]::Matches($Text, $uuidPattern)) {
        $uuid = $match.Value.ToLowerInvariant()
        if ($Missing.Contains($uuid)) {
            [void]$matches.Add([pscustomobject]@{
                UUID     = $uuid
                Name     = $Missing[$uuid].Name
                Folder   = $Missing[$uuid].Folder
                Evidence = $Evidence
            })
        }
    }

    return $matches
}

function Get-MatchesFromInfoJsonText {
    param(
        [string]$Text,
        [hashtable]$Missing,
        [string]$Evidence
    )

    $matches = New-Object System.Collections.ArrayList
    if ([string]::IsNullOrWhiteSpace($Text)) { return $matches }

    try {
        $parsed = $Text | ConvertFrom-Json
        $items = @()
        if ($null -ne $parsed.Mods) { $items += @($parsed.Mods) }
        if ($null -ne $parsed.UUID -or $null -ne $parsed.ModGuid) { $items += $parsed }

        foreach ($item in $items) {
            $candidateUuid = $null
            foreach ($propertyName in @("UUID", "ModGuid", "Guid")) {
                if ($item.PSObject.Properties.Name -contains $propertyName -and $item.$propertyName) {
                    $candidateUuid = [string]$item.$propertyName
                    break
                }
            }

            if ($candidateUuid -and $candidateUuid -match '^[0-9a-fA-F-]{36}$') {
                $uuid = $candidateUuid.ToLowerInvariant()
                if ($Missing.Contains($uuid)) {
                    [void]$matches.Add([pscustomobject]@{
                        UUID     = $uuid
                        Name     = $Missing[$uuid].Name
                        Folder   = $Missing[$uuid].Folder
                        Evidence = $Evidence
                    })
                }
            }
        }
    }
    catch {
        Add-Items -List $matches -Items (Get-MatchesFromText -Text $Text -Missing $Missing -Evidence $Evidence)
    }

    return $matches
}

function Merge-Matches {
    param([object[]]$MatchSets)

    $seen = @{}
    $out = New-Object System.Collections.ArrayList
    foreach ($match in $MatchSets) {
        if ($null -eq $match) { continue }
        foreach ($item in @($match)) {
            if ($null -eq $item -or -not $item.UUID) { continue }
            $key = "$($item.UUID)|$($item.Evidence)"
            if (-not $seen.ContainsKey($key)) {
                $seen[$key] = $true
                [void]$out.Add($item)
            }
        }
    }
    return $out
}

function Add-Items {
    param(
        [object]$List,
        [object]$Items
    )

    foreach ($item in @($Items)) {
        if ($null -ne $item) {
            [void]$List.Add($item)
        }
    }
}

function Read-ZipEntryText {
    param(
        [System.IO.Compression.ZipArchive]$Zip,
        [System.IO.Compression.ZipArchiveEntry]$Entry
    )

    $stream = $Entry.Open()
    try {
        $reader = [System.IO.StreamReader]::new($stream)
        try { return $reader.ReadToEnd() }
        finally { $reader.Dispose() }
    }
    finally {
        $stream.Dispose()
    }
}

function Expand-ZipPakToTemp {
    param(
        [System.IO.Compression.ZipArchive]$Zip,
        [System.IO.Compression.ZipArchiveEntry]$Entry,
        [string]$TempRoot
    )

    $safeName = ($Entry.FullName -replace '[\\/:*?"<>|]', '_')
    $target = Join-Path $TempRoot $safeName
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($Entry, $target, $true)
    return $target
}

function Expand-ExternalArchiveToTemp {
    param(
        [string]$ArchivePath,
        [string]$SevenZip,
        [string]$TempRoot
    )

    if (-not $SevenZip) {
        throw "7z.exe not found; cannot inspect '$ArchivePath'"
    }

    $extractRoot = Join-Path $TempRoot ("archive-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null

    $arguments = @("x", "-y", "-o$extractRoot", $ArchivePath)
    $exitCode = Invoke-ExternalProcess -FilePath $SevenZip -Arguments $arguments
    if ($exitCode -ne 0) {
        throw "7z.exe failed with exit code $exitCode"
    }

    return $extractRoot
}

function Get-PakMatches {
    param(
        [string]$PakPath,
        [hashtable]$Missing,
        [string]$Divine,
        [string]$TempRoot,
        [string]$EvidencePrefix = "pak"
    )

    $matches = New-Object System.Collections.ArrayList
    $fileName = [System.IO.Path]::GetFileName($PakPath)
    Add-Items -List $matches -Items (Get-MatchesFromText -Text $fileName -Missing $Missing -Evidence "$EvidencePrefix filename")

    $folder = Split-Path -Parent $PakPath
    foreach ($sidecar in @("info.json", "meta.lsx")) {
        $sidecarPath = Join-Path $folder $sidecar
        if (Test-Path -LiteralPath $sidecarPath) {
            $text = Get-Content -LiteralPath $sidecarPath -Raw
            if ($sidecar -eq "info.json") {
                Add-Items -List $matches -Items (Get-MatchesFromInfoJsonText -Text $text -Missing $Missing -Evidence "$EvidencePrefix sidecar info.json")
            }
            else {
                Add-Items -List $matches -Items (Get-MatchesFromText -Text $text -Missing $Missing -Evidence "$EvidencePrefix sidecar meta.lsx")
            }
        }
    }

    if ($Divine) {
        $extractRoot = Join-Path $TempRoot ("extract-" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
        try {
            $arguments = @(
                "-g", "bg3",
                "-a", "extract-package",
                "-s", $PakPath,
                "-d", $extractRoot,
                "-x", "*meta.lsx",
                "-l", "off"
            )
            $exitCode = Invoke-ExternalProcess -FilePath $Divine -Arguments $arguments
            if ($exitCode -eq 0) {
                foreach ($meta in Get-ChildItem -LiteralPath $extractRoot -Recurse -File -Filter "meta.lsx" -ErrorAction SilentlyContinue) {
                    $text = Get-Content -LiteralPath $meta.FullName -Raw -ErrorAction SilentlyContinue
                    Add-Items -List $matches -Items (Get-MatchesFromText -Text $text -Missing $Missing -Evidence "$EvidencePrefix Divine meta.lsx")
                }
            }
        }
        catch {
            Write-Warning "Divine failed for '$PakPath': $($_.Exception.Message)"
        }
        finally {
            if (Test-Path -LiteralPath $extractRoot) {
                Remove-Item -LiteralPath $extractRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    return Merge-Matches -MatchSets $matches
}

function New-Result {
    param(
        [string]$ArchivePath,
        [string]$PakPath,
        [string]$PakEntry,
        [object[]]$Matches,
        [string]$SourceKind
    )

    foreach ($match in $Matches) {
        [pscustomobject]@{
            UUID       = $match.UUID
            Name       = $match.Name
            Folder     = $match.Folder
            SourceKind = $SourceKind
            Archive    = $ArchivePath
            Pak        = $PakPath
            PakEntry   = $PakEntry
            Evidence   = $match.Evidence
        }
    }
}

function Install-Result {
    param(
        [object]$Result,
        [string]$DestinationModsPath,
        [switch]$Overwrite,
        [string]$TempRoot
    )

    New-Item -ItemType Directory -Force -Path $DestinationModsPath | Out-Null

    $sourcePath = $Result.Pak
    if (-not $sourcePath -and $Result.Archive -and $Result.PakEntry) {
        $zip = [System.IO.Compression.ZipFile]::OpenRead($Result.Archive)
        try {
            $entry = $zip.Entries | Where-Object { $_.FullName -eq $Result.PakEntry } | Select-Object -First 1
            if (-not $entry) { throw "Cannot find zip entry '$($Result.PakEntry)' in '$($Result.Archive)'" }
            $sourcePath = Expand-ZipPakToTemp -Zip $zip -Entry $entry -TempRoot $TempRoot
        }
        finally {
            $zip.Dispose()
        }
    }

    if (-not $sourcePath -or -not (Test-Path -LiteralPath $sourcePath)) {
        throw "No installable pak source for $($Result.Name) ($($Result.UUID))"
    }

    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($sourcePath)
    $targetFile = "{0}_{1}.pak" -f $baseName, $Result.UUID
    $targetPath = Join-Path $DestinationModsPath $targetFile

    if ((Test-Path -LiteralPath $targetPath) -and -not $Overwrite) {
        return [pscustomobject]@{
            UUID   = $Result.UUID
            Name   = $Result.Name
            Status = "SkippedAlreadyExists"
            Target = $targetPath
        }
    }

    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force:$Overwrite
    return [pscustomobject]@{
        UUID   = $Result.UUID
        Name   = $Result.Name
        Status = "Installed"
        Target = $targetPath
    }
}

$missing = Get-MissingMods -Path $StatusPath
$divine = Find-Divine -PreferredPath $DivinePath
$sevenZip = Find-SevenZip
$tempRoot = Join-Path $env:TEMP ("bg3-verify-downloads-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

$results = New-Object System.Collections.ArrayList
$installActions = New-Object System.Collections.ArrayList

try {
    $files = New-Object System.Collections.ArrayList
    foreach ($path in $ScanPath) {
        $resolved = Resolve-ExistingPath $path
        if (-not $resolved) { continue }

        Get-ChildItem -LiteralPath $resolved -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension -in @(".zip", ".pak", ".rar", ".7z") } |
            ForEach-Object { [void]$files.Add($_) }
    }

    foreach ($file in ($files | Sort-Object FullName -Unique)) {
        if ($file.Extension -ieq ".pak") {
            $matches = Get-PakMatches -PakPath $file.FullName -Missing $missing -Divine $divine -TempRoot $tempRoot -EvidencePrefix "pak"
            if (@($matches).Count -gt 0) {
                Add-Items -List $results -Items (New-Result -ArchivePath $null -PakPath $file.FullName -PakEntry $null -Matches $matches -SourceKind "pak")
            }
            continue
        }

        if ($file.Extension -ieq ".zip") {
            $zip = $null
            try {
                $zip = [System.IO.Compression.ZipFile]::OpenRead($file.FullName)
                $zipLevelMatches = New-Object System.Collections.ArrayList

                foreach ($entry in $zip.Entries) {
                    $entryName = $entry.FullName
                    if ($entryName -match '(^|/|\\)(info\.json)$') {
                        $text = Read-ZipEntryText -Zip $zip -Entry $entry
                        Add-Items -List $zipLevelMatches -Items (Get-MatchesFromInfoJsonText -Text $text -Missing $missing -Evidence "zip info.json: $entryName")
                    }
                    elseif ($entryName -match '(^|/|\\)(meta\.lsx)$') {
                        $text = Read-ZipEntryText -Zip $zip -Entry $entry
                        Add-Items -List $zipLevelMatches -Items (Get-MatchesFromText -Text $text -Missing $missing -Evidence "zip meta.lsx: $entryName")
                    }
                }

                $pakEntries = @($zip.Entries | Where-Object { $_.FullName -match '\.pak$' })
                foreach ($pakEntry in $pakEntries) {
                    $entryMatches = New-Object System.Collections.ArrayList
                    Add-Items -List $entryMatches -Items (Get-MatchesFromText -Text $pakEntry.FullName -Missing $missing -Evidence "zip pak filename: $($pakEntry.FullName)")

                    if ($pakEntries.Count -eq 1) {
                        Add-Items -List $entryMatches -Items $zipLevelMatches
                    }

                    if (@($entryMatches).Count -eq 0 -and $divine) {
                        $expandedPak = Expand-ZipPakToTemp -Zip $zip -Entry $pakEntry -TempRoot $tempRoot
                        Add-Items -List $entryMatches -Items (Get-PakMatches -PakPath $expandedPak -Missing $missing -Divine $divine -TempRoot $tempRoot -EvidencePrefix "zip pak")
                    }

                    $entryMatches = Merge-Matches -MatchSets $entryMatches
                    if (@($entryMatches).Count -gt 0) {
                        Add-Items -List $results -Items (New-Result -ArchivePath $file.FullName -PakPath $null -PakEntry $pakEntry.FullName -Matches $entryMatches -SourceKind "zip")
                    }
                }
            }
            catch {
                Write-Warning "Cannot inspect zip '$($file.FullName)': $($_.Exception.Message)"
            }
            finally {
                if ($zip) { $zip.Dispose() }
            }
        }

        if ($file.Extension -in @(".rar", ".7z")) {
            try {
                $extractRoot = Expand-ExternalArchiveToTemp -ArchivePath $file.FullName -SevenZip $sevenZip -TempRoot $tempRoot

                $archiveLevelMatches = New-Object System.Collections.ArrayList
                foreach ($metadata in Get-ChildItem -LiteralPath $extractRoot -Recurse -File -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name -in @("info.json", "meta.lsx") }) {
                    $text = Get-Content -LiteralPath $metadata.FullName -Raw -ErrorAction SilentlyContinue
                    if ($metadata.Name -eq "info.json") {
                        Add-Items -List $archiveLevelMatches -Items (Get-MatchesFromInfoJsonText -Text $text -Missing $missing -Evidence "$($file.Extension.TrimStart('.')) info.json: $($metadata.FullName.Substring($extractRoot.Length).TrimStart('\'))")
                    }
                    else {
                        Add-Items -List $archiveLevelMatches -Items (Get-MatchesFromText -Text $text -Missing $missing -Evidence "$($file.Extension.TrimStart('.')) meta.lsx: $($metadata.FullName.Substring($extractRoot.Length).TrimStart('\'))")
                    }
                }

                $pakFiles = @(Get-ChildItem -LiteralPath $extractRoot -Recurse -File -Filter "*.pak" -ErrorAction SilentlyContinue)
                foreach ($pakFile in $pakFiles) {
                    $pakMatches = New-Object System.Collections.ArrayList
                    Add-Items -List $pakMatches -Items (Get-MatchesFromText -Text $pakFile.Name -Missing $missing -Evidence "$($file.Extension.TrimStart('.')) pak filename: $($pakFile.Name)")

                    if ($pakFiles.Count -eq 1) {
                        Add-Items -List $pakMatches -Items $archiveLevelMatches
                    }

                    if (@($pakMatches).Count -eq 0 -and $divine) {
                        Add-Items -List $pakMatches -Items (Get-PakMatches -PakPath $pakFile.FullName -Missing $missing -Divine $divine -TempRoot $tempRoot -EvidencePrefix "$($file.Extension.TrimStart('.')) pak")
                    }

                    $pakMatches = Merge-Matches -MatchSets $pakMatches
                    if (@($pakMatches).Count -gt 0) {
                        Add-Items -List $results -Items (New-Result -ArchivePath $file.FullName -PakPath $pakFile.FullName -PakEntry $null -Matches $pakMatches -SourceKind $file.Extension.TrimStart('.'))
                    }
                }
            }
            catch {
                Write-Warning "Cannot inspect archive '$($file.FullName)': $($_.Exception.Message)"
            }
        }
    }

    $deduped = $results |
        Sort-Object UUID, SourceKind, Archive, Pak, PakEntry, Evidence -Unique

    if ($Install) {
        $bestByUuid = [ordered]@{}
        foreach ($result in $deduped) {
            if (-not $bestByUuid.Contains($result.UUID)) {
                $bestByUuid[$result.UUID] = $result
            }
        }

        foreach ($uuid in $bestByUuid.Keys) {
            [void]$installActions.Add((Install-Result -Result $bestByUuid[$uuid] -DestinationModsPath $ModsPath -Overwrite:$Force -TempRoot $tempRoot))
        }
    }

    $summary = [pscustomobject]@{
        MissingUuidCount = $missing.Count
        ScannedFileCount = $files.Count
        DivinePath       = $divine
        SevenZipPath     = $sevenZip
        ResultCount      = @($deduped).Count
        Results          = @($deduped)
        InstallActions   = @($installActions)
    }

    if ($Json) {
        $summary | ConvertTo-Json -Depth 8
    }
    else {
        "Missing UUIDs: $($summary.MissingUuidCount)"
        "Scanned files: $($summary.ScannedFileCount)"
        "Divine: $(if ($summary.DivinePath) { $summary.DivinePath } else { 'not found; filename/info.json/meta.lsx only' })"
        "7z: $(if ($summary.SevenZipPath) { $summary.SevenZipPath } else { 'not found; .rar/.7z disabled' })"
        ""
        if ($summary.ResultCount -eq 0) {
            "No matching missing mods found."
        }
        else {
            "Matches:"
            $summary.Results |
                Select-Object Name, UUID, SourceKind, PakEntry, Pak, Archive, Evidence |
                Format-Table -AutoSize
        }

        if ($Install) {
            ""
            "Install actions:"
            $summary.InstallActions | Format-Table -AutoSize
        }
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
