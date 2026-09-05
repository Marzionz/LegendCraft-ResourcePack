#Requires -Version 5.1
<#
.SYNOPSIS
  Removes BetterHud's generated text shader templates so the plugin writes fresh ones on its
  next boot.

.DESCRIPTION
  BetterHud writes plugins/BetterHud/shaders/text.vsh and text.fsh once, on the first boot
  after install, and never overwrites them again -- not on a plugin upgrade, not on a rebuild
  of the box. Those two files override the vanilla GLOBAL text shaders, so a stale pair does
  not fail in a way that points at the HUD: every piece of text the client draws goes dim,
  chat and menus included, and the natural reading is a client or a video-driver problem.

  Removing them before the restart is what makes the plugin regenerate them, which is why the
  deploy runs this ahead of step 3 rather than after it.

  Only the two named files are touched. BetterHud's other generated shaders are its own, and
  a deploy that decided which of them to keep would be guessing.

      powershell -NoProfile -File tools\clear-hud-shaders.ps1 -BetterHudRoot <plugins\BetterHud>

  Tested by tests\run-hud-shader-clear-tests.ps1.
#>

param(
    [Parameter(Mandatory = $true)][string]$BetterHudRoot
)

$ErrorActionPreference = 'Stop'

# The vanilla text shaders BetterHud overrides. Not a wildcard: a pattern over shaders/ would
# take whatever else the plugin generates there.
$TextShaderTemplates = @('text.vsh', 'text.fsh')

# -LiteralPath throughout: Test-Path -Path reads square brackets as a wildcard, so a server
# folder legally named with them answers False and a guard inspecting it waves the path
# through. A caller's path is data, never a pattern.
$shaders = Join-Path $BetterHudRoot 'shaders'
if (-not (Test-Path -LiteralPath $shaders)) {
    Write-Host "  BetterHud shaders/: none at '$shaders' -- nothing to clear (fresh install)."
    exit 0
}

foreach ($name in $TextShaderTemplates) {
    $path = Join-Path $shaders $name
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Host "  already absent: $path"
        continue
    }
    $item = Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer) {
        throw "refusing to clear '$path': it is a directory, not a shader template. Removing it would take whatever is under it."
    }
    Remove-Item -LiteralPath $path -Force
    # A delete can fail without throwing when another process holds the handle. Name the
    # survivor rather than letting the deploy restart onto the template it meant to drop.
    if (Test-Path -LiteralPath $path) {
        throw "could not remove '$path' -- it is still on disk. Something holds it open; the server would boot on the stale template."
    }
    Write-Host "  removed stale template: $path"
}

exit 0
