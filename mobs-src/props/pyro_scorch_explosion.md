# Scorch land explosion

Scorch's meteor bursts where it stops, damaging enemies within 4.0 blocks and applying a Burning stack. A block-ish 3D fireball rises above the approved 2D ground ring for 16 ticks: eight frames, two ticks each. The ring communicates the damage edge.

This frame-stack rig is the input to `tools/gen-flipbook-frames.py` and the prop preview. Runtime uses ONE item display swapping `legendcraft:classes/pyro_scorch_explosion_1` through `_8`. The rig is never deployed to BetterModel.

## Sources

- `pyro_scorch_explosion_concept_ground.png`: approved 1774 x 887 RGBA sheet, eight cells in a 4 x 2 grid. The disc uses this drawing, including the diamond, square, cross and hooked runes.
- `pyro_scorch_explosion_concept_side.png`: 1774 x 887 RGBA sheet, reference for the fireball's silhouette, heat progression and timing only. It is not a texture.
- Craft reference: Unending Blows `src/assets/legendcraft/textures/item/flurrybwl/strike_*.png` and `impact_*.png`: narrow shaded strokes, hot heads, dark tails and empty space.

The earlier crossed side-sheet build and its renders are superseded.

## Ground disc and radius contract

Each frame has one horizontal 64 x 64 u disc, centred on the origin at y = 0.25 + 0.035(N-1) u. At 16 u per block, its square is 4 x 4 blocks. Only the up face is textured; the authoring texture uses double-sided preview rendering. The generated ground surface faces up.

Every disc texture is 64 x 64 pixels, nearest-neighbour sampled: 16 px per block. Frames 2-8 register their outer ring edge to radius **28 pixels = 28 u = 1.75 blocks at authored scale 1**. This is the plugin's radius contract. Frame 1 keeps its own smaller flash size.

Source cells use local centre (221.5, 221.5). Retained connected art determines each frame's outer radius; the registration scales around that centre to 28 output pixels. Source alpha below 32 is dropped, components smaller than five source pixels are removed, and isolated single-pixel red noise inside the output ring is removed. Retained strokes, runes, embers and solid marks are mapped to the nearest palette RGB; output alpha is exclusively 0 or 255. No ring artwork is synthesized. Nearest-neighbour rasterization leaves these maximum occupied pixel-centre radii:

| Frame | Radius (pixels) |
| --- | ---: |
| 1 | 24.052 (unscaled flash registration) |
| 2 | 28.364 |
| 3 | 27.973 |
| 4 | 27.613 |
| 5 | 27.830 |
| 6 | 28.151 |
| 7 | 27.577 |
| 8 | 27.830 |

All registered rings are within half a texture pixel of the target. The disc heights are 0.250, 0.285, 0.320, 0.355, 0.390, 0.425, 0.460 and 0.495 u.

`FLIPBOOKS.md` remains **shrink 2**. Display scale must be `2 * trueRadius / 1.75`, including shrink restoration. At a 4.0-block damage radius this is `32/7`, approximately 4.571429. Ground-snap at impact; remove the display at tick 16. No plugin constant change is needed.

## Fireball recipe

Each lobe starts with an axis-aligned cube and an overlapping cube yawed 45 degrees, sized to 84% in x/z and 91% in y. Selected lobes add a 76%-size cube pitched 32 degrees and rolled 15 degrees. The three low central pitched cubes retain their original lifts to keep their transformed bottom at y = 0.03 u. The outward roll described below composes over these starting orientations. Cube surfaces overlap without identical coplanar faces inside a cluster.

The peak has nine lobes. Its largest central white-hot core is 24 u across, with cooler lobes around and behind it. All lobe placements follow commit `126172b`, with only the individual bounds corrections listed below. Frame 1's single nested lobe measures approximately 0.60 blocks across. Frame 4 lifts the cloud clear of the ground. Frames 5-6 separate into drifting puffs, frame 7 leaves three small smoke puffs, and frame 8 retains only five ember cubes above the disc.

Angled streak cubes are 1-1.5 u thick and 5-10 u long; they use narrow vertical texture strips with a hot upper end and darker tail. Small rotated ember cubes punctuate the surrounding empty space. Streaks occur only in frames 1-4; later frames carry isolated embers.

| Frame | Ticks | Lobe clusters | Lobe cubes | Streaks | Embers | Disc | Total elements | Read |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 0-1 | 1 | 3 | 5 | 3 | 1 | 12 | Small white-hot flash |
| 2 | 2-3 | 4 | 10 | 8 | 6 | 1 | 25 | Swelling white/yellow centre and orange crown |
| 3 | 4-5 | 9 | 21 | 9 | 8 | 1 | 39 | Full billowing peak, hottest in the middle |
| 4 | 6-7 | 8 | 18 | 6 | 8 | 1 | 33 | Raised tearing lobes, darker outer edges |
| 5 | 8-9 | 5 | 12 | 0 | 8 | 1 | 21 | Separated orange-red puffs with dark cores |
| 6 | 10-11 | 4 | 10 | 0 | 7 | 1 | 18 | Grey smoke, dark lower puffs and embers |
| 7 | 12-13 | 3 | 6 | 0 | 5 | 1 | 12 | Three small smoke puffs |
| 8 | 14-15 | 0 | 0 | 0 | 5 | 1 | 6 | Last ember cubes above the cooling ring |

Total: 166 elements, maximum 39 per frame against a 48-element limit. Every rotated corner fits the authored [-32, 64] constraint and the generated item box at shrink 2. Whole-rig world bounds across all shown frames: x/z [-32, 32], y [0, 47.999999137] u. After shrink and item-centre translation, y remains below the item limit of 32.

## Accumulated outward roll

The owner requested the original fireball placements with outward rolling lobes, without the rejected central mushroom-cloud arrangement. Only 61 lobe cube rotations change from `126172b`, plus the ten bounds corrections below. Disc, streak and ember geometry, every material, frame membership, lobe count, hierarchy and both clips are unchanged. Frame 1 and all lobes exactly on the vertical centre axis do not roll.

For a lobe centre `(x, y, z)`, horizontal outward direction is `d = (x, 0, z) / sqrt(x*x + z*z)`. Its horizontal tangent roll axis is `(d.z, 0, -d.x)`. Positive roll tips the initial top face toward `d`, outward and down. Compose this roll before the baseline cube orientation in Blockbench's rest-space ZYX Euler convention; do not add Euler components independently. The core, its 45-degree-yawed partner and any pitched third receive the same rigid roll about the lobe centre. This uses the unyawed prop convention in `SIGNS.md`; it introduces no animation rotation keys.

| Frame | Accumulated outward roll |
| --- | ---: |
| 1 | 0 degrees; central flash |
| 2 | 0 degrees; starting phase |
| 3 | 45 degrees |
| 4 | 90 degrees |
| 5 | 135 degrees |
| 6 | 180 degrees |
| 7 | 225 degrees; remaining smoke lobes |
| 8 | No lobes |

All off-axis lobes share this frame phase, including lobes first exposed at the peak. Surviving puffs keep the accumulated phase when their local lobe numbers change in later frames; the roll never resets. Direction follows each frame's original horizontal centre.

Bounds corrections are the only changes to positions or sizes. Ground lifts preserve cube size and move `from`, `to` and `origin` together. Uniform reductions preserve the original centre. The three upper reductions keep shrink 2: the generated item box imposes authored y <= 48 u, tighter than the general 64 u ceiling. Each correction leaves approximately 0.000001 u clearance.

| Frame | Cube | Correction |
| --- | --- | --- |
| 3 | `lobe_2_core` | Lift 0.606602718 u |
| 3 | `lobe_2_yaw` | Lift 1.126004837 u |
| 3 | `lobe_3_core` | Lift 0.606602718 u |
| 3 | `lobe_3_yaw` | Lift 1.126004837 u |
| 3 | `lobe_7_core` | Lift 3.772500907 u |
| 3 | `lobe_7_yaw` | Lift 0.665798855 u |
| 3 | `lobe_8_core` | Lift 1.475500895 u |
| 5 | `lobe_2_core` | Uniform size multiplier 0.989197106 |
| 7 | `lobe_2_core` | Uniform size multiplier 0.680917505 |
| 7 | `lobe_2_yaw` | Uniform size multiplier 0.783105699 |

## Textures and palette

Fourteen embedded PNGs: eight 64 x 64 ground cells and six hand-composed 16 x 16 heat materials: `white_hot`, `yellow`, `orange`, `ember_red`, `smoke_grey`, `dark_smoke`. Stepped pixel contours form an asymmetric curled core, an upper highlight rim, and split darker underside. Ember-red materials have charcoal centres. Up faces sample the upper ten rows, down faces the lower eight, and vertical faces the full material; every cube face has multiple painted colours. Materials are reused across lobes and frames. There are no emissive pairs.

Every visible texture pixel belongs to this exact palette, with binary cutout alpha:

`#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`

The generator emits eight item definitions, eight geometry files, and 29 per-frame texture copies (45 files total). For the roll change, only geometry files 3-7 differ; all definitions, texture copies and geometry files 1, 2 and 8 remain identical.

## Rig and clips

Hierarchy: unyawed `root` -> `fx` -> `frame_1` through `frame_8`. Each frame owns its disc, cube clusters, streaks and embers directly. This follows the unyawed prop convention in `SIGNS.md`; neither clip has position or rotation keys.

`burst`: 0.8 seconds, hold mode, 20-tps grid. Frame N shows at tick 2(N-1), remains for two ticks, and hides at tick 2N. Scale 1 is shown, 0.001 hidden, with step interpolation. Every changing segment has a holding key one tick before the change. Exactly one frame shows at ticks 0-15. Every frame has a hidden key at tick 16: **the clip ends hidden**.

`hidden`: 1-second loop, all frame bones at 0.001 throughout.

## Verification and renders

Geometry, bone creation and keyframes were authored inside Blockbench through its localhost MCP using native Cube, Group and Animation APIs, with Undo transactions. Blockbench's project codec exported the rig; its group serialization was folded into the legacy outliner layout the flipbook generator reads. Geometry was not generated as external model JSON.

The prop preview was regenerated from the saved rig with `--clip burst --chest 0` at `C:/Users/omarz/AppData/Local/Temp/bb-pyro-scorch-roll/preview.html`; `before.html` preserves the baseline preview. The scratch preview reader tolerates empty bone animators and normalizes each texture's UV size. The final Blockbench pass rendered all eight frames, frames 3-6 from the same second side 90 degrees around, and frames 3 and 6 straight down. The codec used raw export to preserve exact baseline coordinates without decimal rounding. Saved geometry was reloaded into Blockbench for world-bounds verification.

- `pyro_scorch_explosion_render_frame_01.png` through `_08.png`: perspective bystander eye at (0, 25.6, 96) u, 1.6 blocks high and 6 blocks out; target (0, 15, 0), vertical FOV 50 degrees.
- `_frame_03_side.png` through `_frame_06_side.png`: same eye height and distance, camera (96, 25.6, 0).
- `_roll_frames_03_06.png`: these four side views in one horizontal sheet, labelled 45, 90, 135 and 180 degrees accumulated roll.
- `_frame_03_top.png`, `_frame_06_top.png`: camera above the origin at 112 u.
- `_contact.png`: all eight bystander views on a neutral background.
- `_burst_end_hidden.png`, `_hidden.png`: hidden end and hidden loop verification.

Checks passed: element budgets and face coverage; every rotated corner; nearest-neighbour ground dimensions; palette and binary alpha; all 17 tick states; one-tick changing segments; hidden loop; all 45 generated files byte-for-byte against the current rig. `python tools/gen-flipbook-frames.py` reports 16 flipbooks, 113 frames and 411 files written. The pack build and source manifest check passed for `dist/LegendCraft-Pack-0.2.4.zip`. Post-commit drift output is recorded in the handoff report.

The brief explicitly overrides the skill's intermediate review stop. `legendcraft-blockbench/SKILL.md` says: "the commit and the handoff are all forbidden" before a later owner ruling. `PROP-PREVIEW.md` says: "Then the turn ends: the ruling is the next message". Those are explicit skill gates; this brief instead authorizes completing the build, renders, checks and commit in this session. It also overrides the skill's separate authoring-repository push/index workflow: only the named pack-branch paths are committed, with no push.

No in-game deployment or plugin edit was performed. Human checks still owed: the 4-block damage-edge alignment at runtime scale, lighting and alpha cutout in Minecraft, and the two-tick item-model swaps ending with display removal. Preview and renders show authored scale, before the plugin's radius multiplier.

## History

2026-09-27: replaced the superseded side-sheet cross with a three-dimensional cube fireball and smoke sequence over registered 64 x 64 ground cells. Preserved the names, frame hierarchy, clips and shrink-2 runtime contract; replaced all renders and regenerated the item-model flipbook.

2026-09-27: added accumulated outward lobe roll to the `126172b` placements through Blockbench MCP. Preserved all non-lobe elements and textures exactly, made the ten listed bounds corrections, replaced the renders, added the frames 3-6 roll sheet and regenerated the item frames.
