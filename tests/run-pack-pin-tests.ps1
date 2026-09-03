#Requires -Version 5.1
<#
.SYNOPSIS
  Contract tests for the pack-channel rules: check-pack-pin.ps1 and publish-pack.ps1's
  versioned-release and promotion behaviour.

.DESCRIPTION
  Builds every input in a temp directory it owns - fake server.properties files, fake pack
  zips, and a stub standing in for the GitHub CLI - so no arm reaches a real release, a real
  server, or the network. The stub records the argument vectors it was handed, which is how
  the arms assert what WOULD be uploaded without uploading anything.

  Organised by contract area:

    PIN     the prod pre-start guard: what it refuses, and what it exempts
    IMM     a versioned release is immutable
    PROM    -Promote is the only way the dev loop becomes a versioned release

  RUN IT when check-pack-pin.ps1 or publish-pack.ps1 changes:

      powershell -NoProfile -File tests\run-pack-pin-tests.ps1

  ---------------------------------------------------------------------------
  SECTION 16 - acceptance list, then RED, then code.

  Requirement: production pins only an immutable versioned asset. The dev pack is a rolling
  pre-release behind a fixed asset name, clobbered every iteration, so a production server
  pinned to it is pinned to a moving target: the sha1 in its config stops matching the bytes
  at the URL the moment anybody runs the dev loop, and under require-resource-pack every join
  then fails the hash check. mc-dev is the dev loop and is exempt.

  The acceptance criteria, written from that requirement before either script grew the
  behaviour:

    AC-1   a prod config whose resource-pack URL is under the dev release is refused,
           naming the URL                                              PIN-01
    AC-2   a prod config whose pinned asset name ends -dev.zip is refused, even when the
           URL is not under the dev release path                       PIN-02
    AC-3   a prod config whose resource-pack-sha1 does not match the sha1 of the asset at
           its URL is refused, naming both sha1s                       PIN-03
    AC-4   a prod config pinned to a versioned asset whose sha1 matches passes            PIN-04
    AC-5   mc-dev is exempt BY NAME: its own config, dev URL and all, passes with the
           exemption stated rather than silently                       PIN-05
    AC-6   a config with no resource-pack line at all is refused, not waved through - an
           absent pin is not a valid pin                               PIN-06
    AC-7   publish-pack refuses to upload to a v<version> tag that already exists, and
           uploads nothing                                             IMM-01
    AC-8   publish-pack still clobbers the rolling dev pre-release, which is the whole
           point of the dev channel                                    IMM-02
    AC-9   -Promote <sha1> refuses when the dev asset's sha1 is not the argument, and
           uploads nothing                                             PROM-01
    AC-10  -Promote <sha1> on a matching dev asset uploads it to v<version> unchanged,
           and the promoted bytes hash to the same sha1                PROM-02
    AC-11  -Promote prints the prod server.properties lines for the promoted asset        PROM-03
    AC-12  -Promote refuses when the target v<version> tag already exists - promotion
           creates a version, it never replaces one                    PROM-04

  FIRST RED, recorded in tests/RED-pack-pin.txt: all twelve arms ran and all twelve failed.
  check-pack-pin.ps1 did not exist, so PIN-01..PIN-06 failed on the missing script;
  publish-pack.ps1 had no -Promote parameter and no existing-tag refusal, so IMM-01 and
  PROM-01..PROM-04 failed on their assertions and IMM-02 failed on the absent -GhPath seam.
#>

param(
    [switch]$KeepFixture,
    [string]$PinScriptPath,
    [string]$PublishScriptPath
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $PinScriptPath)     { $PinScriptPath     = Join-Path $RepoRoot 'tools\check-pack-pin.ps1' }
if (-not $PublishScriptPath) { $PublishScriptPath = Join-Path $RepoRoot 'tools\publish-pack.ps1' }

$script:Pass = 0
$script:Fail = 0

function Assert {
    param([string]$Id, [string]$What, [bool]$Ok)
    if ($Ok) { $script:Pass++; Write-Host ("  PASS {0}  {1}" -f $Id, $What) }
    else     { $script:Fail++; Write-Host ("  FAIL {0}  {1}" -f $Id, $What) -ForegroundColor Red }
}

# --- fixture ---------------------------------------------------------------
$Fixture = Join-Path ([System.IO.Path]::GetTempPath()) ("packpin-" + [guid]::NewGuid().ToString('n'))
New-Item -ItemType Directory -Force -Path $Fixture | Out-Null
$Dist = Join-Path $Fixture 'dist'
New-Item -ItemType Directory -Force -Path $Dist | Out-Null

# The motd mc-dev advertises. The guard exempts that server by this name, so the suite has to
# use the real value or it is testing an exemption nobody gets.
$McDevMotd = 'LegendCraft Build Server'
$ProdMotd  = 'LegendCraft'
$DevUrl    = 'https://github.com/OmarZiadeh/LegendCraft-ResourcePack/releases/download/dev/LegendCraft-Pack-dev.zip'
$VerUrl    = 'https://github.com/OmarZiadeh/LegendCraft-ResourcePack/releases/download/v0.3.0/LegendCraft-Pack-0.3.0.zip'

function Write-Utf8 {
    param([string]$Path, [string]$Text)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) | Out-Null
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}

function New-Pack {
    param([string]$Path, [string]$Marker)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) | Out-Null
    $staging = Join-Path $Fixture ("stage-" + [guid]::NewGuid().ToString('n'))
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    Write-Utf8 (Join-Path $staging 'pack.mcmeta') $Marker
    if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($staging, $Path)
    $sha = (Get-FileHash -LiteralPath $Path -Algorithm SHA1).Hash.ToLowerInvariant()
    Write-Utf8 ($Path + '.sha1') $sha
    return $sha
}

function New-ServerProperties {
    param([string]$Name, [string]$Motd, [string]$Url, [string]$Sha1, [switch]$NoPack)
    $path = Join-Path $Fixture ("$Name.properties")
    $lines = @("motd=$Motd", "level-name=world")
    if (-not $NoPack) {
        $lines += "resource-pack=" + ($Url -replace ':', '\:')
        $lines += "resource-pack-sha1=$Sha1"
    }
    Write-Utf8 $path (($lines -join "`n") + "`n")
    return $path
}

# The guard has to hash the bytes at the pinned URL. A local file:// URL keeps that a real
# fetch of real bytes while never touching the network.
function As-FileUrl { param([string]$Path) return ([uri]$Path).AbsoluteUri }

# --- the gh stub -----------------------------------------------------------
# Records every argument vector it is handed, and answers `release view` from a list of tags
# the arm declares to exist. Nothing here reaches GitHub.
$GhLog      = Join-Path $Fixture 'gh-calls.log'
$GhTagsFile = Join-Path $Fixture 'gh-existing-tags.txt'
$GhStub     = Join-Path $Fixture 'gh-stub.ps1'
Write-Utf8 $GhStub @'
$logPath  = Join-Path $PSScriptRoot 'gh-calls.log'
$tagsPath = Join-Path $PSScriptRoot 'gh-existing-tags.txt'
Add-Content -LiteralPath $logPath -Value ($args -join ' ')
if ($args[0] -eq 'auth') { exit 0 }
$existing = @()
if (Test-Path -LiteralPath $tagsPath) {
    $existing = (Get-Content -LiteralPath $tagsPath) | Where-Object { $_ -ne '' }
}
if ($args[0] -eq 'release' -and $args[1] -eq 'view') {
    if ($existing -contains $args[2]) { exit 0 } else { exit 1 }
}
exit 0
'@
# publish-pack invokes gh as an executable; a .ps1 cannot be one, so the seam takes a command
# line the suite can point at powershell running the stub.
$GhShim = Join-Path $Fixture 'gh-shim.cmd'
Write-Utf8 $GhShim ("@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"$GhStub`" %*`r`n")

function Reset-Gh {
    param([string[]]$ExistingTags = @())
    if (Test-Path -LiteralPath $GhLog) { Remove-Item -LiteralPath $GhLog -Force }
    Write-Utf8 $GhTagsFile (($ExistingTags -join "`n") + "`n")
}
function Gh-Calls {
    if (-not (Test-Path -LiteralPath $GhLog)) { return @() }
    return @(Get-Content -LiteralPath $GhLog)
}
function Gh-Uploaded {
    return @(Gh-Calls | Where-Object { $_ -match 'release (create|upload)' })
}

# --- runners ---------------------------------------------------------------
function Invoke-Script {
    param([string]$Path, [string[]]$ScriptArgs)
    if (-not (Test-Path -LiteralPath $Path)) {
        return @{ exit = 127; text = "script not found: $Path" }
    }
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $Path @ScriptArgs 2>&1
    return @{ exit = $LASTEXITCODE; text = (($out | Out-String)) }
}
function Invoke-Pin     { param([string[]]$A) return Invoke-Script -Path $PinScriptPath -ScriptArgs $A }

# publish-pack talks to the GitHub CLI, so every arm here drives it through the -GhPath seam
# and a stub. A publish script that does not declare that seam would fall through to the real
# gh and reach the real releases, so the suite refuses to execute one rather than running it
# and hoping the fixture repo name saves it. A fixture that can mutate the world is a defect
# of the gate, not of the subject.
function Invoke-Publish {
    param([string[]]$A)
    if (-not (Test-Path -LiteralPath $PublishScriptPath)) {
        return @{ exit = 127; text = "script not found: $PublishScriptPath" }
    }
    $declared = (Get-Command -Name $PublishScriptPath -CommandType ExternalScript -ErrorAction SilentlyContinue)
    if (-not $declared -or -not $declared.Parameters.ContainsKey('GhPath')) {
        return @{ exit = 126; text = 'publish-pack.ps1 declares no -GhPath seam; refusing to run it against the real gh' }
    }
    return Invoke-Script -Path $PublishScriptPath -ScriptArgs $A
}

# --- shared fixture packs --------------------------------------------------
$DevPack   = Join-Path $Dist 'LegendCraft-Pack-dev.zip'
$DevSha    = New-Pack -Path $DevPack -Marker '{"dev":1}'
$VerPack   = Join-Path $Dist 'LegendCraft-Pack-0.3.0.zip'
$VerSha    = New-Pack -Path $VerPack -Marker '{"ver":1}'
$WrongSha  = '0000000000000000000000000000000000000000'

Write-Host ''
Write-Host 'PIN - the prod pre-start guard'

$devPinned = New-ServerProperties -Name 'prod-dev-url' -Motd $ProdMotd -Url (As-FileUrl $DevPack) -Sha1 $DevSha
$r = Invoke-Pin @('-ServerProperties', $devPinned)
Assert 'PIN-01' 'a prod config pinned under the dev release is refused' (
    $r.exit -ne 0 -and $r.text -match 'dev')

# The dev asset served from a path that is NOT the dev release: the name alone must still refuse.
$renamedDev = Join-Path $Dist 'v9\LegendCraft-Pack-9.9.9-dev.zip'
$renamedSha = New-Pack -Path $renamedDev -Marker '{"dev":1}'
$devNamePinned = New-ServerProperties -Name 'prod-dev-name' -Motd $ProdMotd -Url (As-FileUrl $renamedDev) -Sha1 $renamedSha
$r = Invoke-Pin @('-ServerProperties', $devNamePinned)
Assert 'PIN-02' 'a prod config whose asset name ends -dev.zip is refused' (
    $r.exit -ne 0 -and $r.text -match '\-dev\.zip')

$mismatch = New-ServerProperties -Name 'prod-mismatch' -Motd $ProdMotd -Url (As-FileUrl $VerPack) -Sha1 $WrongSha
$r = Invoke-Pin @('-ServerProperties', $mismatch)
Assert 'PIN-03' 'a prod config whose pinned sha1 does not match the asset is refused, naming both' (
    $r.exit -ne 0 -and $r.text -match $WrongSha -and $r.text -match $VerSha)

$good = New-ServerProperties -Name 'prod-good' -Motd $ProdMotd -Url (As-FileUrl $VerPack) -Sha1 $VerSha
$r = Invoke-Pin @('-ServerProperties', $good)
Assert 'PIN-04' 'a prod config pinned to a matching versioned asset passes' ($r.exit -eq 0)

$mcdev = New-ServerProperties -Name 'mcdev' -Motd $McDevMotd -Url (As-FileUrl $DevPack) -Sha1 $DevSha
$r = Invoke-Pin @('-ServerProperties', $mcdev)
Assert 'PIN-05' 'mc-dev is exempt by name, and says so' (
    $r.exit -eq 0 -and $r.text -match 'exempt')

$nopack = New-ServerProperties -Name 'prod-nopack' -Motd $ProdMotd -NoPack
$r = Invoke-Pin @('-ServerProperties', $nopack)
# The refusal has to be FOR the absent pin. A guard that is simply missing also exits non-zero,
# which is the one way this arm could pass while proving nothing.
Assert 'PIN-06' 'a config with no resource-pack line is refused, naming the absent pin' (
    $r.exit -ne 0 -and $r.text -match 'resource-pack')

Write-Host ''
Write-Host 'IMM - a versioned release is immutable'

Reset-Gh -ExistingTags @('v0.3.0')
$r = Invoke-Publish @('-Zip', $VerPack, '-Repo', 'fixture/repo', '-GhPath', $GhShim)
# "Refused and uploaded nothing" is also true of a script that never ran, so the arm carries
# its own control: gh must have been consulted, and the refusal must name the tag it is about.
Assert 'IMM-01' 'publishing over an existing v<version> tag is refused, and uploads nothing' (
    $r.exit -ne 0 -and (Gh-Uploaded).Count -eq 0 -and
    ((Gh-Calls) -join ' ') -match 'release view v0\.3\.0' -and $r.text -match 'v0\.3\.0')

Reset-Gh -ExistingTags @('dev')
$r = Invoke-Publish @('-Dev', '-Zip', $DevPack, '-Repo', 'fixture/repo', '-GhPath', $GhShim)
Assert 'IMM-02' 'the rolling dev pre-release is still clobbered' (
    $r.exit -eq 0 -and ((Gh-Uploaded) -join ' ') -match '--clobber')

Write-Host ''
Write-Host 'PROM - promotion is the only dev-to-versioned path'

Reset-Gh -ExistingTags @('dev')
$r = Invoke-Publish @('-Promote', $WrongSha, '-Version', '0.4.0', '-Zip', $DevPack, '-Repo', 'fixture/repo', '-GhPath', $GhShim)
Assert 'PROM-01' 'promotion refuses on a sha1 mismatch, naming both sha1s, and uploads nothing' (
    $r.exit -ne 0 -and (Gh-Uploaded).Count -eq 0 -and
    $r.text -match $WrongSha -and $r.text -match $DevSha)

Reset-Gh -ExistingTags @('dev')
$r = Invoke-Publish @('-Promote', $DevSha, '-Version', '0.4.0', '-Zip', $DevPack, '-Repo', 'fixture/repo', '-GhPath', $GhShim)
$uploaded = (Gh-Uploaded) -join ' '
$promotedPath = Join-Path $Dist 'LegendCraft-Pack-0.4.0.zip'
$promotedSha = if (Test-Path -LiteralPath $promotedPath) {
    (Get-FileHash -LiteralPath $promotedPath -Algorithm SHA1).Hash.ToLowerInvariant()
} else { '' }
Assert 'PROM-02' 'promotion uploads the dev bytes unchanged to v<version>' (
    $r.exit -eq 0 -and $uploaded -match 'v0\.4\.0' -and $promotedSha -eq $DevSha)

Assert 'PROM-03' 'promotion prints the prod server.properties lines' (
    $r.text -match 'resource-pack=' -and $r.text -match ("resource-pack-sha1=" + $DevSha))

Reset-Gh -ExistingTags @('dev', 'v0.4.0')
$r = Invoke-Publish @('-Promote', $DevSha, '-Version', '0.4.0', '-Zip', $DevPack, '-Repo', 'fixture/repo', '-GhPath', $GhShim)
Assert 'PROM-04' 'promotion refuses when the target version already exists' (
    $r.exit -ne 0 -and (Gh-Uploaded).Count -eq 0 -and
    ((Gh-Calls) -join ' ') -match 'release view v0\.4\.0' -and $r.text -match 'v0\.4\.0')

Write-Host ''
Write-Host ("{0} passed, {1} failed" -f $script:Pass, $script:Fail)
if ($KeepFixture) { Write-Host "fixture kept: $Fixture" }
else { Remove-Item -LiteralPath $Fixture -Recurse -Force -ErrorAction SilentlyContinue }
if ($script:Fail -gt 0) { exit 1 }
exit 0
