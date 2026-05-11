param(
    [string]$SaveListPath = "D:\Games\BG3_missing_mods.txt",
    [string]$ModsPath = "$env:LOCALAPPDATA\Larian Studios\Baldur's Gate 3\Mods",
    [string]$ModSettingsPath = "$env:LOCALAPPDATA\Larian Studios\Baldur's Gate 3\PlayerProfiles\Public\modsettings.lsx",
    [string]$DivinePath = "$env:LOCALAPPDATA\Temp\codex-lslib\Packed\Tools\Divine.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Escape-XmlValue {
    param([string]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Security.SecurityElement]::Escape($Value)
}

function Get-AttributeValue {
    param(
        [string]$Text,
        [string]$Id
    )

    $match = [regex]::Match($Text, '<attribute\s+id="' + [regex]::Escape($Id) + '"[^>]*\svalue="([^"]*)"')
    if ($match.Success) { return $match.Groups[1].Value }
    return $null
}

function Get-LsxNodeAttributeValue {
    param(
        [System.Xml.XmlNode]$Node,
        [string]$Id
    )

    $attributeNode = $Node.SelectSingleNode("attribute[@id='$Id']")
    if ($attributeNode) { return $attributeNode.GetAttribute("value") }
    return $null
}

function Get-SaveOrder {
    param([string]$Path)

    $pattern = '^\d+\.\s+(?<Name>.+?) \| Folder: (?<Folder>.+?) \| UUID: (?<UUID>[0-9a-fA-F-]{36})(?: \| PublishHandle: (?<PublishHandle>\d+))?'
    $items = New-Object System.Collections.ArrayList
    foreach ($line in Get-Content -LiteralPath $Path) {
        $match = [regex]::Match($line, $pattern)
        if ($match.Success) {
            [void]$items.Add([pscustomobject]@{
                Name          = $match.Groups["Name"].Value.Trim()
                Folder        = $match.Groups["Folder"].Value.Trim()
                UUID          = $match.Groups["UUID"].Value.ToLowerInvariant()
                PublishHandle = if ($match.Groups["PublishHandle"].Success) { $match.Groups["PublishHandle"].Value } else { "0" }
            })
        }
    }
    return $items
}

function Get-PakMetadata {
    param(
        [string]$PakPath,
        [string]$Divine,
        [string]$TempRoot
    )

    $extractRoot = Join-Path $TempRoot ([guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
    & $Divine -g bg3 -a extract-package -s $PakPath -d $extractRoot -x "*meta.lsx" -l off | Out-Null
    $meta = Get-ChildItem -LiteralPath $extractRoot -Recurse -File -Filter "meta.lsx" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $meta) { return $null }

    $text = Get-Content -LiteralPath $meta.FullName -Raw
    $xml = [xml]$text
    $moduleInfo = $xml.SelectSingleNode("//node[@id='ModuleInfo']")
    if (-not $moduleInfo) { return $null }

    $uuid = Get-LsxNodeAttributeValue -Node $moduleInfo -Id "UUID"
    if (-not $uuid) { return $null }

    return [pscustomobject]@{
        Pak           = $PakPath
        Folder        = Get-LsxNodeAttributeValue -Node $moduleInfo -Id "Folder"
        Name          = Get-LsxNodeAttributeValue -Node $moduleInfo -Id "Name"
        UUID          = $uuid.ToLowerInvariant()
        Version64     = Get-LsxNodeAttributeValue -Node $moduleInfo -Id "Version64"
        MD5           = Get-LsxNodeAttributeValue -Node $moduleInfo -Id "MD5"
        PublishHandle = Get-LsxNodeAttributeValue -Node $moduleInfo -Id "PublishHandle"
    }
}

$saveOrder = @(Get-SaveOrder -Path $SaveListPath)
if ($saveOrder.Count -eq 0) { throw "No save mod order found in $SaveListPath" }

$wanted = @{}
foreach ($item in $saveOrder) { $wanted[$item.UUID] = $true }

$tempRoot = Join-Path $env:TEMP ("bg3-write-modsettings-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

try {
    $metadataByUuid = @{}
    foreach ($pak in Get-ChildItem -LiteralPath $ModsPath -File -Filter "*.pak" -ErrorAction SilentlyContinue | Sort-Object Name) {
        $meta = Get-PakMetadata -PakPath $pak.FullName -Divine $DivinePath -TempRoot $tempRoot
        if ($meta -and $wanted.ContainsKey($meta.UUID) -and -not $metadataByUuid.ContainsKey($meta.UUID)) {
            $metadataByUuid[$meta.UUID] = $meta
        }
    }

    $missing = @($saveOrder | Where-Object { -not $metadataByUuid.ContainsKey($_.UUID) })
    if ($missing.Count -gt 0) {
        Write-Warning "Using save-list metadata fallback for: $($missing.Name -join ', ')"
    }

    $backup = "$ModSettingsPath.codex-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    if (Test-Path -LiteralPath $ModSettingsPath) {
        Copy-Item -LiteralPath $ModSettingsPath -Destination $backup -Force
    }

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    [void]$lines.Add('<save>')
    [void]$lines.Add('    <version major="4" minor="8" revision="0" build="700"/>')
    [void]$lines.Add('    <region id="ModuleSettings">')
    [void]$lines.Add('        <node id="root">')
    [void]$lines.Add('            <children>')
    [void]$lines.Add('                <node id="ModOrder">')
    [void]$lines.Add('                    <children>')
    [void]$lines.Add('                        <node id="Module">')
    [void]$lines.Add('                            <attribute id="UUID" type="FixedString" value="cb555efe-2d9e-131f-8195-a89329d218ea"/>')
    [void]$lines.Add('                        </node>')
    foreach ($item in $saveOrder) {
        [void]$lines.Add('                        <node id="Module">')
        [void]$lines.Add("                            <attribute id=""UUID"" type=""FixedString"" value=""$(Escape-XmlValue $item.UUID)""/>")
        [void]$lines.Add('                        </node>')
    }
    [void]$lines.Add('                    </children>')
    [void]$lines.Add('                </node>')
    [void]$lines.Add('                <node id="Mods">')
    [void]$lines.Add('                    <children>')
    [void]$lines.Add('                        <node id="ModuleShortDesc">')
    [void]$lines.Add('                            <attribute id="Folder" type="LSString" value="GustavX"/>')
    [void]$lines.Add('                            <attribute id="MD5" type="LSString" value="ef3fcba3f3684b3088ad1f9874d4957c"/>')
    [void]$lines.Add('                            <attribute id="Name" type="LSString" value="GustavX"/>')
    [void]$lines.Add('                            <attribute id="PublishHandle" type="uint64" value="0"/>')
    [void]$lines.Add('                            <attribute id="UUID" type="guid" value="cb555efe-2d9e-131f-8195-a89329d218ea"/>')
    [void]$lines.Add('                            <attribute id="Version64" type="int64" value="145241946983074840"/>')
    [void]$lines.Add('                        </node>')
    foreach ($item in $saveOrder) {
        $meta = if ($metadataByUuid.ContainsKey($item.UUID)) {
            $metadataByUuid[$item.UUID]
        }
        else {
            [pscustomobject]@{
                Folder        = $item.Folder
                Name          = $item.Name
                Version64     = "1"
                MD5           = ""
                PublishHandle = $item.PublishHandle
            }
        }
        $folder = if ($meta.Folder) { $meta.Folder } else { $item.Folder }
        $name = if ($meta.Name) { $meta.Name } else { $item.Name }
        $version64 = if ($meta.Version64) { $meta.Version64 } else { "1" }
        $md5 = if ($meta.MD5) { $meta.MD5 } else { "" }
        $publishHandle = if ($meta.PublishHandle) { $meta.PublishHandle } elseif ($item.PublishHandle) { $item.PublishHandle } else { "0" }

        [void]$lines.Add('                        <node id="ModuleShortDesc">')
        [void]$lines.Add("                            <attribute id=""Folder"" type=""LSString"" value=""$(Escape-XmlValue $folder)""/>")
        [void]$lines.Add("                            <attribute id=""MD5"" type=""LSString"" value=""$(Escape-XmlValue $md5)""/>")
        [void]$lines.Add("                            <attribute id=""Name"" type=""LSString"" value=""$(Escape-XmlValue $name)""/>")
        [void]$lines.Add("                            <attribute id=""PublishHandle"" type=""uint64"" value=""$(Escape-XmlValue $publishHandle)""/>")
        [void]$lines.Add("                            <attribute id=""UUID"" type=""guid"" value=""$(Escape-XmlValue $item.UUID)""/>")
        [void]$lines.Add("                            <attribute id=""Version64"" type=""int64"" value=""$(Escape-XmlValue $version64)""/>")
        [void]$lines.Add('                        </node>')
    }
    [void]$lines.Add('                    </children>')
    [void]$lines.Add('                </node>')
    [void]$lines.Add('            </children>')
    [void]$lines.Add('        </node>')
    [void]$lines.Add('    </region>')
    [void]$lines.Add('</save>')

    Set-Content -LiteralPath $ModSettingsPath -Value $lines -Encoding UTF8

    [pscustomobject]@{
        SaveOrderCount = $saveOrder.Count
        WrittenPath    = $ModSettingsPath
        BackupPath     = $backup
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
