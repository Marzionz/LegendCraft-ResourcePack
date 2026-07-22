<#
.SYNOPSIS
  Packages src/ into a distributable Minecraft resource pack zip and emits its SHA1.

.DESCRIPTION
  Minecraft requires pack.mcmeta at the ZIP ROOT, so we archive the CONTENTS of src/
  (not the src/ folder itself). Outputs dist/LegendCraft-Pack-<version>.zip plus a
  .sha1 sidecar — Paper's setResourcePack(url, sha1, required) needs that hex SHA1.
  Generates a placeholder pack.png if one is not present.
#>
param(
    [string]$Configuration = "release"
)

$ErrorActionPreference = "Stop"
$root    = $PSScriptRoot
$srcDir  = Join-Path $root "src"
$distDir = Join-Path $root "dist"
$version = (Get-Content (Join-Path $root "VERSION") -Raw).Trim()

if (-not (Test-Path $srcDir)) { throw "src/ not found at $srcDir" }
if (-not (Test-Path (Join-Path $srcDir "pack.mcmeta"))) { throw "src/pack.mcmeta missing" }

# --- ensure a pack icon exists (placeholder if the artist hasn't dropped one) ---
$packPng = Join-Path $srcDir "pack.png"
if (-not (Test-Path $packPng)) {
    Add-Type -AssemblyName System.Drawing
    $size = 128
    $bmp  = New-Object System.Drawing.Bitmap $size, $size
    $g    = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(20, 18, 28))
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(212, 175, 55)) # legend gold
    $font  = New-Object System.Drawing.Font "Georgia", 52, ([System.Drawing.FontStyle]::Bold)
    $fmt   = New-Object System.Drawing.StringFormat
    $fmt.Alignment = "Center"; $fmt.LineAlignment = "Center"
    $g.DrawString("LC", $font, $brush, (New-Object System.Drawing.RectangleF 0,0,$size,$size), $fmt)
    $g.Dispose()
    $bmp.Save($packPng, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "Generated placeholder pack.png"
}

# --- clean + build ---
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
$zipPath = Join-Path $distDir "LegendCraft-Pack-$version.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

# Archive the CONTENTS of src/ so pack.mcmeta lands at the ZIP ROOT.
#
# NOTE: do NOT use Compress-Archive here — Windows PowerShell writes zip entries with
# BACKSLASH separators, which violate the ZIP spec. Java zip readers (Minecraft) then
# can't find "assets/legendcraft/..." and reject the pack. Build entries by hand with
# forward slashes via System.IO.Compression instead. Skip .gitkeep (dev-only markers).
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$srcFull = (Resolve-Path $srcDir).Path.TrimEnd('\')
$zip = [System.IO.Compression.ZipFile]::Open($zipPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    Get-ChildItem -Path $srcDir -Recurse -File |
        Where-Object { $_.Name -ne '.gitkeep' } |
        ForEach-Object {
            $rel = $_.FullName.Substring($srcFull.Length + 1) -replace '\\', '/'
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $zip, $_.FullName, $rel, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
        }
} finally {
    $zip.Dispose()
}

# --- SHA1 (Paper's resource-pack integrity hash) ---
$sha1 = (Get-FileHash -Algorithm SHA1 -Path $zipPath).Hash.ToLower()
Set-Content -Path "$zipPath.sha1" -Value $sha1 -Encoding ascii -NoNewline

$sizeKb = [math]::Round((Get-Item $zipPath).Length / 1KB, 1)
Write-Host ""
Write-Host "Built  : $zipPath  (${sizeKb} KB)"
Write-Host "Version: $version   pack_format: $((Get-Content (Join-Path $srcDir 'pack.mcmeta') -Raw | ConvertFrom-Json).pack.pack_format)"
Write-Host "SHA1   : $sha1"
