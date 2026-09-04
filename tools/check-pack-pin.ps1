#Requires -Version 5.1
<#
.SYNOPSIS
  Pre-start guard: a production server pins only an immutable versioned pack.

.DESCRIPTION
  The dev pack is a rolling pre-release behind a fixed asset name, clobbered on every
  iteration of the HUD loop. A production server pinned to it is pinned to a moving target:
  the sha1 in its config stops matching the bytes at that URL the moment anyone runs the loop,
  and with require-resource-pack=true every join then fails the hash check and is
  disconnected. That is an outage for everyone, produced by a change nobody made to the
  production server.

  So this refuses three things, and the third is the one that catches a pin nobody touched:

    the URL is under the dev release
    the pinned asset is named as a dev build
    the pinned sha1 is not the sha1 of the bytes now served at that URL

  The development server is the dev loop and is exempt BY NAME - it is supposed to follow the
  rolling asset. The exemption is stated on stdout rather than being a silent pass, because a
  guard that can exempt has to say when it did.

.EXAMPLE
  powershell -NoProfile -File tools\check-pack-pin.ps1 -ServerProperties C:\srv\server.properties
#>

param(
    [Parameter(Mandatory = $true)][string]$ServerProperties
)

$ErrorActionPreference = 'Stop'

# The servers that ARE the dev loop, by the motd they advertise. A name rather than a path,
# because a path says where a checkout happens to sit and a motd is the server's own identity.
$DEV_SERVER_MOTDS = @('LegendCraft Build Server')

# The rolling pre-release's tag, as it appears in a release download URL, and the suffix its
# asset carries. Either alone is enough to refuse.
$DEV_RELEASE_URL_SEGMENT = '/releases/download/dev/'
$DEV_ASSET_SUFFIX = '-dev.zip'

$PACK_KEY = 'resource-pack'
$SHA1_KEY = 'resource-pack-sha1'
$MOTD_KEY = 'motd'

function Get-Property {
    param([string[]]$Lines, [string]$Key)
    foreach ($line in $Lines) {
        if ($line -match ('^' + [regex]::Escape($Key) + '=(.*)$')) {
            # .properties escapes the colon in a URL; the value is the unescaped form.
            return ($Matches[1] -replace '\\:', ':').Trim()
        }
    }
    return $null
}

function Get-RemoteSha1 {
    param([string]$Url)
    $temp = [System.IO.Path]::GetTempFileName()
    try {
        $client = New-Object System.Net.WebClient
        try { $client.DownloadFile($Url, $temp) } finally { $client.Dispose() }
        return (Get-FileHash -LiteralPath $temp -Algorithm SHA1).Hash.ToLowerInvariant()
    }
    finally { Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue }
}

if (-not (Test-Path -LiteralPath $ServerProperties)) {
    Write-Host "FAIL: no server.properties at $ServerProperties" -ForegroundColor Red
    exit 1
}
$lines = Get-Content -LiteralPath $ServerProperties

$motd = Get-Property -Lines $lines -Key $MOTD_KEY
if ($motd -and ($DEV_SERVER_MOTDS -contains $motd)) {
    Write-Host "EXEMPT: '$motd' is the development server; it follows the rolling dev pack by design."
    exit 0
}

$url = Get-Property -Lines $lines -Key $PACK_KEY
if ([string]::IsNullOrWhiteSpace($url)) {
    Write-Host "FAIL: no $PACK_KEY is set in $ServerProperties" -ForegroundColor Red
    Write-Host "      an absent pin is not a valid pin: the server pushes nothing and every custom model is missing."
    exit 1
}

$failures = @()
if ($url.Contains($DEV_RELEASE_URL_SEGMENT)) {
    $failures += "$PACK_KEY points under the rolling dev release: $url"
}
$asset = $url.Split('/')[-1]
if ($asset.EndsWith($DEV_ASSET_SUFFIX)) {
    $failures += "the pinned asset is a dev build: $asset ends $DEV_ASSET_SUFFIX"
}

$pinned = Get-Property -Lines $lines -Key $SHA1_KEY
if ([string]::IsNullOrWhiteSpace($pinned)) {
    $failures += "no $SHA1_KEY is set; the client cannot verify what it downloaded"
}
elseif ($failures.Count -eq 0) {
    # Only worth fetching once the URL itself is legal; a dev URL is refused whatever it serves.
    $served = Get-RemoteSha1 -Url $url
    if ($served -ne $pinned.ToLowerInvariant()) {
        $failures += "$SHA1_KEY is $pinned but the asset at that URL hashes to $served"
    }
}

if ($failures.Count -gt 0) {
    Write-Host "FAIL: $ServerProperties" -ForegroundColor Red
    foreach ($failure in $failures) { Write-Host "  $failure" -ForegroundColor Red }
    exit 1
}

Write-Host "OK: pinned to $asset, sha1 $pinned, and the asset at that URL matches."
exit 0
