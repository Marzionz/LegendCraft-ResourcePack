# Conflagration detonation

A heavy, rolling 3D fireball detonates at the caster's feet above a flat cracked-lava blast disc. The outer edge marks the ultimate's true reach. This replaces the old eight-frame flat build with **16 frames at one tick each: 0.8 seconds, 20 fps**. Runtime swaps `legendcraft:classes/pyro_conflag_explosion_1` through `_16` on one item display and removes it after tick 16. This is an authoring/preview frame stack, never a BetterModel deployment. No plugin code is included.

## Sources

- `pyro_conflag_explosion_concept_ground.png`: owner's 1774 x 887 sheet, eight top-down cells in a 4 x 2 grid; source for flash, advancing shockwave, cracked centre, rune band and cooling stages.
- `pyro_conflag_explosion_concept_side.png`: owner's eight-cell silhouette, heat and timing reference only. It is not mapped onto a plane or any runtime texture. Lobes cut by source-cell edges become complete overlapping 3D clusters.
- `pyro_scorch_explosion.md`: approved nested-cube lobe recipe, outward quaternion roll, upper highlight/darker underside material treatment, and registered ground-disc method.

The original sheets are committed unchanged. PNGs were painted/cropped by script; all geometry, groups, rotations and animation keys were created inside Blockbench through the localhost MCP and native Cube, Group, Texture and Animation APIs, with Undo transactions. The native project codec exported the rig; only its group descriptors were folded into the legacy outliner serialization expected by the existing generator.

## Ground and radius contract

Frame 1 has the small ground flash. Frames 2-4 expand the shockwave through 53%, 76% and 92% of its full radius. From frame 5 through frame 16, every outer band is exactly the same authored **36.8 u = 2.3-block radius**. The horizontal band geometry uses 24 tangent tile elements, each spanning 15 degrees with its own 32 x 32 PNG. The outer shock/fire line and inner rune belt occupy separate radial zones on each tile. Binary cutout clips sector overlaps and trims outer corners to the same circle. The raster edge is accurate to one radial texel; radius does not change as the ring cools.

The band is 6.2 u deep at full radius. Its circumferential density is approximately 10.2 pixels per block at the 12-block true radius. The central disc has radius 30.8 u, overlapping the inner tile edge by 0.2 u, and samples a coarser 96 x 96 PNG. Frame N's centre is y = 0.25 + 0.035(N-1) u; tiles sit another 0.025 u above it. Only the up face is textured. No overlapping back-face drawing.

The centre textures retain the sheet's cracked lava, with RGB mapped to the nearest allowed palette entry and alpha thresholded at 80. Frame 1 retains the cleaned flash composition (components smaller than eight source pixels dropped). Cells 2/3 sample central source radii 80/140 pixels; cells 4-8 sample radius 120 pixels, registered over the central disc. This crops the sheet's low-resolution rune band out of the centre: the visible rune band is supplied by the high-resolution tiles. Transparent holes within the later ground substrate use charcoal. The band is a deliberate pixel repaint of the source's shock/rune/charcoal progression, rather than a single enlarged disc.

FLIPBOOKS keeps `pyro_conflag_explosion | pyro_conflag_explosion | detonate | 4`. **Shrink remains 4.** Generated item display scale = `4 * trueRadius / 2.3`; the authored unshrunk rig uses `trueRadius / 2.3`. Whole-rig rotated bounds: x/z [-36.8, 36.8], y [0.25, 48] u, inside the prescribed shrink-4 box. No shrink change was needed.

## Fireball and outward roll

The peak has twelve complete lobes: the large white-hot central mass, upper crown, six surrounding lower lobes and four upper lobes. Each lobe contains a main cube and an overlapping 45-degree yaw companion at 84% x/z and 91% y. The early core and crown also have a 76%-size companion pitched 32 degrees and rolled 15 degrees. The hottest central lobe is 27 x 28 x 25 u before the tiny peak fit below. Peak frame 6 measures 56.317 x 47.240 x 57.076 u over its fireball bounds: about **3.52 x 2.95 x 3.57 blocks**. Its highest corner is 48 u above the ground origin.

For each off-axis lobe with horizontal direction `d = (x,0,z)/sqrt(x*x+z*z)`, the outward tangent axis is `(d.z,0,-d.x)`. Compose the accumulated positive axis-angle quaternion BEFORE the baseline cube orientation, using Blockbench rest-space ZYX. Phase is `(frame-1)*22.5 degrees`: never reset it when a lobe continues, shrinks, or becomes smoke. Central lobes do not roll. All 225 lobe cubes are numerically checked against this rule. There are no animation rotation keys: the baked frame geometry carries the motion. The unyawed root follows `SIGNS.md`.

Frames 1-7 carry thin shaded streak cubes; frames 2-7 fling two blocky cross glyphs made from four cubes. Three cyan-fleck cubes occur in frame 1 only. Frames 8-10 separate and cool the rolling mass; 11-13 become ember-cored grey smoke; 14-16 leave shrinking charcoal puffs and falling embers. No lobe ends at a flat source-cell cutoff.

## Per-frame contract

Each frame shows from tick N-1 to N. Ground cell mapping advances the first three source cells during frames 1-4, then uses cells 4-8 for two or three frames each.

| Frame | Tick | Ground cell | Outer radius (blocks) | Lobe clusters | Lobe cubes | Ground | Streaks | Glyph cubes | Flecks/embers | Total | Roll phase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0..1 | 1 | flash | 1 | 3 | 1 | 5 | 0 | 3 | 12 | 0 degrees |
| 2 | 1..2 | 2 | 1.219 | 5 | 12 | 25 | 6 | 4 | 3 | 50 | 22.5 degrees |
| 3 | 2..3 | 2 | 1.748 | 8 | 18 | 25 | 6 | 4 | 3 | 56 | 45 degrees |
| 4 | 3..4 | 3 | 2.116 | 10 | 22 | 25 | 6 | 4 | 3 | 60 | 67.5 degrees |
| 5 | 4..5 | 4 | 2.300 | 12 | 26 | 25 | 5 | 4 | 3 | 63 | 90 degrees |
| 6 | 5..6 | 4 | 2.300 | 12 | 26 | 25 | 5 | 4 | 3 | 63 | 112.5 degrees |
| 7 | 6..7 | 4 | 2.300 | 12 | 26 | 25 | 5 | 4 | 3 | 63 | 135 degrees |
| 8 | 7..8 | 5 | 2.300 | 10 | 20 | 25 | 0 | 0 | 7 | 52 | 157.5 degrees |
| 9 | 8..9 | 5 | 2.300 | 8 | 16 | 25 | 0 | 0 | 7 | 48 | 180 degrees |
| 10 | 9..10 | 6 | 2.300 | 7 | 14 | 25 | 0 | 0 | 7 | 46 | 202.5 degrees |
| 11 | 10..11 | 6 | 2.300 | 6 | 12 | 25 | 0 | 0 | 7 | 44 | 225 degrees |
| 12 | 11..12 | 7 | 2.300 | 5 | 10 | 25 | 0 | 0 | 7 | 42 | 247.5 degrees |
| 13 | 12..13 | 7 | 2.300 | 4 | 8 | 25 | 0 | 0 | 7 | 40 | 270 degrees |
| 14 | 13..14 | 8 | 2.300 | 3 | 6 | 25 | 0 | 0 | 8 | 39 | 292.5 degrees |
| 15 | 14..15 | 8 | 2.300 | 2 | 4 | 25 | 0 | 0 | 8 | 37 | 315 degrees |
| 16 | 15..16 | 8 | 2.300 | 1 | 2 | 25 | 0 | 0 | 8 | 35 | 337.5 degrees |

750 elements total; maximum **63 per frame**, below the 64-element limit. The 24 ground-band tiles are absent only in the initial small flash frame.

## Ground clearance and peak fit

Five lobe-cluster floor lifts keep every rotated companion above the ground. Two uniform fire-only fits keep the peak at the requested three-block height. The fixed-radius ground geometry is unaffected.

| Frame | Part | Correction (u unless multiplier) |
| --- | --- | ---: |
| 1 | 0: floor lift | 0.154222598 |
| 3 | 2: floor lift | 0.383987348 |
| 3 | 5: floor lift | 0.430193803 |
| 6 | all_fire: uniform height fit | 0.992282370 |
| 7 | 2: floor lift | 0.525462121 |
| 7 | 5: floor lift | 0.588758634 |
| 7 | all_fire: uniform height fit | 0.992282370 |

These are ordinary ground/size registration adjustments, not changes to the accumulated roll. The saved model was reloaded under a unique temporary path and its actual Blockbench mesh Box3 bounds agree with analytic rotated-corner checks to floating-point precision. No corner goes below ground; no cropped lobe is present.

## Textures

183 embedded editable PNGs under `pyro_conflag_explosion_tex_`: 168 tile textures (24 for each used band stage, source cells 2-8), eight 96 x 96 central-disc stages, and seven 32 x 32 materials (`white_hot`, `yellow`, `orange`, `ember_red`, `smoke_grey`, `dark_smoke`, `cyan`). All lobes, including every lobe over half a block, use 32 x 32 material swatches.

Fire and smoke faces use deliberately stepped concentric contours, an asymmetric hot centre, a thin upper highlight and returning dark underside curl; five palette steps distinguish planes without smooth gradients or flat fills. Up faces sample rows 0-20, down faces 16-32, vertical faces all 32 rows. The cyan material is reserved for the initial flash flecks.

Visible runtime texture pixels are exclusively `#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`, with `#9FE8FF` on flash flecks only. Alpha is exclusively 0 or 255. The unmodified reference sheets are not runtime textures.

## Rig and clips

Hierarchy: `root -> fx -> frame_1..frame_16`, root rotation [0,0,0]. Each frame directly owns the `ground_*` and fireball elements. `detonate` is a 0.8-second hold clip; every frame bone has a step-scale key on every tick 0..16, scale 1 only on its own visible tick and 0.001 otherwise. All frames are hidden at tick 16: **ends hidden**. `hidden` is a one-second loop, every frame parked at 0.001 on each tick. Every changing key segment lasts one tick. No position or rotation keys. Exact 180-degree ring-tile turns are baked into coordinates and up-face UV orientation to accommodate the existing generator's diagonal-matrix check.

## Verification and renders

The prop loop starts from `C:/Users/omarz/AppData/Local/Temp/bb-pyro-conflagration/explosion_before.html` and ends at `explosion_preview.html` in the same folder, both generated from real rig files with clip detonate and chest offset 0. The scratch preview reader handles empty bone animators, per-texture UV dimensions, 180-degree UV turns, ZYX rest rotations and binary depth-writing cutout surfaces.

- `pyro_conflag_explosion_render_contact.png`: all sixteen frames, bystander eye.
- `pyro_conflag_explosion_render_detonate.gif`: sixteen 50 ms frames, exactly 20 fps / 0.8 seconds.
- `pyro_conflag_explosion_render_frame_06_side.png`: peak from 90 degrees around the ring.
- `pyro_conflag_explosion_render_frame_06_top.png` and `_render_frame_12_top.png`: straight-down peak and cooling ground/ash.
- `pyro_conflag_explosion_render_end_hidden.png` and `_render_hidden.png`: terminal hidden state and hidden loop.

Bystander camera is (0,25.6,96) u, target (0,18,0), FOV 50: 1.6 blocks up, 6 blocks out. Second side is (96,25.6,0). Top camera is (0,125,0.001), target origin, FOV 50. These are authored-scale views before runtime true-radius scaling. All named stills and the numbered motion contact sheet were visually inspected in Blockbench renders.

Verification covers per-frame budgets, every rotated corner, native reloaded world bounds, 225 outward quaternion rolls, all twelve fixed-radius frames, palette/binary alpha, embedded/editable PNG equality, all 17 detonation tick states, hidden-loop keys, one-tick segments, 16 generator spans, all 456 generated files byte-for-byte and GIF frame count/durations. Pack build and manifest validation results, plus the exact post-commit generator drift result, are in the handoff report.

The brief explicitly overrides `legendcraft-blockbench/SKILL.md`: “the commit and the handoff are all forbidden” before a later owner ruling, and `PROP-PREVIEW.md`: “Then the turn ends: the ruling is the next message”. These explicit skill gates do not stop this authorized build. The brief's named-path pack-branch workflow also replaces the skill's unrelated index/push workflow.

No plugin edits, deployment, branch switching, push or PR. Remaining in-game checks belong to the owner: 8/12-block damage-edge alignment, shrink restoration, one-tick item swaps, lighting/cutout behaviour, and display removal after tick 16.

## History

2026-09-28: replaced the flat eight-frame detonation with a sixteen-frame twelve-lobe 3D fireball and tiled ground/rune band; refined shaded cores, registered the cracked centre inside the tile band, regenerated item models and retained shrink 4.
