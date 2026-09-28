# Scorch land explosion

Scorch's meteor bursts where it stops, damaging enemies within 4.0 blocks and applying a Burning stack. A block-ish 3D fireball rises above the approved 2D ground ring for **16 frames at one tick each: 0.8 seconds, 20 fps**. The ring communicates the damage edge.

This frame-stack rig feeds `tools/gen-flipbook-frames.py` and the prop preview. Runtime uses ONE item display swapping `legendcraft:classes/pyro_scorch_explosion_1` through `_16`, one model each tick, then removes the display at tick 16. The rig is never deployed to BetterModel. This asset change contains no plugin code.

## Sources and preservation

- `pyro_scorch_explosion_concept_ground.png`: approved 1774 x 887 RGBA sheet, eight cells in a 4 x 2 grid. The disc retains the diamond, square, cross and hooked runes from this drawing.
- `pyro_scorch_explosion_concept_side.png`: reference for silhouette, heat progression and timing only; not a texture.
- Craft reference: Unending Blows `src/assets/legendcraft/textures/item/flurrybwl/strike_*.png` and `impact_*.png`: narrow shaded strokes, hot heads, dark tails and empty space.

Commit `049598e` is the eight-frame baseline. Old frame k is new frame 2k-1. Every original non-disc element is preserved exactly, including its UUID, coordinates, rotations, faces and materials. The only original-element changes are the requested disc y offsets. All fourteen embedded texture sources are byte-for-byte unchanged. The earlier crossed side-sheet build is superseded.

## Ground disc and radius contract

Every frame has one horizontal 64 x 64 u disc centred on the origin, y = 0.25 + 0.035(N-1) u for new frame N. Only its up face is textured; authoring preview is double-sided. At 16 u per block the square is 4 x 4 blocks.

New frames 2k-1 and 2k both use old ground cell k. Thus the geometry advances every tick while the original ground drawing changes every two ticks. Each ground texture remains 64 x 64 pixels, nearest-neighbour sampled, 16 px per block. Cells 2-8 register their outer ring edge to **28 pixels = 28 u = 1.75 blocks at authored scale 1**. Cell 1 retains its smaller flash registration.

Source cells use local centre (221.5, 221.5). The retained connected art determines each cell's outer radius and is registered around that centre to 28 output pixels. Source alpha below 32 is dropped, components smaller than five source pixels are removed, and isolated single-pixel red noise inside the output ring is removed. Retained strokes, runes, embers and solid marks are mapped to the nearest palette RGB with binary alpha. No ring art is synthesized.

| Ground cell | New frames | Maximum occupied radius (pixels) |
| --- | --- | ---: |
| 1 | 1-2 | 24.052 (unscaled flash) |
| 2 | 3-4 | 28.364 |
| 3 | 5-6 | 27.973 |
| 4 | 7-8 | 27.613 |
| 5 | 9-10 | 27.830 |
| 6 | 11-12 | 28.151 |
| 7 | 13-14 | 27.577 |
| 8 | 15-16 | 27.830 |

Registered rings remain within half a texture pixel of the target. `FLIPBOOKS.md` remains **shrink 2**. Display scale is `2 * trueRadius / 1.75`, including shrink restoration: at a 4.0-block damage radius this is `32/7`, approximately 4.571429. Ground-snap at impact. Runtime cadence must consume all sixteen models at one tick each; radius scaling is unchanged.

## Fireball and in-between rule

The baseline lobe consists of a cube with an overlapping partner yawed 45 degrees, 84% in x/z and 91% in y. Selected lobes have a 76%-size third cube pitched 32 degrees and rolled 15 degrees. The three low central pitched cubes retain their original lifts, placing their transformed bottoms at y = 0.03 u. The accumulated outward rotation composes over those starting orientations. The peak has nine lobes, with a 24 u central white-hot core.

New even frames interpolate neighbouring original poses. Surviving cubes average position and dimensions. Lobe roll advances by half the original phase change; it is composed as a quaternion over the baseline orientation, never by averaging wrapped Euler components. A newly appearing lobe or cube is half the next pose's size at its next centre. A disappearing lobe or cube is half the previous size, moves 0.75 u horizontally outward and 0.5 u upward, and uses one cooler material, clamped at dark smoke. Two small ground lifts and one upper-bound size correction are explicitly listed below.

When neighbouring lobe materials differ, the midpoint uses the cooler one. Material order is `white_hot`, `yellow`, `orange`, `ember_red`, `smoke_grey`, `dark_smoke`. Matched streaks average their positions, dimensions and orientations along their continuing trajectory; disappearing streaks shrink, drift and cool like lobes. Matched embers drift halfway; appearing/disappearing embers grow/shrink at half size. Ember shrink-out retains ember heat. New frame 16 contains the final five embers at half size, drifted outward/upward, over ground cell 8.

Matching follows spatial continuity rather than assuming local element numbers are durable identities. From old frame 2 to 3, crown lobe 4 continues into lobe 5; lobe 4 at the new left crown grows in. From old frame 4 to 5, lobe pairs are 2->1, 5->2, 8->3, 7->4, 6->5; old lobes 1, 3 and 4 shrink out. All other surviving lobe pairs retain their local number. Individual pitch companions may appear/disappear within a continuing cluster. Streaks and embers similarly follow their spatial paths where local numbers change.

| Frame | Tick | Ground cell | Disc y (u) | Lobe clusters | Lobe cubes | Streaks | Embers | Disc | Total | Read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 0 | 1 | 0.250 | 1 | 3 | 5 | 3 | 1 | 12 | Original small flash |
| 2 | 1 | 1 | 0.285 | 4 | 10 | 8 | 6 | 1 | 25 | Half-grown outer lobes |
| 3 | 2 | 2 | 0.320 | 4 | 10 | 8 | 6 | 1 | 25 | Original swelling centre |
| 4 | 3 | 2 | 0.355 | 9 | 21 | 9 | 8 | 1 | 39 | Half-grown peak lobes |
| 5 | 4 | 3 | 0.390 | 9 | 21 | 9 | 8 | 1 | 39 | Original full peak |
| 6 | 5 | 3 | 0.425 | 9 | 21 | 9 | 8 | 1 | 39 | Halfway rising and rolling |
| 7 | 6 | 4 | 0.460 | 8 | 18 | 6 | 8 | 1 | 33 | Original raised fireball |
| 8 | 7 | 4 | 0.495 | 8 | 20 | 6 | 8 | 1 | 35 | Shrinking central mass; separating puffs |
| 9 | 8 | 5 | 0.530 | 5 | 12 | 0 | 8 | 1 | 21 | Original orange-red puffs |
| 10 | 9 | 5 | 0.565 | 5 | 12 | 0 | 9 | 1 | 22 | Cooling and drifting |
| 11 | 10 | 6 | 0.600 | 4 | 10 | 0 | 7 | 1 | 18 | Original grey smoke |
| 12 | 11 | 6 | 0.635 | 4 | 10 | 0 | 8 | 1 | 19 | Halfway smoke breakup |
| 13 | 12 | 7 | 0.670 | 3 | 6 | 0 | 5 | 1 | 12 | Original three smoke puffs |
| 14 | 13 | 7 | 0.705 | 3 | 6 | 0 | 5 | 1 | 12 | Half-size smoke fades |
| 15 | 14 | 8 | 0.740 | 0 | 0 | 0 | 5 | 1 | 6 | Original five embers |
| 16 | 15 | 8 | 0.775 | 0 | 0 | 0 | 5 | 1 | 6 | Half-size drifting embers |

Total: **363 elements**, maximum **39 per frame**, below the 48-element limit. Whole-rig authored bounds over all shown frames: x/z [-32, 32], y [0, 47.999999137] u. The original peak core touches y = 0; no corner is below ground. Reloaded Blockbench mesh bounds agree within float precision. Generated item models fit the shrink-2 box.

## Accumulated outward roll and bounds

For lobe centre `(x,y,z)`, horizontal outward direction is `d = (x,0,z) / sqrt(x*x+z*z)`. The tangent roll axis is `(d.z,0,-d.x)`. Positive roll tips the starting top face outward and down. Compose it before the baseline cube orientation in Blockbench's rest-space ZYX convention. The unyawed prop root follows `SIGNS.md`; neither clip has rotation or position keys. Exactly central lobes do not roll.

| New frame | Off-axis phase |
| --- | ---: |
| 1-3 | 0 degrees |
| 4 | 22.5 degrees |
| 5 | 45 degrees |
| 6 | 67.5 degrees |
| 7 | 90 degrees |
| 8 | 112.5 degrees |
| 9 | 135 degrees |
| 10 | 157.5 degrees |
| 11 | 180 degrees |
| 12 | 202.5 degrees |
| 13 | 225 degrees |
| 14 | 247.5 degrees, shrinking smoke |
| 15-16 | No lobes |

The roll phase never resets when a surviving puff is renumbered. Its outward axis follows the interpolated horizontal centre. Baseline orientations are recovered before composing the new phase, retaining yawed/pitched companion orientations.

Three literal midpoints conflict with the ground/48 u constraints. The delivered bounds corrections affect only new even-frame cubes:

| Frame | Cube | Correction | Uncorrected bound |
| --- | --- | --- | --- |
| 4 | `lobe_2_core` | Lift 0.169281136 u | min y = -0.169280136 u |
| 4 | `lobe_3_core` | Lift 0.277953752 u | min y = -0.277952752 u |
| 12 | `lobe_2_core` | Uniform size multiplier 0.955218838 about unchanged midpoint centre | max y = 48.304722374 u |

These are exceptions to literal midpoint position/size; the OPEN block "Scorch sixteen-frame interpolation versus authored bounds" in `C:/Users/omarz/.claude/comms/orchestrator-inbox.md` recommends retaining them. Shrink remains 2. All original corrections from `049598e` remain untouched: old frame 3's seven floor lifts become new frame 5; old frame 5's core reduction becomes new frame 9; old frame 7's two upper reductions become new frame 13.

## Textures and palette

Fourteen embedded PNGs: eight 64 x 64 ground cells and six 16 x 16 materials, `white_hot`, `yellow`, `orange`, `ember_red`, `smoke_grey`, `dark_smoke`. Stepped contours form an asymmetric curled core, upper highlight rim and split darker underside. Ember-red has charcoal centres. Up faces sample the upper ten rows, down faces the lower eight, and vertical faces the full material. No emissive pairs.

Every visible pixel belongs to this palette, with alpha exclusively 0 or 255:

`#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`

The generator emits 16 item definitions, 16 geometry files and 58 per-frame texture copies: 90 files for this row. The actual generator output is checked byte-for-byte against the row's generated in-memory results.

## Rig and clips

Hierarchy: unyawed `root` -> `fx` -> `frame_1` through `frame_16`. Frames directly own their disc, lobe cubes, streaks and embers.

`burst`: length 0.8 s, hold mode, 20-tps grid. Frame N shows from tick N-1 until tick N. Every frame bone has a step scale key on every tick 0-16: scale 1 only at its own tick, 0.001 otherwise. Every changing segment is one tick. Exactly one frame shows at ticks 0-15; every frame is hidden at tick 16: **the clip ends hidden**.

`hidden`: 1-second loop, every frame bone at 0.001 throughout. Neither clip contains position or rotation keys.

## Verification and renders

Geometry, groups and keyframes were edited through Blockbench's localhost MCP with native Cube, Group and Animation APIs and Undo transactions. The native project codec exported the model without coordinate rounding; group descriptors were folded into the legacy outliner serialization expected by the generator. Geometry was not generated as external model JSON.

The prop preview uses the real saved geometry at `C:/Users/omarz/AppData/Local/Temp/bb-pyro-scorch-16/preview.html`, with the new rig and eight-frame baseline side by side, `--clip burst --chest 0`. `before.html` preserves the initial preview. The scratch reader handles empty bone animators and per-texture UV sizes.

All sixteen poses were rendered in Blockbench from the bystander eye, camera (0,25.6,96) u, target (0,15,0), vertical FOV 50 degrees: 1.6 blocks high, six blocks out, at authored scale before the plugin radius multiplier. The numbered contact sheet and full frame renders were visually inspected.

- `pyro_scorch_explosion_render_contact.png`: sixteen-frame contact sheet.
- `pyro_scorch_explosion_render_frame_05.png` through `_08.png`: the requested full-size peak-to-breakup span.
- `pyro_scorch_explosion_render_burst_end_hidden.png`: burst at tick 16.
- `pyro_scorch_explosion_render_hidden.png`: hidden loop at tick 10.
- `pyro_scorch_explosion_preview.gif`: exactly sixteen 50 ms frames, 20 fps, 0.8-second loop, same bystander eye.

Verification covers original non-disc element equality; identical embedded texture bytes; all rotated corners and reloaded Blockbench world bounds; palette/binary alpha; ground cell pairing and all sixteen stagger heights; element budgets; 17 burst and 21 hidden tick states; one-tick changing segments; sixteen generator spans; all 90 generated files; and GIF frame count/duration. Generator summary: `OK: 16 flipbook(s), 121 frame(s), 456 file(s) written`. The build and source manifest check pass for `dist/LegendCraft-Pack-0.2.4.zip`. The pre-commit drift check detects the new uncommitted output; the required post-commit result is quoted in the handoff report.

The brief overrides the skill's intermediate review stop. `legendcraft-blockbench/SKILL.md` says "the commit and the handoff are all forbidden" before a later owner ruling. `PROP-PREVIEW.md` says "Then the turn ends: the ruling is the next message". These are explicit skill gates; this brief authorizes completing the build, renders, checks and commit in this session. It also overrides the separate authoring-repository push/index workflow: only named pack-branch paths are committed; no push or PR.

No plugin edits or deployment occurred. In-game verification still belongs to the owner: one-tick model swaps across all sixteen frames, display removal at tick 16, 4-block damage-edge alignment, Minecraft lighting and alpha cutout. The bounds-correction OPEN block above remains a disclosed midpoint exception.

## History

2026-09-27: replaced the side-sheet cross with a three-dimensional cube fireball and smoke sequence over registered 64 x 64 ground cells; retained shrink 2 and regenerated item frames.

2026-09-27: `049598e` added accumulated outward lobe roll to `126172b` placements, with ten bounds corrections and unchanged textures/non-lobe elements.

2026-09-28: doubled the eight two-tick frames to sixteen one-tick frames through Blockbench MCP, preserving original odd-frame geometry except requested disc staggering. Added growing/shrinking midpoint lobes, continued roll, cooler midpoint materials, drifted embers and the final ember shrink; three new bounds corrections are disclosed above. Replaced stale renders, added the 20-fps GIF and regenerated the sixteen item frames.
