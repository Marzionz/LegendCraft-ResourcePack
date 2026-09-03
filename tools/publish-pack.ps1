# Publishes the merged LegendCraft resource pack to a PUBLIC GitHub Release, so
# real players (not just the local mc-dev client) can download it.
#
# This is DELIBERATE and separate from deploy-hud.ps1's build/merge steps: run it
# when you actually want players on the new pack. Both dev and prod servers point
# their server.properties resource-pack at the public URL this produces.
#
# What it does:
#   1. Pick the merged pack to publish (newest LegendCraft-Pack-*-dev.zip in
#      dist/, or -Version / -Zip to override). This is the HUD-MERGED pack that
#      merge_dev_pack.py produces -- NOT the models-only base pack.
#   2. Upload it as an asset on a GitHub Release, re-uploading (--clobber) if the
#      release already exists. Two modes:
#        default : permanent release, tag v<version>, versioned asset name.
#        -Dev    : the rolling dev pack -- a single reusable "dev" pre-release with a
#                  FIXED asset name (LegendCraft-Pack-dev.zip), so the download URL is
#                  STABLE across iterations and only the sha1 changes. deploy-hud.ps1
#                  uses this so the dev loop never spams releases.
#   3. Print the public download URL + sha1, plus the exact server.properties
#      lines (resource-pack= / resource-pack-sha1=) to paste into your server.
#
# Prerequisite: the GitHub CLI, authenticated once:
#   winget install --id GitHub.cli -e --source winget
#   gh auth login
param(
    [string]$Version = "",   # e.g. 0.2.93-dev; default = newest merged zip in dist/
    [string]$Zip     = "",   # explicit path to a merged pack zip; overrides -Version
    [switch]$Dev,            # publish to the rolling "dev" pre-release with a stable URL
    [string]$Repo    = "OmarZiadeh/LegendCraft-ResourcePack"
)
$ErrorActionPreference = "Stop"

$DIST = Join-Path (Split-Path -Parent $PSScriptRoot) "dist"

# --- Resolve gh (fall back to the winget install path if it isn't on PATH) & check auth. ---
$gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
if (-not $gh) { $gh = "C:\Program Files\GitHub CLI\gh.exe" }
if (-not (Test-Path $gh)) {
    throw "GitHub CLI 'gh' not found. Install it, then re-run:`n  winget install --id GitHub.cli -e --source winget`n  gh auth login"
}
& $gh auth status 1>$null 2>$null
if ($LASTEXITCODE -ne 0) { throw "gh is installed but not authenticated. Run: gh auth login" }

# --- Resolve which merged zip to publish ---
if ($Zip) {
    $zipPath = (Resolve-Path $Zip).Path
    # The rolling dev pack carries no version in its name -- it is whatever the newest built
    # base pack plus the current plugin builds are -- so "dev" is a legal version here.
    if ($zipPath -notmatch 'LegendCraft-Pack-(?<v>[\d.]+(?:-dev)?|dev)\.zip$') {
        throw "-Zip must point at a LegendCraft-Pack-<version>.zip or LegendCraft-Pack-dev.zip file."
    }
    $Version = $Matches['v']
}
else {
    if (-not $Version) {
        # Newest by semantic version among the merged -dev packs on disk.
        $cand = Get-ChildItem "$DIST\LegendCraft-Pack-*-dev.zip" -ErrorAction SilentlyContinue |
            ForEach-Object {
                if ($_.Name -match 'LegendCraft-Pack-(\d+)\.(\d+)\.(\d+)-dev\.zip') {
                    [pscustomobject]@{
                        File = $_.FullName
                        Ver  = "$($Matches[1]).$($Matches[2]).$($Matches[3])-dev"
                        Key  = [int]$Matches[1]*1000000 + [int]$Matches[2]*1000 + [int]$Matches[3]
                    }
                }
            } | Sort-Object Key -Descending | Select-Object -First 1
        if (-not $cand) { throw "No LegendCraft-Pack-*-dev.zip found in $DIST. Run deploy-hud.ps1 (or merge_dev_pack.py) first to build the merged pack." }
        $Version = $cand.Ver
        $zipPath = $cand.File
    }
    else {
        $zipPath = "$DIST\LegendCraft-Pack-$Version.zip"
    }
}

if (-not (Test-Path $zipPath)) { throw "Pack not found: $zipPath" }
$shaPath = "$zipPath.sha1"
if (-not (Test-Path $shaPath)) { throw "SHA1 sidecar missing: $shaPath (merge_dev_pack.py writes it alongside the zip)." }
$sha    = (Get-Content $shaPath -Raw).Trim()

# Dev mode publishes a FIXED asset name to a reusable "dev" pre-release so the URL never
# changes (only sha1 does). gh names the asset by the file's basename, so copy the versioned
# zip to the fixed name before upload. Default mode keeps the permanent versioned release.
if ($Dev) {
    $tag        = "dev"
    $asset      = "LegendCraft-Pack-dev.zip"
    $uploadPath = Join-Path $DIST $asset
    Copy-Item $zipPath $uploadPath -Force
} else {
    $tag        = "v$Version"
    $asset      = Split-Path $zipPath -Leaf
    $uploadPath = $zipPath
}

Write-Host "Publishing $asset (built from $Version, sha $sha) to $Repo @ $tag ..." -ForegroundColor Cyan

# --- Create the release if absent, then upload/clobber the asset ---
# gh writes normal status (and "release not found") to stderr; under -EA Stop PS 5.1 would
# wrap that as a terminating error, so switch to Continue and gate on $LASTEXITCODE instead.
$ErrorActionPreference = "Continue"
& $gh release view $tag -R $Repo *> $null
$releaseExists = ($LASTEXITCODE -eq 0)
if (-not $releaseExists) {
    $title = if ($Dev) { "LegendCraft Pack (rolling dev)" } else { "LegendCraft Pack $Version" }
    $createArgs = @("release","create",$tag,$uploadPath,"-R",$Repo,
                    "--title",$title,
                    "--notes","Merged resource pack (custom models + BetterHud HUD). Built from $Version, sha1: $sha")
    if ($Dev) { $createArgs += "--prerelease" }
    & $gh @createArgs
} else {
    & $gh release upload $tag $uploadPath -R $Repo --clobber
}
$publishExit = $LASTEXITCODE
$ErrorActionPreference = "Stop"
if ($publishExit -ne 0) { throw "gh release publish failed (exit $publishExit)." }

$url = "https://github.com/$Repo/releases/download/$tag/$asset"

Write-Host ""
Write-Host "DONE - pack published publicly." -ForegroundColor Green
Write-Host "  URL : $url"
Write-Host "  sha1: $sha"
Write-Host ""
Write-Host "Point your server's delivery at it (vanilla server.properties):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  resource-pack=$url"
Write-Host "  resource-pack-sha1=$sha"
Write-Host ""
Write-Host "Then restart the server so it pushes the new pack on join." -ForegroundColor Yellow
