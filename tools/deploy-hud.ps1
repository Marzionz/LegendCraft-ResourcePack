# Deploys the LegendCraft BetterHud stat HUD to the mc-dev server end to end.
#
# Automates the loop that is otherwise ~7 manual steps (see hud/betterhud/README.md):
#   1. regenerate art + config      (generate_hud.py)
#   2. copy into plugins/BetterHud
#   3. restart server               -> BetterHud rebuilds build.zip
#   4. merge build.zip into the newest built base pack (merge_dev_pack.py)
#   5. publish the merged pack to the rolling GitHub "dev" pre-release (publish-pack.ps1 -Dev)
#   6. point server.properties sha1 at it (URL is the stable dev-release URL; only sha1 moves)
#   7. restart server               -> pushes the new pack on join
#
# Delivery is the public GitHub Release URL (dev + prod both use it); needs `gh` authed.
#
# After it finishes: rejoin the client (accept the pack) and screenshot. Tune the knobs in
# generate_hud.py (STAT_HUD_X / STAT_HUD_Y / STAT_TEXT_SCALE, bar art) then run this again.
#
# NOTE: first run should be watched — it stops/starts the live server. RCON is off, so the
# stop is a force-kill of the process listening on 25565 (dev server; worlds autosave).
$ErrorActionPreference = "Stop"

$RP       = Split-Path -Parent $PSScriptRoot
$SERVER   = "C:\Repositories\mc-dev\server"
$BH       = "$SERVER\plugins\BetterHud"
$DIST     = "$RP\dist"
$JAVA     = "C:\Repositories\mc-dev\jdk25\jdk-25.0.3+9\bin\java.exe"
$PROPS    = "$SERVER\server.properties"

function Stop-GameServer {
    $conn = Get-NetTCPConnection -LocalPort 25565 -State Listen -ErrorAction SilentlyContinue
    if ($conn) { Stop-Process -Id $conn.OwningProcess -Force }
    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $deadline -and (Get-NetTCPConnection -LocalPort 25565 -State Listen -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 500 }
}

function Start-GameServer {
    $before = (Get-Item "$SERVER\logs\latest.log").LastWriteTimeUtc
    Start-Process -FilePath $JAVA -ArgumentList '-Xms2G','-Xmx4G','-jar',"$SERVER\paper.jar",'--nogui' -WorkingDirectory $SERVER -WindowStyle Hidden
    Write-Host "  waiting for server startup..."
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        $log = Get-Content "$SERVER\logs\latest.log" -Raw -ErrorAction SilentlyContinue
        if ($log -and $log.Contains('Done (') -and (Get-Item "$SERVER\logs\latest.log").LastWriteTimeUtc -gt $before) { return }
    }
    throw "server did not report 'Done (' within 120s"
}

Write-Host "[1/7] regenerating HUD art + config..."
& python "$RP\tools\generate_hud.py" | Out-Null

# Preflight: every asset the lc_stat HUD references MUST exist before we deploy. The skill-icon row
# (frames, the black placeholder gem, per-class art) is defined in the "hunter" image registry and
# under assets/legendcraft/{frames,indicators,skill-icons}; if any of it is missing we would ship a
# HUD with silent holes (exactly how the icon row went dark once). Fail loudly instead.
$required = @(
    "$RP\hud\betterhud\images\legendcraft-stat.yml",
    "$RP\hud\betterhud\images\legendcraft-hunter.yml",   # defines lc_icon_placeholder, lc_hud_*, lc_skill_frame, lc_cd_shroud_*
    "$RP\hud\betterhud\layouts\legendcraft-stat.yml",    # the lc_stat layout (per-class icon row lives here)
    "$RP\hud\betterhud\huds\legendcraft-stat.yml",
    "$RP\hud\indicators\icon_placeholder.png",           # the default black gem shown for every class
    "$RP\hud\skill-icons",
    # The party rows draw from two trees generate_hud.py does NOT produce: Volya-derived chrome
    # staged from the purchased zips, and the hand-authored class icons. A fresh clone therefore
    # has the YAML referencing PNGs that are not there -- the exact silent failure the rest of
    # this preflight exists to catch (the row renders, minus whichever art is missing).
    "$RP\hud\party\frame_portrait.png",                  # party-frame chrome
    "$RP\hud\class-icons\knight.png",                    # the 24 identity icons the CLASS rows draw
    "$RP\hud\betterhud\images\legendcraft-party.yml",
    "$RP\hud\betterhud\layouts\legendcraft-party.yml"    # the lc_party layout (layout 2 of lc_stat_hud)
)
foreach ($p in $required) {
    if (-not (Test-Path $p)) { throw "HUD deploy preflight failed: missing '$p' -- did generate_hud.py run? Aborting so we never ship a half-built HUD." }
}

Write-Host "[2/7] deploying to plugins/BetterHud..."
Copy-Item "$RP\hud\bars\*.png"        "$BH\assets\legendcraft\bars\"       -Force
Copy-Item "$RP\hud\stat-icons\*.png"  "$BH\assets\legendcraft\stat-icons\" -Force
foreach ($sub in 'texts','images','layouts','huds') {
    Copy-Item "$RP\hud\betterhud\$sub\legendcraft-stat.yml" "$BH\$sub\" -Force
}
# The lc_stat per-class icon row references images from the (historically named) "hunter" registry
# and art under assets/legendcraft/{frames,indicators,skill-icons}. The -stat loop above does NOT
# ship these, so a clean redeploy would drop the entire icon row -- ship them here. (generate_hud.py
# ran in step 1, so the regenerated frames/indicators PNGs exist on disk.)
Copy-Item "$RP\hud\betterhud\images\legendcraft-hunter.yml" "$BH\images\" -Force
foreach ($art in 'frames','indicators','skill-icons','vitals','party','class-icons') {
    $dst = "$BH\assets\legendcraft\$art"
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item "$RP\hud\$art\*" $dst -Recurse -Force
}
# Party frames: a hand-authored pair (image registry + layout) rather than a fifth -stat file,
# so the -stat loop above does not ship them.
Copy-Item "$RP\hud\betterhud\images\legendcraft-party.yml"  "$BH\images\"  -Force
Copy-Item "$RP\hud\betterhud\layouts\legendcraft-party.yml" "$BH\layouts\" -Force

Write-Host "[3/7] restarting server (BetterHud rebuilds build.zip)..."
Stop-GameServer; Start-GameServer

# Contract probe: the HUD is driven by the LegendCraft-Classes PlaceholderAPI expansion. If that
# expansion isn't registered (PAPI missing, or a plugin build that dropped it -- exactly how the
# skill-icon row went dark), every papi:legendcraft_* the config reads goes blank and the row
# vanishes. Confirm it registered rather than shipping a HUD wired to nothing.
$log = Get-Content "$SERVER\logs\latest.log" -Raw -ErrorAction SilentlyContinue
if (-not ($log -and $log.Contains("Registered PlaceholderAPI expansion 'legendcraft'"))) {
    Write-Host "  WARNING: the 'legendcraft' PlaceholderAPI expansion did NOT register this boot." -ForegroundColor Yellow
    Write-Host "  The HUD's placeholders (slot_count/subclass/slotN_*, resource/xp/vitals) will be blank" -ForegroundColor Yellow
    Write-Host "  and the skill-icon row will not render. Check: PlaceholderAPI installed, and the deployed" -ForegroundColor Yellow
    Write-Host "  LegendCraft-Classes jar exposes them (see src/test/resources/hud-placeholders.txt)." -ForegroundColor Yellow
}

# The merged dev pack has a fixed name and no version of its own: it is whatever the newest
# built base pack in dist/ plus the two plugin build.zips currently are. The base is resolved
# at merge time rather than pinned, so a pack rebuilt with new art reaches the dev pin.
$DEV_ZIP = "$DIST\LegendCraft-Pack-dev.zip"

Write-Host "[4/7] merging the newest built pack with the plugin builds..."
& python "$RP\tools\merge_dev_pack.py" | Out-Null
$sha = (Get-Content "$DEV_ZIP.sha1").Trim()

Write-Host "[5/7] publishing to the rolling GitHub 'dev' pre-release..."
& "$RP\tools\publish-pack.ps1" -Dev -Zip $DEV_ZIP | Out-Null

Write-Host "[6/7] pointing server.properties sha1 at the stable dev URL (sha $sha)..."
# The URL is the fixed dev-release asset; only the sha1 changes each build. Colons escaped for
# .properties. NOTE: must not be named $props -- PS vars are case-insensitive and $PROPS is the path.
$DEV_URL = 'https\://github.com/OmarZiadeh/LegendCraft-ResourcePack/releases/download/dev/LegendCraft-Pack-dev.zip'
$propsText = Get-Content $PROPS -Raw
$propsText = [regex]::Replace($propsText, '(?m)^resource-pack=.*$', "resource-pack=$DEV_URL")
$propsText = [regex]::Replace($propsText, '(?m)^resource-pack-sha1=.*$', "resource-pack-sha1=$sha")
[System.IO.File]::WriteAllText($PROPS, $propsText)

Write-Host "[7/7] restarting server (pushes the new pack)..."
Stop-GameServer; Start-GameServer

Write-Host ""
Write-Host "DONE - pack published to the rolling 'dev' release + live (sha $sha). Rejoin the client, accept the pack, screenshot." -ForegroundColor Green
