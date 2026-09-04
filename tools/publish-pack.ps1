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
#   2. Upload it as an asset on a GitHub Release. Three modes:
#        -Dev            : the rolling dev pack -- a single reusable "dev" pre-release with a
#                          FIXED asset name (LegendCraft-Pack-dev.zip), so the download URL is
#                          STABLE across iterations and only the sha1 changes. deploy-hud.ps1
#                          uses this so the dev loop never spams releases. Clobbered every
#                          time, by design: that is what makes the URL stable.
#        -Promote <sha1> : take the dev pack, prove it is the build you meant by its sha1, and
#                          re-upload those exact bytes as v<version>.
#        default         : upload an already-versioned zip as v<version>.
#      A v<version> tag that exists is never written to again, in any mode. Production pins a
#      versioned asset and verifies it by hash; re-uploading under a tag somebody is already
#      pinned to breaks that pin without touching their config. A new build is a new version.
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
    [string]$Promote = "",   # sha1 the dev pack must have; promotes those bytes to v<version>
    [string]$Repo    = "OmarZiadeh/LegendCraft-ResourcePack",
    # The GitHub CLI to drive. A seam so the contract tests can run every path against a stub
    # instead of the real releases; a suite that can publish is a suite nobody dares run.
    [string]$GhPath  = ""
)
$ErrorActionPreference = "Stop"

$DIST = Join-Path (Split-Path -Parent $PSScriptRoot) "dist"

# --- Resolve gh (fall back to the winget install path if it isn't on PATH) & check auth. ---
$gh = $GhPath
if (-not $gh) { $gh = (Get-Command gh -ErrorAction SilentlyContinue).Source }
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
    # Under -Promote the version is the one being CREATED, which is the caller's argument and
    # not something the dev pack's name could ever carry.
    if (-not $Promote) { $Version = $Matches['v'] }
    # The fixed-name dev copy and a promoted asset are staged beside the pack they came from,
    # not in this repo's dist/: an explicitly named zip says where its siblings belong.
    $DIST = Split-Path -Parent $zipPath
}
elseif ($Promote) {
    # Promotion always starts from the rolling dev pack; there is nothing else to promote.
    $zipPath = Join-Path $DIST "LegendCraft-Pack-dev.zip"
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

# Nothing goes out that has quietly lost content. A merge over a stale input produces a valid
# zip that is simply missing things, so the failure is invisible until a player joins and the
# art is not there. The audit compares against THIS repo's src/, so it applies to a pack built
# here -- one from anywhere else is not a pack src/ describes, and auditing it would only
# measure the distance between two unrelated trees.
$repoRoot   = Split-Path -Parent $PSScriptRoot
$sourceTree = Join-Path $repoRoot "src"
$ownDist    = Join-Path $repoRoot "dist"
if ((Test-Path -LiteralPath $sourceTree) -and $zipPath.StartsWith($ownDist, [System.StringComparison]::OrdinalIgnoreCase)) {
    & python (Join-Path $PSScriptRoot "check_pack_manifest.py") --pack $zipPath --source-tree $sourceTree
    if ($LASTEXITCODE -ne 0) {
        throw "Refusing to publish $($zipPath): it does not carry everything the source tree holds (see above)."
    }
}

# Promotion takes the dev pack's exact bytes and gives them a version. The sha1 argument is
# what makes it a promotion rather than a fresh upload: the dev asset is clobbered constantly,
# so "the current dev pack" names no particular build, and the caller has to say which build
# they watched behave. A mismatch means the loop moved under them.
if ($Promote) {
    if ($Dev) { throw "-Promote and -Dev are opposite directions; pick one." }
    if (-not $Version) { throw "-Promote needs -Version: the version these bytes become." }
    $devSha = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA1).Hash.ToLowerInvariant()
    if ($devSha -ne $Promote.Trim().ToLowerInvariant()) {
        throw ("Refusing to promote: -Promote names $Promote but $zipPath hashes to $devSha. " +
               "The dev pack moved since the build you meant; re-run the dev loop or promote the sha1 you measured.")
    }
    $sha        = $devSha
    $tag        = "v$Version"
    $asset      = "LegendCraft-Pack-$Version.zip"
    $uploadPath = Join-Path $DIST $asset
    # Copied, never rebuilt: a promotion that re-zips is a different pack with the same name.
    Copy-Item -LiteralPath $zipPath -Destination $uploadPath -Force
}
# Dev mode publishes a FIXED asset name to a reusable "dev" pre-release so the URL never
# changes (only sha1 does). gh names the asset by the file's basename, so copy the versioned
# zip to the fixed name before upload. Default mode keeps the permanent versioned release.
elseif ($Dev) {
    $tag        = "dev"
    $asset      = "LegendCraft-Pack-dev.zip"
    $uploadPath = Join-Path $DIST $asset
    # The merge already writes the fixed name, so the pack handed in is often the upload path
    # itself; copying it over itself is an error, not a no-op.
    if ($uploadPath -ne $zipPath) { Copy-Item -LiteralPath $zipPath -Destination $uploadPath -Force }
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
$ErrorActionPreference = "Stop"

# A versioned release is immutable. Somebody's server.properties may already pin this tag's
# asset by hash, and replacing the bytes behind it fails their clients' hash check on the next
# join without anything changing on their side. Only the rolling dev tag is written twice.
if ($releaseExists -and -not $Dev) {
    throw ("Refusing to publish: $tag already exists on $Repo, and a versioned release is never " +
           "written to again -- a server pinned to it would fail its hash check. Bump the version.")
}

$ErrorActionPreference = "Continue"
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
