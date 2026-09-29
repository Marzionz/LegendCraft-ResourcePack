# Flame Surge — rune-circled lava ground

`pyro_surge_patch` is the Level 45 burning-ground MOTION RIG for BetterModel. It keeps the original rig identifier, all ten bone names and UUIDs, five clip names, clip durations and loop modes, and **1.25-block art radius at scale 1**. The hook still owns the four-second lifespan and its three ages. This change re-arts the patch from the approved concept's bottom row: fractured basalt and connected lava veins inside a rune circle, short three-dimensional flame tongues around the rim, and five rock chunks.

The brief supersedes the old chips-only/no-glyph art decision. The new boundary is explicitly a rune circle. `surge_volcano`, plugin code, balance and server files are untouched.

## Shape, radius and textures

Each state has a ground plane at y = 0.28 u with only its up face textured, double-sided for authoring. The plane is 320/7 u (45.714286 u) square, centred on the origin. Its 64×64 texture registers the ring at radius 28 pixels around (31.5,31.5); this yields 20 u = **1.25 blocks**. Maximum occupied pixel-centre radius is 1.248804 blocks, within half a texture pixel of the intended edge. Every age uses the same registration. All rock and flame corners remain inside radius 19.259868 u, so decorative cubes do not overstate the zone edge.

Runtime scale remains `patchRadius / 1.25`; for a 3-block radius, **2.4**. The hook advances age1 → age2 → age3 across the configured lifetime and times gutter to finish at that lifetime. No clip spans or retimes the entire four seconds.

The ground textures use individually composed basalt plates, chipped edges and small clustered marks, with a connected branching crack network. Age 1 has orange/yellow veins and a hot ring; age 2 shifts them to ember red; age 3 breaks the glowing network into faint residual embers over charcoal. Ring glyphs are small diamonds, crosses, boxed squares and hooked strokes.

Hot/cooling states carry ten flame clusters. Each cluster has a hand-shaded cube, a 45-degree-yawed partner at 84% x/z and 91% y, and a smaller tilted tip, following Scorch's lobe recipe. Peak top is 8.8004 u in age 1 and 3.8836 u in age 2; age 3 has no flames and only 2.2-u-high rock chunks. Every shown corner remains above ground (minimum y = 0.1 u).

Seven embedded textures, with editable PNGs beside the model: three 64×64 ground ages; four 16×16 materials (`basalt`, `orange`, `yellow`, `ember_red`). Scorch supplies the accepted flame material tiles; basalt and ground plates are newly painted. All visible pixels belong to `#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`. Alpha is only 0/255; no cyan, no emissive pairs.

## Rig and timing contract

Unyawed identity `root` → `fx` → the original eight state bones:

| Bones | Geometry per bone | Use |
| --- | ---: | --- |
| `pf_a1_1`, `pf_a1_2` | 36 | Hot: ground, five rocks, ten three-cube flames |
| `pf_a2_1`, `pf_a2_2` | 36 | Cooling: same layout, shorter dimmer flames |
| `pf_a3_1`, `pf_a3_2` | 6 | Dying: ground and five rocks, no flames |
| `pf_g1` | 15 | Gutter: cooling ground, rocks, three small flame clusters |
| `pf_g2` | 6 | Gutter: dying ground and rocks |

177 elements in the complete rig, at most 36 shown at once. All original bone UUIDs are retained. The `_2` age bones retain valid alternate geometry and their contract names but stay hidden in normal age playback. This prevents the old two-frame smolder loop from blinking under BetterModel's scale-step handling.

| Clip | Mode / duration | Tick states |
| --- | --- | --- |
| `age1` | loop / 0.6 s (12t) | `pf_a1_1` stays shown at ticks 0–12; every other state stays hidden |
| `age2` | loop / 0.6 s (12t) | `pf_a2_1` stays shown at ticks 0–12; every other state stays hidden |
| `age3` | loop / 0.6 s (12t) | `pf_a3_1` stays shown at ticks 0–12; every other state stays hidden |
| `gutter` | hold / 0.25 s (5t) | `pf_g1` at ticks 0–1; `pf_g2` at ticks 2–3; all hidden at ticks 4–5 |
| `hidden` | loop / 0.05 s (1t) | All state bones hidden |

All scale tracks have keys on every tick, including held values. Every changing segment is one tick. Age clips never swap frame bones inside their loops; the plugin changes age clips by their existing names. Gutter preserves the original state-change ticks and terminal hidden state, with its long changing segments replaced by one-tick segments. There are no rotation or position keys. Static geometry follows the unyawed prop convention in `SIGNS.md`.

## Verification and renders

Native Blockbench Cube/Group/Animation/Texture APIs through `bb.py` at `http://localhost:3000/bb-mcp` authored the geometry and clips in Undo transactions. The original groups remained in place. Native project export was normalized only by folding group metadata into legacy outliner objects; no script generated model geometry as JSON.

Before and after pages follow `PROP-PREVIEW.md`: `%TEMP%/bb-pyro-surge/patch_before.html`, then `pyro_surge_patch_render_preview.html` generated from the actual final rig. The scratch reader handles empty bone animators and per-texture UV dimensions. Browser security blocked local-file navigation during this session; browser playback is unverified. Native Blockbench supplied the visual review.

The six required stills are `pyro_surge_patch_render_age{1,2,3}_{eye,top}.png`. Eye camera is (0,25.6,96) u toward the ground origin: 1.6 blocks up, six blocks out. Top camera is (0,96,0.001) u toward the origin (the negligible z offset avoids a degenerate look-at basis). Both use perspective FOV 50, at authored scale. Hot, cooling and dying reads were visually inspected. `_gutter_hidden.png` and `_hidden_hidden.png` record the terminal and parked states. Reloaded Blockbench bounds agree with independent rotated-corner calculations.

Verified original bone names/UUIDs, clip names/durations/loop modes, one-tick changing segments, no age-frame swapping, hidden end states, palette and binary alpha, registered radius, cube radius and above-ground bounds.

Staged with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File deploy-rigs.ps1 -Rig pyro_surge_patch -Prop -StageDir dist/pyro-surge-patch-stage
powershell -NoProfile -ExecutionPolicy Bypass -File deploy-rigs.ps1 -Preflight -Prop -StageDir dist/pyro-surge-patch-stage
```

`-Prop` asserts the rig's existing identity root. The dedicated stage avoids replacing another session's staging output. The stage contains this rig only; `STAGE-READY` matches every file and `STAGE-INVALID` is absent. Staged model SHA1: `73cd2e1589e907a9815cecbfc385c2f441d80cee`. **Stage only; no server copy.**

In-game checks still owed: BetterModel clip transitions, no blink across age changes, exact four-second age/gutter schedule, 3-block boundary alignment at scale 2.4, terrain placement and lighting/cutout read against real ground.

## History and skill overrides

2026-09-28: replaced the old painted smolder decal with rune-circled cracked lava, paired-cube rim flames and basalt chunks. Retained the plugin's rig/bone/clip/duration/radius contract. Removed internal age-frame toggling; gutter retains its original swap times with one-tick segments. Old `tools/build_pyro_surge_frames.py` and `tools/build_pyro_surge_rigs.py` are STALE for this asset; this model is authoritative.

The brief explicitly overrides `legendcraft-blockbench/SKILL.md`'s “the commit and the handoff are all forbidden” before a later owner ruling, and `PROP-PREVIEW.md`'s “Then the turn ends: the ruling is the next message”. These explicit skill gates do not pause this authorized build/render/commit session. The skill's separate models-repository index/push workflow is also superseded: only named asset paths on this pack worktree branch are committed, with no push or PR.
