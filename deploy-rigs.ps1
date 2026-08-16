<#
.SYNOPSIS
  Stages named .bbmodel rigs from the authoring tree into a BetterModel-shaped
  folder, and writes the verification list the owner works through at the box.

.DESCRIPTION
  STAGE ONLY, and enforced rather than promised: a destination inside a
  plugins/BetterModel folder, or anywhere under a live server root, is refused
  before anything is read, written or deleted. mc-dev is shared, so the copy
  into plugins/BetterModel/models is the owner's step, taken under the deploy
  lock; what this produces is the exact folder to copy and the checklist to work
  through afterwards.

  BetterModel 3.3.0 loads models from plugins/BetterModel/models (and rigs that
  animate a player, which this script does not stage, from
  plugins/BetterModel/players). Its documentation states the folders and nothing
  about subdirectories, so the staged models/ folder is FLAT: one .bbmodel per
  rig, nothing else in it, so that copying it over the plugin folder is a merge
  with no stowaways.

  Every rig named is either staged or reported by name. There is no silent skip,
  no partial stage, and no stale stage: the run builds into a sibling temporary
  folder and promotes it only once every write has succeeded, and ANY failure
  first invalidates whatever a previous run left behind - a rejected folder the
  owner could still copy is the worst outcome this script has.

  The id checks (stem vs `name` vs `model_identifier`) exist because BetterModel
  does not document how a model id is derived from the file. Requiring the three
  to agree makes the question moot - under agreement every candidate rule gives
  the same id.

.EXAMPLE
  pwsh -File deploy-rigs.ps1 -Rig wept,glassjackal -SourceRoot .\mobs-src

.EXAMPLE
  pwsh -File deploy-rigs.ps1 -Rig wept -Json
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    # Required unless -Preflight.
    [string[]]$Rig,

    # Answer one question about an existing stage - is it safe to copy? - and
    # write nothing. Exit 0 means deployable.
    [switch]$Preflight,

    # The authoring tree. Scanned recursively for <rig>.bbmodel.
    [string]$SourceRoot,

    # Where the BetterModel-shaped folder is written. Never a live server.
    [string]$StageDir,

    # Emit the machine-readable result instead of the human report.
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

# --- the shape BetterModel 3.3.0 expects, and our authoring conventions -----
$MODELS_SUBDIR        = 'models'          # plugins/BetterModel/models
$VERIFY_FILENAME      = 'VERIFY.md'       # written OUTSIDE models/
$READY_FILENAME       = 'STAGE-READY'     # written LAST, and only by a verified success
$INVALID_FILENAME     = 'STAGE-INVALID'   # written FIRST; its presence vetoes the stage
$TEMP_STAGE_NAME      = '.deploy-rigs-tmp'
$BBMODEL_EXT          = '.bbmodel'
$ROOT_BONE_NAME       = 'root'
$ROOT_YAW_DEGREES     = 180               # the facing fix: authored +Z, Minecraft wants -Z
$ANGLE_TOLERANCE      = 1e-6
$SPAWN_COMMAND        = '/bettermodel spawn'
$LOCK_SCRIPT          = 'lc-deploy-lock.ps1'

# Blockbench embeds a rig's texture as a base64 PNG data URI. Anything else is
# either a path that only resolves on the author's machine or not an image at
# all - both stage happily and ship blank, which no later check would catch.
$TEXTURE_DATA_PREFIX  = 'data:image/png;base64,'
$PNG_SIGNATURE        = [byte[]]@(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)

# A destination is refused if it sits under either of these. The plugin folder
# is the direct hazard; the server marker catches the rest of a live box.
$PLUGIN_DIR_SEGMENT   = 'plugins'
$MODEL_PLUGIN_SEGMENT = 'BetterModel'
$SERVER_ROOT_MARKER   = 'server.properties'

# Rigs whose in-game facing a human has actually seen. Everything else carries
# the 180-degree root yaw but has never been looked at, which is the whole point
# of the list this script writes.
$FACING_VERIFIED_RIGS = @('bone_colossus')

$root = $PSScriptRoot
if (-not $SourceRoot) { $SourceRoot = Join-Path $root 'mobs-src' }
if (-not $StageDir)   { $StageDir   = Join-Path $root 'dist\rigs' }

# `powershell -File deploy-rigs.ps1 -Rig wept,glassjackal` hands this parameter
# ONE string, "wept,glassjackal" - -File never splits an array argument. Split
# before anything else so every failure path below can name every requested rig.
$Rig = @($Rig | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

$stageFull  = [System.IO.Path]::GetFullPath($StageDir)
$modelsDir  = Join-Path $stageFull $MODELS_SUBDIR
$verifyPath = Join-Path $stageFull $VERIFY_FILENAME
$readyPath  = Join-Path $stageFull $READY_FILENAME
$invalidPath = Join-Path $stageFull $INVALID_FILENAME
$tempDir    = Join-Path $stageFull $TEMP_STAGE_NAME

$failures   = New-Object System.Collections.ArrayList
$candidates = New-Object System.Collections.ArrayList

function Add-Failure {
    param([string]$RigName, [string]$Reason)
    $null = $failures.Add([ordered]@{ rig = $RigName; reason = $Reason })
}

# A precondition failure is nobody's rig in particular, so it is reported as
# every rig - the caller asked about all of them and none of them happened.
function Add-GlobalFailure {
    param([string]$Reason)
    foreach ($r in $Rig) { Add-Failure $r $Reason }
}

# -----------------------------------------------------------------------------
# A CALLER'S PATH IS DATA, NEVER A PATTERN.
#
# `Test-Path -Path` treats [ ] as a wildcard, so a directory legally named
# "[handoff]" reports as ABSENT and every guard reading it waves the destination
# through. Every filesystem call below that touches a caller-supplied path uses
# -LiteralPath, or a .NET API where the cmdlet has no literal form. Adding a
# non-literal call here re-opens the hole silently, so don't.
# -----------------------------------------------------------------------------
function Test-PathLiteral {
    param([string]$Path, [string]$Type = 'Any')
    if (-not $Path) { return $false }
    return (Test-Path -LiteralPath $Path -PathType $Type)
}

# A junction or symlink makes a path's spelling say nothing about where it lands,
# which defeats every check in this script that reads a path rather than a disk.
# Both guards below refuse a reparse point outright instead of resolving and
# following it: refusing costs a caller one unusual layout, following costs a
# server its models folder. Unreadable counts as suspect.
function Test-Reparse {
    param([string]$Path)
    if (-not (Test-PathLiteral $Path)) { return $false }
    try { return (Get-Item -LiteralPath $Path -Force).Attributes.HasFlag([System.IO.FileAttributes]::ReparsePoint) }
    catch { return $true }
}

# A DRIVE ALIAS HIDES EVERYTHING A PATH-BASED GUARD CAN READ.
#
# `subst R: <server>\plugins\BetterModel` gives a destination that spells no
# plugin segments, carries no reparse attribute, and has no parent above the
# mapping - all three guards below see a clean local path. DriveInfo and
# Win32_LogicalDisk both report such a drive as an ordinary fixed disk;
# QueryDosDevice is what actually tells them apart:
#
#   a real volume   ->  \Device\HarddiskVolume3
#   a SUBST         ->  \??\C:\some\path
#   a network drive ->  a redirector device
#
# Anything that is not a plain volume is REFUSED rather than resolved, on both
# the write path and the preflight. Resolving and re-checking was the other
# option; refusing wins because the alias can be re-pointed after the check
# either way - the same argument that already refuses reparse points. A check
# that cannot run is also a refusal: a destination whose nature cannot be
# established is not one to write into.
$script:DosDeviceReady = $null
function Get-DriveAliasProblem {
    param([string]$Path)

    $root = [System.IO.Path]::GetPathRoot($Path)
    if (-not $root) { return "cannot determine the drive root of $Path" }
    if ($root.StartsWith('\\')) {
        return "destination is on a network path ($root) - this script stages onto a local volume only"
    }

    if ($null -eq $script:DosDeviceReady) {
        try {
            # The guard matters because this script can be invoked more than once
            # in a process (its own test suite does); re-adding a live type throws.
            if (-not ('LcNative.Dos' -as [type])) {
                Add-Type -Namespace LcNative -Name Dos -ErrorAction Stop -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
public static extern uint QueryDosDevice(string lpDeviceName, System.Text.StringBuilder lpTargetPath, uint ucchMax);
'@
            }
            $script:DosDeviceReady = $true
        }
        catch { $script:DosDeviceReady = $false }
    }
    if (-not $script:DosDeviceReady) {
        return "cannot establish what drive $root really is (the device query is unavailable here) - refusing rather than guessing"
    }

    $letter = $root.TrimEnd('\', '/')
    $buffer = New-Object System.Text.StringBuilder 1024
    $len = [LcNative.Dos]::QueryDosDevice($letter, $buffer, 1024)
    if ($len -eq 0) { return "cannot establish what drive $letter really is - refusing rather than guessing" }

    $device = $buffer.ToString()
    if ($device.StartsWith('\??\')) {
        return "destination is on a SUBSTituted drive ($letter maps to $($device.Substring(4))) - the alias hides where writes land and can be re-pointed after this check; stage onto the real path instead"
    }
    # ANCHORED, not a prefix. A letter can be mapped straight at
    # \Device\HarddiskVolume3\some\path, which begins with a real volume and is
    # not one: everything after the volume id is a hidden destination.
    if ($device -notmatch '^\\Device\\HarddiskVolume\d+$') {
        return "destination drive $letter is not a plain local volume (it maps to $device) - this script stages onto a local volume only"
    }
    return $null
}

# THE one ancestor walk. Both the write guard and the preflight call it, because
# a rule enforced in two places is a rule that will disagree with itself: the
# leaf can be an ordinary directory while a parent is the junction, and then one
# side validates a folder the other never writes to. Returns the offending path,
# or $null.
function Get-ReparseAncestor {
    param([string]$Path)
    $walk = $Path
    while ($walk) {
        if (Test-Reparse $walk) { return $walk }
        $parent = [System.IO.Path]::GetDirectoryName($walk)
        if (-not $parent -or $parent -eq $walk) { break }
        $walk = $parent
    }
    return $null
}

# A stage is deployable only if it can PROVE it: the tombstone absent, the
# marker present and parseable, and models/ matching that marker name for name
# and hash for hash. Presence of a file is never the answer on its own - a
# marker can survive a cleanup that removed everything it describes.
function Get-StageProblems {
    $problems = New-Object System.Collections.ArrayList

    $aliased = Get-DriveAliasProblem $stageFull
    if ($aliased) {
        $null = $problems.Add("$aliased - so what this checks and what a copy would read are not provably the same folder")
        return $problems
    }
    $linked = Get-ReparseAncestor $stageFull
    if ($linked) {
        $null = $problems.Add("the stage is reached through a reparse point ($linked) - what this checks and what a copy would read are not provably the same folder, and the link can be re-pointed in between")
        return $problems
    }
    if (Test-PathLiteral $invalidPath) {
        $null = $problems.Add("$INVALID_FILENAME is present - the last run refused or could not finish, and this stage is not deployable")
    }
    if ((Test-Reparse $readyPath) -or -not (Test-PathLiteral $readyPath 'Leaf')) {
        $null = $problems.Add("$READY_FILENAME is missing or is not a plain file - nothing here was ever completely staged")
        return $problems
    }

    $expected = @{}
    foreach ($line in [System.IO.File]::ReadAllLines($readyPath)) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        $parts = $t -split '\s+', 2
        if ($parts.Count -eq 2) { $expected[$parts[1].Trim()] = $parts[0].Trim().ToLower() }
    }
    if ($expected.Count -eq 0) {
        $null = $problems.Add("$READY_FILENAME lists nothing")
        return $problems
    }
    if (-not $expected.ContainsKey($VERIFY_FILENAME)) {
        $null = $problems.Add("$READY_FILENAME does not list $VERIFY_FILENAME - it was written by an older stager and cannot vouch for the runbook")
    }
    # Root-relative names, not basenames. `models/alpha.bbmodel` moved to
    # `models/nested/alpha.bbmodel` keeps its name and its hash while no longer
    # being where BetterModel reads, so the KEY has to carry the location.
    $present = @{}
    if (Test-Reparse $verifyPath) {
        $null = $problems.Add("$VERIFY_FILENAME is a reparse point, not a plain file")
    }
    elseif (Test-PathLiteral $verifyPath 'Leaf') {
        $present[$VERIFY_FILENAME] = (Get-FileHash -Algorithm SHA1 -LiteralPath $verifyPath).Hash.ToLower()
    }

    if (Test-Reparse $modelsDir) {
        $null = $problems.Add("$MODELS_SUBDIR/ is a reparse point - its contents live somewhere else and can be re-pointed between this check and the copy")
    }
    elseif (-not (Test-PathLiteral $modelsDir 'Container')) {
        $null = $problems.Add("$MODELS_SUBDIR/ is missing or is not a directory, but $READY_FILENAME lists $($expected.Count) entr(ies)")
    }
    else {
        # One level deep, deliberately. BetterModel loads .bbmodel flat out of
        # its models folder, so a subdirectory here - even an empty one - is not
        # part of a stage, and a recursive walk would flatten it back into a
        # match. Anything that is not a plain file is rejected outright rather
        # than followed, which also covers a link pointing outside the stage.
        foreach ($e in @(Get-ChildItem -LiteralPath $modelsDir -Force -ErrorAction SilentlyContinue)) {
            if ($e.PSIsContainer -or $e.Attributes.HasFlag([System.IO.FileAttributes]::ReparsePoint)) {
                $null = $problems.Add("$MODELS_SUBDIR/$($e.Name) is not a plain file - the staged folder is flat, one $BBMODEL_EXT per rig and nothing else")
                continue
            }
            $present["$MODELS_SUBDIR/$($e.Name)"] = (Get-FileHash -Algorithm SHA1 -LiteralPath $e.FullName).Hash.ToLower()
        }
    }

    foreach ($name in $expected.Keys) {
        if (-not $present.ContainsKey($name)) {
            $null = $problems.Add("$name is listed in $READY_FILENAME but is not in the stage")
        }
        elseif ($present[$name] -ne $expected[$name]) {
            $null = $problems.Add("$name does not match $READY_FILENAME - on disk $($present[$name]), marker says $($expected[$name])")
        }
    }
    foreach ($name in $present.Keys) {
        if (-not $expected.ContainsKey($name)) {
            $null = $problems.Add("$name is in the stage but not listed in $READY_FILENAME - it is not part of it")
        }
    }
    return $problems
}

# Written BEFORE any cleanup or promotion, so a stage stops being deployable at
# the first moment it stops being whole - including when the marker itself turns
# out to be undeletable, which is the one case marker-removal alone cannot cover.
function Set-StageInvalid {
    param([string]$Why)
    # Nothing to invalidate if the caller's directory does not exist yet.
    if (-not (Test-PathLiteral $stageFull)) { return }
    try {
        [System.IO.File]::WriteAllText($invalidPath,
            "# $INVALID_FILENAME - this stage is NOT deployable.`r`n# $Why`r`n# Re-run deploy-rigs.ps1; this file is removed only by a run that verifies its own output.`r`n",
            (New-Object System.Text.UTF8Encoding($false)))
    }
    catch {
        Add-GlobalFailure "could not write $INVALID_FILENAME to $stageFull ($($_.Exception.Message.Split([char]10)[0])) - treat this stage as unusable and delete it by hand"
    }
}

function Test-Angle {
    param($Value, [double]$Expected)
    if ($null -eq $Value) { return $false }
    try { $d = [double]$Value } catch { return $false }
    return ([math]::Abs($d - $Expected) -le $ANGLE_TOLERANCE)
}

# Everything this script owns inside the stage directory, and nothing else. The
# stage directory itself is the caller's and is never removed.
#
# Deletion can fail - another process holding a handle beats us and there is no
# fix for that here. What must never fail is SAYING SO: the marker is dropped
# first, so a folder we could not clear is already un-deployable, and every path
# is re-checked for absence afterwards. A survivor becomes a named failure
# rather than a silently-swallowed error, because a stale rig somebody can still
# copy is the worst outcome this script has.
function Remove-OwnedStage {
    $surviving = New-Object System.Collections.ArrayList
    # NOT $invalidPath: the tombstone is what a refusal deliberately leaves behind.
    foreach ($p in @($readyPath, $verifyPath, $modelsDir, $tempDir)) {
        if (-not (Test-PathLiteral $p)) { continue }
        $err = $null
        try { Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction Stop }
        catch { $err = $_.Exception.Message.Split([char]10)[0] }
        if (Test-PathLiteral $p) {
            if (-not $err) { $err = 'still present after removal reported no error' }
            $null = $surviving.Add([ordered]@{ path = $p; error = $err })
        }
    }
    return $surviving
}

# Every refusal path goes through here, so no failure exit can forget it. The
# tombstone goes down FIRST and stays: cleanup may fail, and the claim "the
# marker is gone" is never made without having looked.
function Invoke-Refusal {
    param([string]$Why = 'the staging run was refused')
    Set-StageInvalid $Why
    foreach ($s in (Remove-OwnedStage)) {
        Add-GlobalFailure "stale stage NOT removed: $($s.path) - $($s.error). DO NOT COPY this folder; $INVALID_FILENAME is in place so the preflight will refuse it, but the files are still on disk."
    }
    Write-Refusal
    exit 1
}

function Write-Refusal {
    if ($Json) {
        Write-Output ([ordered]@{
                staged     = @()
                failures   = @($failures)
                stageDir   = $stageFull
                modelsDir  = $modelsDir
                verifyList = $verifyPath
            } | ConvertTo-Json -Depth 8)
    }
    else {
        Write-Host ''
        Write-Host "REFUSED - nothing was staged." -ForegroundColor Red
        foreach ($f in $failures) { Write-Host "  $($f.rig): $($f.reason)" -ForegroundColor Red }
        Write-Host ''
    }
}

# --- 0. -Preflight: answer, write nothing --------------------------------
#
# Deliberately ahead of the destination guard: this branch only reads, so it is
# useful pointed at a real installation as well as at a stage.

if ($Preflight) {
    # @(): a returned collection of ONE unrolls to a bare string, and indexing a
    # string gives a character rather than the problem.
    $problems = @(Get-StageProblems)
    if ($problems.Count -eq 0) {
        Write-Host "DEPLOYABLE: $stageFull"
        Write-Host "  $READY_FILENAME matches every file in $MODELS_SUBDIR/ and no $INVALID_FILENAME is present."
        exit 0
    }
    Write-Host ''
    Write-Host "NOT DEPLOYABLE: $stageFull" -ForegroundColor Red
    foreach ($p in $problems) { Write-Host "  $p" -ForegroundColor Red }
    Write-Host '  Copy nothing. Re-run deploy-rigs.ps1 and read what it says.'
    Write-Host ''
    exit 1
}

if ($Rig.Count -eq 0) {
    # No tombstone here: nothing was attempted, so an existing good stage in this
    # directory is still exactly as good as it was.
    Add-Failure '(none)' "no rigs named - pass -Rig <name>[,<name>...], or -Preflight to check an existing stage"
    Write-Refusal
    exit 1
}

# --- 1. the destination guard, before anything is read, written or deleted ---
#
# Pointing -StageDir at a live plugins/BetterModel folder would make this script
# wipe and rewrite a running server's models outside the deploy lock. Refuse
# first, so a mistyped path costs an error message rather than the box.

$forbidden = Get-DriveAliasProblem $stageFull

$segments = @($stageFull -split '[\\/]' | Where-Object { $_ })
for ($i = 1; $i -lt $segments.Count -and -not $forbidden; $i++) {
    if ($segments[$i] -ieq $MODEL_PLUGIN_SEGMENT -and $segments[$i - 1] -ieq $PLUGIN_DIR_SEGMENT) {
        $forbidden = "destination is inside a $PLUGIN_DIR_SEGMENT/$MODEL_PLUGIN_SEGMENT folder ($stageFull) - this script stages only; the copy into a running server is the owner's step under the deploy lock"
        break
    }
}
if (-not $forbidden) {
    # This is what stops the two rules above from being merely LEXICAL: a
    # junction named anything at all can land inside a live plugin folder, and
    # its visible path would pass both of them. Same helper the preflight uses.
    $linked = Get-ReparseAncestor $stageFull
    if ($linked) {
        $forbidden = "destination is reached through a reparse point ($linked) - a junction or symlink hides where writes actually land, and this script will not delete or write through one"
    }
}
if (-not $forbidden) {
    $walk = $stageFull
    while ($walk) {
        if (Test-PathLiteral (Join-Path $walk $SERVER_ROOT_MARKER)) {
            $forbidden = "destination is under a live server root ($walk holds $SERVER_ROOT_MARKER) - this script stages only; the copy into a running server is the owner's step under the deploy lock"
            break
        }
        $parent = [System.IO.Path]::GetDirectoryName($walk)
        if (-not $parent -or $parent -eq $walk) { break }
        $walk = $parent
    }
}
if (-not $forbidden) {
    # The paths this run would itself remove or overwrite, for the same reason.
    foreach ($owned in @($modelsDir, $verifyPath, $readyPath, $tempDir)) {
        if (Test-Reparse $owned) {
            $forbidden = "$owned is a reparse point - this run would delete or overwrite through it, and what it points at is not this stage"
            break
        }
    }
}
if ($forbidden) {
    Add-GlobalFailure $forbidden
    Write-Refusal
    exit 1
}

# --- 2. the source tree ------------------------------------------------------

$allModels = @()
try {
    if (-not (Test-PathLiteral $SourceRoot)) { throw "source root not found: $SourceRoot" }
    if (-not (Test-PathLiteral $SourceRoot 'Container')) { throw "source root is not a directory: $SourceRoot" }
    $allModels = @(Get-ChildItem -LiteralPath $SourceRoot -Recurse -File -Filter "*$BBMODEL_EXT" -ErrorAction Stop)
}
catch {
    Add-GlobalFailure "cannot scan the source tree: $($_.Exception.Message.Split([char]10)[0])"
    Invoke-Refusal
}

# --- 3. validate every rig; nothing is written until all of them pass --------

foreach ($name in $Rig) {
    $matched = @($allModels | Where-Object { [System.IO.Path]::GetFileNameWithoutExtension($_.Name) -eq $name })

    if ($matched.Count -eq 0) {
        Add-Failure $name "no $name$BBMODEL_EXT anywhere under $SourceRoot"
        continue
    }
    if ($matched.Count -gt 1) {
        Add-Failure $name "ambiguous: $($matched.Count) files match - $(($matched | ForEach-Object { $_.FullName }) -join ' | ')"
        continue
    }

    $file = $matched[0]

    try {
        $model = [System.IO.File]::ReadAllText($file.FullName) | ConvertFrom-Json
    }
    catch {
        Add-Failure $name "not parseable as JSON ($($file.FullName)): $($_.Exception.Message.Split([char]10)[0])"
        continue
    }

    # id agreement - stem, `name`, and any non-empty `model_identifier`
    if ($model.name -ne $name) {
        Add-Failure $name "internal name '$($model.name)' does not match the filename stem '$name' ($($file.FullName))"
        continue
    }
    $ident = $model.model_identifier
    if ($ident -and $ident -ne $name) {
        Add-Failure $name "model_identifier '$ident' does not match the filename stem '$name' ($($file.FullName))"
        continue
    }

    # the facing fix: ONE top-level bone, named root, at the origin, yawed 180
    $tops = @($model.outliner | Where-Object { $_ -is [psobject] -and $null -ne $_.name })
    if ($tops.Count -ne 1 -or $tops[0].name -ne $ROOT_BONE_NAME) {
        Add-Failure $name "expected exactly one top-level '$ROOT_BONE_NAME' bone, found $($tops.Count): $(($tops | ForEach-Object { $_.name }) -join ', ')"
        continue
    }
    $rot = @($tops[0].rotation)
    $org = @($tops[0].origin)
    $yawOk = $rot.Count -eq 3 -and (Test-Angle $rot[0] 0) -and (Test-Angle $rot[2] 0) -and
             ((Test-Angle $rot[1] $ROOT_YAW_DEGREES) -or (Test-Angle $rot[1] (-$ROOT_YAW_DEGREES)))
    $orgOk = $org.Count -eq 3 -and (Test-Angle $org[0] 0) -and (Test-Angle $org[1] 0) -and (Test-Angle $org[2] 0)
    if (-not ($yawOk -and $orgOk)) {
        Add-Failure $name "root bone is not the origin-anchored $ROOT_YAW_DEGREES-degree yaw: rotation [$($rot -join ', ')] origin [$($org -join ', ')]"
        continue
    }

    # A mob rig renders from the texture EMBEDDED in the .bbmodel. Each stage
    # here rejects a different lie the previous one lets through: a workstation
    # path is not a payload, a payload that decodes is not necessarily bytes,
    # and bytes are not necessarily an image.
    $textureProblem = $null
    $embedded = 0
    foreach ($t in @($model.textures)) {
        $src = [string]$t.source
        if (-not $src) { continue }
        if ($src -notlike "$TEXTURE_DATA_PREFIX*") {
            $textureProblem = "texture '$($t.name)' is not an embedded PNG - its source starts '$($src.Substring(0, [math]::Min(40, $src.Length)))' rather than '$TEXTURE_DATA_PREFIX'"
            break
        }
        $payload = $src.Substring($TEXTURE_DATA_PREFIX.Length)
        $bytes = $null
        try { $bytes = [System.Convert]::FromBase64String($payload) }
        catch {
            $textureProblem = "texture '$($t.name)' carries a data: URI whose base64 payload does not decode"
            break
        }
        if ($bytes.Length -lt $PNG_SIGNATURE.Length) {
            $textureProblem = "texture '$($t.name)' decodes to $($bytes.Length) byte(s) - too short to be a PNG"
            break
        }
        $signed = $true
        for ($b = 0; $b -lt $PNG_SIGNATURE.Length; $b++) {
            if ($bytes[$b] -ne $PNG_SIGNATURE[$b]) { $signed = $false; break }
        }
        if (-not $signed) {
            $textureProblem = "texture '$($t.name)' decodes to $($bytes.Length) byte(s) that are not a PNG - the file has no PNG signature"
            break
        }
        $embedded++
    }
    if ($textureProblem) { Add-Failure $name $textureProblem; continue }
    if ($embedded -eq 0) {
        Add-Failure $name "no embedded texture - BetterModel generates its pack assets from the .bbmodel's own texture"
        continue
    }

    $elements = @($model.elements)
    if ($elements.Count -eq 0) {
        Add-Failure $name "no elements - the rig has no geometry"
        continue
    }

    $clips = @($model.animations | ForEach-Object { $_.name })
    $facing = if ($FACING_VERIFIED_RIGS -contains $name) { 'VERIFIED' } else { 'UNPROVEN' }

    $null = $candidates.Add([ordered]@{
            rig        = $name
            source     = $file.FullName
            sha1       = (Get-FileHash -Algorithm SHA1 -LiteralPath $file.FullName).Hash.ToLower()
            bytes      = $file.Length
            elements   = $elements.Count
            animations = $clips
            facing     = $facing
        })
}

if ($failures.Count -gt 0) {
    # A rejected run must not leave a folder the owner could still copy.
    Invoke-Refusal
}

# --- 4. build into a temp folder, then promote ------------------------------

function Get-VerifyList {
    $lines = New-Object System.Collections.ArrayList
    function Emit { param([string]$Line) $null = $lines.Add($Line) }

    Emit '# Rig staging - verification list'
    Emit ''
    Emit "Staged $($candidates.Count) rig(s) from ``$SourceRoot`` into ``$modelsDir``."
    Emit ''
    Emit '## Deploy (owner, at the box)'
    Emit ''
    Emit 'mc-dev is shared. Hold the deploy lock across the WHOLE window - two restarts'
    Emit 'need the box to sit still - and release it on every exit, including a failed'
    Emit 'check. Readings taken without `baseline` and `verify` around them cannot be'
    Emit 'attributed to the build that produced them, and an unattributable reading is'
    Emit 'not evidence.'
    Emit ''
    Emit "1. ``$LOCK_SCRIPT check``, then ``$LOCK_SCRIPT acquire -Owner <you> -Reason `"MM-P3 rig load`"``."
    Emit '2. PREFLIGHT. Run it; do not eyeball the folder:'
    Emit ''
    Emit '   ```'
    Emit "   powershell -NoProfile -File deploy-rigs.ps1 -Preflight -StageDir `"$stageFull`""
    Emit '   ```'
    Emit ''
    Emit '   COPY NOTHING unless it exits 0. It proves three things a glance cannot: that'
    Emit "   ``$INVALID_FILENAME`` is absent, that ``$READY_FILENAME`` is present, and that every file"
    Emit "   in ``$MODELS_SUBDIR`` - AND this file - matches the marker path for path and hash for"
    Emit '   hash. A marker on its own proves none of that: a refused run can leave one behind'
    Emit '   when the file cannot be deleted, a rig moved into a subfolder is no longer where'
    Emit "   BetterModel reads, and a stage that lost THIS file would deploy with no lock"
    Emit '   discipline and no facing checklist at all.'
    Emit "3. Copy every file in ``$modelsDir`` into ``plugins/BetterModel/models``."
    Emit '4. Restart. BetterModel regenerates its `build.zip` at boot.'
    Emit '5. `build.ps1`, then `tools/merge_dev_pack.py`, upload, pin the printed sha1 in'
    Emit '   `server.properties`, restart again.'
    Emit "6. ``$LOCK_SCRIPT baseline -Owner <you>`` - AFTER that final restart. It pins the"
    Emit '   build every reading below describes; `acquire` snapshotted the PREVIOUS one.'
    Emit '7. Work through the per-rig checks below.'
    Emit "8. ``$LOCK_SCRIPT verify`` - proves nobody swapped the build mid-window. A drift"
    Emit '   result invalidates every reading above; re-run them, do not reason from them.'
    Emit "9. ``$LOCK_SCRIPT release -Owner <you>``."
    Emit ''
    Emit '## Staged rigs'
    Emit ''
    Emit '| rig | sha1 | bytes | elements | clips | facing |'
    Emit '|---|---|---|---|---|---|'
    foreach ($c in $candidates) {
        Emit "| $($c.rig) | ``$($c.sha1)`` | $($c.bytes) | $($c.elements) | $($c.animations.Count) | $($c.facing) |"
    }
    Emit ''
    Emit '## Per-rig checks'
    Emit ''
    Emit 'For each rig: (a) the boot log carries no BetterModel error naming it,'
    Emit "(b) ``$SPAWN_COMMAND <rig>`` renders geometry rather than nothing, and (c) FACING -"
    Emit 'the rig''s front points where it looks. Facing is the one nobody has confirmed:'
    Emit 'every rig is authored facing +Z and carries a 180-degree yaw on its `root` bone'
    Emit 'to meet Minecraft''s -Z, and that fix has only ever been seen working on'
    Emit "$($FACING_VERIFIED_RIGS -join ', '). A rig marked UNPROVEN below is one where a"
    Emit 'back-to-front result is a live possibility, not a formality.'
    Emit ''
    foreach ($c in $candidates) {
        $clipList = ($c.animations | ForEach-Object { '`' + $_ + '`' }) -join ', '
        Emit "### $($c.rig)  -  facing $($c.facing)"
        Emit ''
        Emit '- [ ] no BetterModel error naming it in the boot log'
        Emit "- [ ] ``$SPAWN_COMMAND $($c.rig)`` renders the rig"
        Emit "- [ ] facing: front points forward (status: $($c.facing))"
        Emit "- clips in the file: $clipList"
        Emit ''
    }
    Emit 'Clip playback is not checked here - chaining a held `<x>_windup` into its payoff'
    Emit 'is MM-P4''s question. The clip list above is what the file carries, so a rig that'
    Emit 'loads with clips missing is visible by comparison.'

    return (($lines -join "`r`n") + "`r`n")
}

try {
    # Down before anything is created or removed. From here until this run has
    # verified its own output, this stage answers "not deployable" - and it does
    # so through a file whose ABSENCE has to be earned, rather than through a
    # marker whose removal might quietly fail.
    # The directory has to exist before it can hold a tombstone, and a fresh
    # stage must be tombstoned while it is being built exactly like a re-stage.
    # .NET rather than New-Item/Copy-Item/Move-Item throughout this block: those
    # cmdlets have no -LiteralPath for the path they CREATE, so a bracketed
    # stage path would be a pattern again (see the note above Test-PathLiteral).
    $null = [System.IO.Directory]::CreateDirectory($stageFull)
    Set-StageInvalid 'a staging run started here and has not finished'

    if (Test-PathLiteral $tempDir) { Remove-Item -LiteralPath $tempDir -Recurse -Force }
    $tempModels = Join-Path $tempDir $MODELS_SUBDIR
    $null = [System.IO.Directory]::CreateDirectory($tempModels)

    foreach ($c in $candidates) {
        [System.IO.File]::Copy($c.source, (Join-Path $tempModels "$($c.rig)$BBMODEL_EXT"), $true)
    }
    $tempVerify = Join-Path $tempDir $VERIFY_FILENAME
    [System.IO.File]::WriteAllText($tempVerify, (Get-VerifyList), (New-Object System.Text.UTF8Encoding($false)))

    # The manifest covers the WHOLE stage, by root-relative path: the rigs and
    # the runbook. VERIFY.md carries the lock discipline and the per-rig facing
    # checklist, so a stage that lost it is not a stage anyone should copy from.
    $readyList = (@("# $READY_FILENAME - written last, once every file below is in place.",
            "# Its absence means the stage is NOT deployable, and so does the presence of",
            "# $INVALID_FILENAME. One line per file, path relative to this folder:",
            "#   <sha1>  <path>") +
        @($candidates | ForEach-Object { "$($_.sha1)  $MODELS_SUBDIR/$($_.rig)$BBMODEL_EXT" }) +
        @("$((Get-FileHash -Algorithm SHA1 -LiteralPath $tempVerify).Hash.ToLower())  $VERIFY_FILENAME")) -join "`r`n"

    # Everything is written. The marker goes first so the stage stops being
    # deployable the moment it stops being whole; then the old outputs go and the
    # new ones arrive as two moves rather than a file at a time.
    if (Test-PathLiteral $readyPath)  { Remove-Item -LiteralPath $readyPath -Force }
    if (Test-PathLiteral $modelsDir)  { Remove-Item -LiteralPath $modelsDir -Recurse -Force }
    if (Test-PathLiteral $verifyPath) { Remove-Item -LiteralPath $verifyPath -Recurse -Force }
    [System.IO.Directory]::Move($tempModels, $modelsDir)
    [System.IO.File]::Move($tempVerify, $verifyPath)
    Remove-Item -LiteralPath $tempDir -Recurse -Force

    [System.IO.File]::WriteAllText($readyPath, $readyList + "`r`n", (New-Object System.Text.UTF8Encoding($false)))
}
catch {
    Add-GlobalFailure "staging failed while writing: $($_.Exception.Message.Split([char]10)[0])"
    Invoke-Refusal 'a staging run failed part-way through writing this stage'
}

# The run now checks its OWN output the same way the owner's preflight will, and
# only a clean answer lifts the tombstone. This is the last write of the run and
# nothing above may be reordered below it.
$selfCheck = @(Get-StageProblems)
if ($selfCheck.Count -gt 1 -or ($selfCheck.Count -eq 1 -and $selfCheck[0] -notlike "$INVALID_FILENAME is present*")) {
    foreach ($p in $selfCheck) { Add-GlobalFailure "the staged folder does not match what was written: $p" }
    Invoke-Refusal 'a staging run finished but could not verify its own output'
}
try { if (Test-PathLiteral $invalidPath) { Remove-Item -LiteralPath $invalidPath -Force -ErrorAction Stop } }
catch {
    Add-GlobalFailure "staging succeeded but $INVALID_FILENAME could not be removed ($($_.Exception.Message.Split([char]10)[0])) - the preflight will keep refusing this stage until it is gone"
    Write-Refusal
    exit 1
}

# --- 5. report --------------------------------------------------------------

if ($Json) {
    Write-Output ([ordered]@{
            staged     = @($candidates)
            failures   = @()
            stageDir   = $stageFull
            modelsDir  = $modelsDir
            verifyList = $verifyPath
        } | ConvertTo-Json -Depth 8)
}
else {
    Write-Host ''
    Write-Host "Staged $($candidates.Count) rig(s) into $modelsDir"
    foreach ($c in $candidates) {
        Write-Host ("  {0,-20} {1}  {2} clip(s)  facing {3}" -f $c.rig, $c.sha1, $c.animations.Count, $c.facing)
    }
    Write-Host ''
    Write-Host "Verification list: $verifyPath"
    Write-Host "Ready marker     : $readyPath"
    Write-Host 'STAGE ONLY - the copy into plugins/BetterModel/models is the owner''s step,'
    Write-Host 'taken under the deploy lock.'
    Write-Host ''
}

exit 0
