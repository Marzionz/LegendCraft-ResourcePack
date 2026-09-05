#Requires -Version 5.1
<#
.SYNOPSIS
  Contract tests for tools/clear-hud-shaders.ps1, the deploy step that drops BetterHud's
  generated text shader templates so the plugin writes fresh ones.

.DESCRIPTION
  Builds a fake plugins/BetterHud tree in a temp directory it owns, so no arm reaches the
  real server. Nothing here starts, stops or reads mc-dev.

  WHY THE STEP EXISTS. BetterHud writes plugins/BetterHud/shaders/text.{vsh,fsh} once and
  never overwrites them again -- not on an upgrade, not on a rebuild. Those two files override
  the vanilla GLOBAL text shaders, so a stale pair does not break the HUD in a way that points
  at the HUD: every piece of text the client draws goes dim, chat and menus included, and the
  natural reading is a client or a video-driver problem. Deleting them is what makes the
  plugin regenerate them, so the deploy has to do it before the restart.

  RUN IT when clear-hud-shaders.ps1 or the deploy's wiring of it changes:

      powershell -NoProfile -File tests\run-hud-shader-clear-tests.ps1

  ---------------------------------------------------------------------------
  SECTION 16 - acceptance list, then RED, then code.

  Requirement: a HUD deploy leaves no shader template the plugin did not write this boot,
  and says what it removed. It runs on a live shared box under the deploy lock, so it has to
  be safe to run twice and it must never delete anything it was not asked to.

    AC-1  both templates present are removed, and each removal is named in the output
          rather than done silently                                       SHD-01
    AC-2  a second run over the same folder succeeds and reports each as already absent -
          the step is idempotent, because a deploy that half-failed gets re-run    SHD-02
    AC-3  another file in shaders/ survives: only the two named templates are touched,
          and BetterHud's other generated shaders are not the deploy's to delete   SHD-03
    AC-4  a DIRECTORY standing where a template belongs is refused BY NAME, and left on
          disk - a recursive delete there would take whatever is under it. The arm reads
          the refusal, because an absent subject exits non-zero and deletes nothing too    SHD-04
    AC-5  a BetterHud root with no shaders/ at all succeeds: a fresh install has not
          written them yet, and that is not a deploy failure                       SHD-05
    AC-6  deploy-hud.ps1 runs the step BEFORE it restarts the server, because the restart
          is what makes the plugin write the replacements                          WIRE-01

  FIRST RED, recorded in tests/RED-hud-shader-clear.txt: all six arms ran and all six
  failed. tools/clear-hud-shaders.ps1 did not exist, so SHD-01..SHD-05 failed on the missing
  script and WIRE-01 failed on deploy-hud.ps1 not naming it.
#>

param(
    [switch]$KeepFixture,
    [string]$ClearScriptPath,
    [string]$DeployScriptPath
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot

# The suite runs on Windows PowerShell locally and on pwsh on the Linux CI runner, and the
# subject it launches must run on whichever of the two is hosting it.
$PwshExe = (Get-Process -Id $PID).Path
if (-not $ClearScriptPath)  { $ClearScriptPath  = Join-Path $RepoRoot 'tools/clear-hud-shaders.ps1' }
if (-not $DeployScriptPath) { $DeployScriptPath = Join-Path $RepoRoot 'tools/deploy-hud.ps1' }

$script:Pass = 0
$script:Fail = 0

function Assert {
    param([string]$Id, [string]$What, [bool]$Ok)
    if ($Ok) { $script:Pass++; Write-Host ("  PASS {0}  {1}" -f $Id, $What) }
    else     { $script:Fail++; Write-Host ("  FAIL {0}  {1}" -f $Id, $What) -ForegroundColor Red }
}

# --- fixture ---------------------------------------------------------------
$Fixture = Join-Path ([System.IO.Path]::GetTempPath()) ("hudshader-" + [guid]::NewGuid().ToString('n'))
New-Item -ItemType Directory -Force -Path $Fixture | Out-Null

$Templates = @('text.vsh', 'text.fsh')

function New-BetterHudRoot {
    param([string]$Name, [switch]$NoShaders, [switch]$TemplateIsDirectory, [string[]]$Extra = @())
    $root = Join-Path $Fixture $Name
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    if ($NoShaders) { return $root }
    $shaders = Join-Path $root 'shaders'
    New-Item -ItemType Directory -Force -Path $shaders | Out-Null
    foreach ($name in $Templates) {
        $path = Join-Path $shaders $name
        if ($TemplateIsDirectory -and $name -eq 'text.vsh') {
            New-Item -ItemType Directory -Force -Path $path | Out-Null
            New-Item -ItemType File -Force -Path (Join-Path $path 'inside.txt') | Out-Null
        }
        else {
            [System.IO.File]::WriteAllText($path, "// july template`n")
        }
    }
    foreach ($name in $Extra) {
        [System.IO.File]::WriteAllText((Join-Path $shaders $name), "// not ours`n")
    }
    return $root
}

# Both of the subject's streams are captured to files rather than through the pipeline. In
# Windows PowerShell a native command's redirected stderr comes back as ErrorRecords, which
# under this suite's `Stop` preference kills the run on the first arm that expects a refusal --
# and the arms that expect one have to READ it, or "the script is not there at all" satisfies
# them exactly as well as "the script refused".
function Invoke-Clear {
    param([string]$Root)
    $stem    = Join-Path $Fixture ([guid]::NewGuid().ToString('n'))
    $outFile = "$stem.out"
    $errFile = "$stem.err"
    $proc = Start-Process -FilePath $PwshExe -NoNewWindow -Wait -PassThru `
        -ArgumentList '-NoProfile', '-File', ('"{0}"' -f $ClearScriptPath),
                      '-BetterHudRoot', ('"{0}"' -f $Root) `
        -RedirectStandardOutput $outFile -RedirectStandardError $errFile
    $text = ''
    foreach ($file in @($outFile, $errFile)) {
        if (Test-Path -LiteralPath $file) { $text += [System.IO.File]::ReadAllText($file) }
    }
    return [pscustomobject]@{ Code = $proc.ExitCode; Text = $text }
}

function Test-TemplatePath {
    param([string]$Root, [string]$Name)
    return Test-Path -LiteralPath (Join-Path (Join-Path $Root 'shaders') $Name)
}

Write-Host ""
Write-Host "SHD  the shader-template clear"

# SHD-01 -- both templates present are removed, and each removal is named.
$root = New-BetterHudRoot -Name 'both-present'
$r = Invoke-Clear -Root $root
$named = ($r.Text -match 'text\.vsh') -and ($r.Text -match 'text\.fsh')
Assert 'SHD-01' 'both templates removed, each named in the output' (
    $r.Code -eq 0 -and -not (Test-TemplatePath $root 'text.vsh') -and
    -not (Test-TemplatePath $root 'text.fsh') -and $named)

# SHD-02 -- a second run over the same folder succeeds: the step is idempotent.
$r2 = Invoke-Clear -Root $root
Assert 'SHD-02' 'a second run succeeds and reports both already absent' (
    $r2.Code -eq 0 -and ($r2.Text -match '(?i)absent'))

# SHD-03 -- another file in shaders/ survives.
$root = New-BetterHudRoot -Name 'other-shader' -Extra @('bar.fsh')
$r = Invoke-Clear -Root $root
Assert 'SHD-03' 'a shader that is not one of the two templates is left alone' (
    $r.Code -eq 0 -and (Test-Path -LiteralPath (Join-Path $root 'shaders/bar.fsh')))

# SHD-04 -- a directory where a template belongs is refused and left on disk.
$root = New-BetterHudRoot -Name 'template-is-a-dir' -TemplateIsDirectory
$r = Invoke-Clear -Root $root
# The refusal has to be READ, not just counted: a subject that is missing, or that crashed on
# something else entirely, exits non-zero and leaves the directory alone too.
Assert 'SHD-04' 'a directory standing in for a template is refused by name, and survives' (
    $r.Code -ne 0 -and ($r.Text -match '(?i)director') -and ($r.Text -match 'text\.vsh') -and
    (Test-Path -LiteralPath (Join-Path $root 'shaders/text.vsh/inside.txt')))

# SHD-05 -- no shaders/ at all is not a failure.
$root = New-BetterHudRoot -Name 'fresh-install' -NoShaders
$r = Invoke-Clear -Root $root
Assert 'SHD-05' 'a BetterHud root with no shaders/ succeeds' ($r.Code -eq 0)

Write-Host ""
Write-Host "WIRE the deploy's use of it"

# WIRE-01 -- the deploy runs the clear before the restart that regenerates the templates.
# Position, not mere presence: run after the restart and the plugin has already re-read the
# stale pair, so the deploy would have deleted nothing that mattered until the NEXT boot.
$deploy = [System.IO.File]::ReadAllText($DeployScriptPath)
$clearAt   = $deploy.IndexOf('clear-hud-shaders.ps1')
$restartAt = $deploy.IndexOf('restarting server')
Assert 'WIRE-01' 'deploy-hud.ps1 clears the templates before it restarts the server' (
    $clearAt -ge 0 -and $restartAt -ge 0 -and $clearAt -lt $restartAt)

# --- report ----------------------------------------------------------------
Write-Host ""
if ($KeepFixture) { Write-Host "fixture kept at $Fixture" }
else { Remove-Item -LiteralPath $Fixture -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host ("{0} passed, {1} failed" -f $script:Pass, $script:Fail)
if ($script:Fail -gt 0) { exit 1 }
exit 0
