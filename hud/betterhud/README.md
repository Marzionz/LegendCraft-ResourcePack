# BetterHud — Skill-Casting HUD config

Renders the ability icon row (`hud-and-icons §3`) via BetterHud as a layered
re-skin of state the plugin already owns. Nothing here changes mechanics.

## ✅ Spike status (2026-07-09) — schema VERIFIED on the real build

**BetterHud 2.0.0 boots on Paper 26.1.2** (NMS `V26_R1`, Platform: Paper) on
mc-dev, and this config **parses + compiles**: all 24 registered textures land
in the generated `build.zip`, the HUD registers, and the self-host pack server
serves on port 8163. This closes the HUD row of the `plugin-strategy.md` buy-column
smoke-boot (visual sign-off in-client is the remaining human step).

## Files (all GENERATED — edit `tools/generate_hud.py`, then re-run)

BetterHud uses a three-tier structure (verified against the installed build's own
defaults, not docs guesses). **The installed build is `2.1.0-SNAPSHOT-447`** — not
the 2.0.0 the dated spike note above was written against, so check docs for that
version, per the online-docs rule below:

- `images/legendcraft-hunter.yml` — registers each PNG:
  `name: { type: single, file: legendcraft/... }` (paths relative to
  `BetterHud/assets/`; subfolders fine).
- `layouts/legendcraft-stat.yml` — layouts = **numbered** `images:` entries with
  `name/x/y/layer` (top-left anchored, integer px), plus `texts:`. Exactly **one**
  layout, `lc_stat`, holding the stat block *and* the skill-casting row: the row is
  not a second layout, it is drawn inside `lc_stat` at **negative y**, measured up
  from the stat block.
- `huds/legendcraft-stat.yml` — `lc_stat_hud`, one hud with that one layout,
  anchored `gui: {x:50, y:100}` (bottom-center) + `pixel:` offsets. Keep it to one
  hud: BetterHud gives each *default-hud* its own bossbar carrier and only the first
  repositions, so a second hud dumps its glyphs at the top boss-bar line.

> **Retired 2026-07-22, generator code deleted 2026-07-28 — three files, all gone:**
> `layouts/legendcraft-hunter.yml` (`lc_hunter_skill_row` / `lc_hunter_states_demo`),
> `huds/legendcraft.yml` (`lc_skill_hud`), and `texts/legendcraft-hunter.yml`
> (`lc_skill_text`, the spike row's numeral font — the live row uses `lc_stat_text`).
> None of the three exists and nothing can regenerate them; the production row lives
> in `legendcraft-stat.yml`. The only surviving `-hunter` file is
> `images/legendcraft-hunter.yml`, which is **live** — the historically-named image
> registry the per-class icons still resolve through.

The layout YAML's pixel offsets are **computed by the generator from the same
geometry as the preview compositor** — art and YAML cannot drift.

## Deploy

Use `tools/deploy-hud.ps1` — it regenerates, preflights that every expected
file exists, then restarts mc-dev and repoints the pack. The manual equivalent:

```
BH=/c/Repositories/mc-dev/server/plugins/BetterHud
# ART -- all five trees. Omitting bars/ or stat-icons/ leaves the layout pointing at
# legendcraft/bars/* and legendcraft/stat-icons/* that aren't there: the stat block
# silently fails to render even though the YAML looks correct.
cp -r hud/{bars,stat-icons,frames,indicators,skill-icons} $BH/assets/legendcraft/
# CONFIG -- the -stat quartet, plus the (historically named) "hunter" image registry the
# lc_stat row's per-class icons resolve through.
cp hud/betterhud/images/legendcraft-hunter.yml $BH/images/
cp hud/betterhud/images/legendcraft-stat.yml   $BH/images/
cp hud/betterhud/layouts/legendcraft-stat.yml  $BH/layouts/
cp hud/betterhud/huds/legendcraft-stat.yml     $BH/huds/
cp hud/betterhud/texts/legendcraft-stat.yml    $BH/texts/
# restart server (never hot-swap); or /betterhud reload for config-only changes
```

Server-side toggles applied on mc-dev:
- `config.yml`: `default-hud: [lc_stat_hud]` — ONE GUI hud carries both the stat block and the
  per-class skill-icon row (the row lives in the `lc_stat` layout). BetterHud only repositions the
  FIRST default-hud, so a second GUI default-hud collides on the bossbar carrier and renders
  nothing — never add one; add a layout to `lc_stat_hud` instead.
- `enable-self-host: false`.

## Placeholder contract — the #1 way the skill icons vanish

The per-class skill row (in the `lc_stat` layout) draws each slot as a black placeholder gem with
real art layered over it, and **every element is gated on `papi:legendcraft_*` placeholders**
(`slot_count`, `subclass`, `slotN_state|cd_percent|cd_secs|charges`, plus the stat/xp/vitals ids).
Those are served by LegendCraft-Classes' `HudPlaceholders` expansion. If the deployed plugin jar
doesn't answer one — a stat-only build, a refactor that dropped a case, or PlaceholderAPI absent —
the gating condition fails and the **whole row (black gems included) disappears**. This has bitten
us more than once, and it fails silently.

Guards, layered:
- **`hud-placeholders.txt`** (generated here by `generate_hud.py`) is the config side of the
  contract: every id the HUD reads. **`HudPlaceholderContractTest`** in LegendCraft-Classes reads a
  synced copy and fails the build if the plugin stops answering any — so a rebuild can't silently
  drop one. When you add/rename a HUD placeholder: regenerate, then copy the new
  `hud-placeholders.txt` into the plugin's `src/test/resources/`.
- **`deploy-hud.ps1`** greps the server log after restart and warns if the `legendcraft` expansion
  didn't register.
- **Deploy the plugin jar and this HUD config from matching revisions** — they are separate repos,
  and the outage came from a stat-only jar landing over a slot-consuming config.

**Any agent editing the HUD wiring or placeholders MUST look up the current BetterHud and
PlaceholderAPI docs online first** — their config syntax (conditions, listeners, image types) and
the expansion API change across versions, and guessing from memory is how these regressions happen.
See the `legendcraft-icon` skill, Step 1.

## Party frames + health afflictions (STAGED, not deployed)

Both grew out of Volya's purchased packs (Party HUD 1.1.0, MMORPG HUD 1.2.5), which are
**MythicHUD** products sharing no syntax with BetterHud. The owner's rule, 2026-08-28:
**buy the read, author the pixels.** Full inventory, the rulings and the class-shield spec:
`Plans/todo/hud-volya-integration.md`.

- **Party frames** are the one hand-authored pair in this tree — `images/legendcraft-party.yml`
  and `layouts/legendcraft-party.yml`. Chrome and bars come from the purchased zip via
  `tools/stage_volya_hud.py` (the zips live in `C:\Repositories\Bought assets\` and are
  in **no** repo; re-run the script after a pack update). It re-ramps every fill that carries a
  hue onto the locked palette, so party bars match the stat block. The **class icons are ours** —
  the 24 identity icons, 24 conditioned elements per row gated on the followed member's
  `legendcraft_subclass`, at `scale: 0.5` from 32x32 into the frame's 16px square.
  Registered as **layout 2 of `lc_stat_hud`**, not a second hud, for the reason the config note
  above gives.
- **Health afflictions** are generated, not staged: `AFFLICTION` / `affliction_fill` /
  `affliction_heart` in `generate_hud.py`, written to `hud/vitals/`. They live in the
  generator because they draw inside the stat block's HP cell and a second layout would have to
  restate its geometry -- the drift this pipeline exists to prevent. Layers 10-18, one per state,
  because several are live at once and a tie is undefined.

**`follow:` is what makes a party row possible.** It resolves a PAPI to a player name and
BetterHud then evaluates that element's listener, conditions and pattern against **them**
(`ImageRenderer`, verified in source -- the wiki documents `follow` only for `texts`/`heads`, but
it lives on the shared `HudLayout` base and images honour it). With
`cancel-if-follower-not-exists` defaulting true, an empty or offline slot renders nothing, so the
stack sizes itself and needs no party-size gate.

**The party frames render nothing until LegendCraft-Classes answers five new placeholders**
(`legendcraft_party_member_1..4`, `legendcraft_is_party_leader`). No YAML can substitute: a PAPI
expansion is Java, BetterHud's built-in party support is hard-coded to MMOCore and Parties, and
its `placeholder/` folder only wraps placeholders that already exist. The ids are already in
`hud-placeholders.txt`; do **not** sync that file into the plugin's `src/test/resources/` until
the same slice adds the answers, or `HudPlaceholderContractTest` goes red on ids nothing serves.

**Two art rules these earned, both only visible at 7px.** A party resource bar is 2px tall and
cannot show rage's two bands, so its ramp is ember-led or it reads as a second HP bar. And an
affliction that tints without changing SHAPE fails the greyscale test -- poison, burning and
regeneration all read as "healthy" at zero saturation on their first pass. Render the composite;
neither defect was visible in the source.

## Pack delivery (current: vanilla push — 2026-07-09)

BetterHud's **self-host is OFF** (advertised the public IP, unreachable from
LAN; also crashes the mineflayer bots). **DevPackGuard is REMOVED** (its
`127.0.0.1` URL blocked non-local testers — user decision). Current path:

1. BetterHud builds `plugins/BetterHud/build.zip` on every enable/reload
   (**verified deterministic** — same configs ⇒ same sha1, so merges stay valid).
2. `tools/merge_dev_pack.py` merges that build with the base LegendCraft
   pack → `dist/LegendCraft-Pack-<ver>.zip` + `.sha1`.
3. `tools/publish-pack.ps1 -Dev` uploads it to the rolling GitHub `dev`
   pre-release under the **fixed** asset name `LegendCraft-Pack-dev.zip`, so the
   URL never changes; **vanilla `server.properties` pushes it**: `resource-pack=`
   that URL + `resource-pack-sha1=` (the only field rewritten per build),
   `require-resource-pack=true` (the delivery contract in
   `Design/plugin-strategy.md §4`, "the Wynncraft required-download model" —
   models are not optional).
   `deploy-hud.ps1` does steps 1–3 for you.
   *(Superseded: serving `dist/` locally with `python -m http.server 8123`. That
   was host-only — the GitHub route is what replaced it.)*

**⚠️ pack.mcmeta must be BetterHud's.** Its `overlays` section maps pack-format
ranges to overlay dirs (`betterhud_26_1` for format 84). The first merge kept
the plain LegendCraft mcmeta → overlays never applied → the pack loaded but the
HUD rendered NOTHING. The merge script now asserts overlays survive.

**Remote testers:** already handled — no port-forwarding needed. `deploy-hud.ps1`
publishes the pack to the rolling GitHub `dev` pre-release and points
`server.properties` at that fixed asset URL
(`.../LegendCraft-ResourcePack/releases/download/dev/LegendCraft-Pack-dev.zip`),
rewriting only `resource-pack-sha1` each build. The old self-hosted
`http://127.0.0.1:8123/...` route was host-only and is no longer what the server
serves; port-forwarding TCP 8123 does nothing for the pack now.

**⚠️ Bot runs:** a non-blank `resource-pack=` crashes the mineflayer bots on
join (config-phase push). Blank **`resource-pack=` only** + restart before bot
testing. **Restore it after — leave `require-resource-pack=true` alone throughout.**
Blanking the URL is what spares the bots; flipping `require` to `false` would
quietly disable model enforcement on a shared box and is not part of this dance.
Easiest restore is re-running `deploy-hud.ps1`, which rewrites the URL and sha1
together. (DevPackGuard existed to whitelist bots — re-adding it with a public
URL would restore that; its config folder is kept.)

**After any HUD art/config change:** run `tools/deploy-hud.ps1` — it does the
whole chain and preflights that nothing is half-built. The manual equivalent:

`generate_hud.py` → copy into `plugins/BetterHud` → restart (BetterHud rebuilds
`build.zip`) → `merge_dev_pack.py <ver>` → **`publish-pack.ps1 -Dev`** → update
**`resource-pack-sha1` only** in `server.properties` → restart.

> ⚠️ **Do not skip the publish step, and do not touch the URL.** The asset name is
> fixed (`LegendCraft-Pack-dev.zip`), so there is no filename to bump — the sha1 is
> the only thing that moves. Bumping the sha1 without uploading leaves the fixed URL
> serving the *old* zip, so every joining client fails the hash check; with
> `require-resource-pack=true` that is a **disconnect for everyone**, not a silent
> fallback.

## In-client review

**Client version MUST be 26.1.2 (match the server).** BetterHud repositions
its glyphs via version-specific `rendertype_text` core shaders (newest overlay:
`betterhud_26_1`). A newer client (e.g. 26.2 via ViaVersion) silently drops the
shader → the whole HUD renders as a garbage glyph strip at the boss-bar line.
That symptom = pipeline fine, shader skipped. (mc-dev already runs the 2.1.0-SNAPSHOT
build — `BetterHud-bukkit-2.1.0-SNAPSHOT-447.jar` — so this is the current behaviour,
not something a future upgrade fixes.)

Join mc-dev and **accept the pack prompt**. The stat block renders bottom-center
with the skill row directly above it. Manual toggle if needed:
`/hud hud add <player> lc_stat_hud` (`/hud reload` after config-only edits) — note
this is `lc_stat_hud`; the old `lc_skill_hud` was retired 2026-07-22 and adding it
does nothing. `merge-boss-bar: false` is required on mc-dev — the Classes plugin's
Phase-1 resource boss bar fights BetterHud's carrier line.

## State-driven layers (the production wiring) — SHIPPED

The state machine runs on **conditions**, numbered blocks on layout elements:

```yaml
    1:
      name: lc_oom_soft
      conditions:
        1:
          first: "papi:legendcraft_slot1_state"   # no [brackets] in conditions
          second: "'starved'"
          operation: '=='
```

Both blockers cleared: PlaceholderAPI is installed (2.12.3) and LegendCraft-Classes
serves the contract from `com.legendcraft.classes.hud.HudPlaceholders`.

**Slot ids are class-agnostic — `slot1`/`slot2`/`slot3`/`ult`,** mapped from the
class's `skills()[0..2]` + `ultimate()`. The early `legendcraft_slot_state_<trap|
arrow|beast|pack>` draft was Hunter-specific and never shipped; do not copy it.
The authoritative list is the generated `hud-placeholders.txt` — every id there
must be answered or the element gated on it silently vanishes.

Shipped **in this HUD config**: cooldown numerals, the circle-split radial sweep,
the out-of-mana tint, the charge-pip sprite row, the deny/ready flash, per-class
icon art gated on `legendcraft_subclass`, and the Phase-1 boss-bar retirement
(`hud-and-icons §7`).

"Shipped" here means the *element exists and is wired to a placeholder* — not that
the feature is finished end-to-end. The charge-pip row is the example: the sprites
and their `charges == k` gating are in this layout, while making
`legendcraft_<slot>_charges` read true for every charge skill is still open work
(`Plans/in-progress/hud-ux-backlog.md` item 2). Config-side done ≠ backlog item done.

Not built at all: the per-tile resource pip on each skill frame, and the ~1 Hz
insufficient-resource pulse `hud-and-icons §4` gives it. `framed_row` emits no pip
element; the starved state ships as the out-of-mana tint instead.

## Stat HUD (Phase 2 — LIVE on mc-dev)

The chunky MMORPG stat block (`hud-and-icons §2`): a 2×2 grid above the hotbar —
HP (red) / armor (green) over resource (recolored) / food (brown) — with centered
`current/max` numerals, flanking icons, and an XP bar + level. Generated by the same
`generate_hud.py` as the skill row; files are `{texts,images,layouts,huds}/legendcraft-stat.yml`
plus art under `hud/{bars,stat-icons}/`. Active via `config.yml default-hud: [lc_stat_hud]`.

- **Native bars (no PAPI):** health/armor/food are `type: listener` with built-in
  `class: health|armor|food`. Armor replaces the reference's stamina bar (design call).
- **Placeholder bars (need PAPI):** the resource bar is `class: placeholder` reading
  `(number)papi:legendcraft_resource_current` / `_max`; the XP fill reads
  `legendcraft_xp_percent`. Per-class recolor = three fill images (mana/energy/rage), each
  gated by a `conditions:` block on `papi:legendcraft_resource_type`.
- **Requires:** PlaceholderAPI installed (it is, 2.12.3) + the `legendcraft` expansion from
  LegendCraft-Classes (`HudPlaceholders`, registered on enable). Placeholders exposed:
  `resource_current|max|percent|type`, `level`, `xp_percent`, `xp_to_next`,
  `health|max_health|food|armor`.
- **Phase-1 boss bar retired:** `SimpleResourceService` now defaults `showBossBar=false`
  (pass `true` to bring it back). Pool/regen/cost/deny-sound unchanged.

### Deploy + tuning

Run `tools/deploy-hud.ps1` — it regenerates, deploys, restarts (rebuild), merges the
pack with a bumped `-dev` version, repoints `server.properties`, and restarts (push). Then
rejoin the client and screenshot. **The pack push needs a rejoin** (sha changes each build).

Tuning knobs live at the top of `generate_hud.py`: `STAT_HUD_X` / `STAT_HUD_Y` (block
position — BetterHud centers on `gui.x:50`, so X is a nudge off-center), `STAT_TEXT_SCALE`
(numeral size), and the bar art (`BAR_RAMP`, `bar_empty`, `bar_fill`). Preview without a
server via `hud/previews/stat_hud_mock.png`.

**Still to nail (needs in-client screenshots):** exact horizontal centering and the final
`STAT_HUD_Y`; the hotbar reskin is deferred (`remove-default-hotbar` blanks the vanilla
hotbar with no replacement — a manual rebuild + a slot-follow placeholder).
