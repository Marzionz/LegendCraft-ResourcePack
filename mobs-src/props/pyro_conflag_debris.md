# Conflagration eruption debris

`pyro_conflag_debris` is a BetterModel motion prop spawned on the ground at detonation. Play `erupt` with HOLD playback. It settles into full-size landed debris and remains there until detonation tick 60. Switch directly to `sink` then; remove the prop at tick 72. Use **`DEBRIS_REACH_U = 84.405151`** for sizing the held landed footprint.

## Source, geometry and bones

Bought source: `C:/Repositories/Animation training/samus2002_AWAKENED_PYROMANCER [v1.1]/ModelEngine/blueprints/RPG_Class_Awakened_Pyromancer/Pyro Combo/lava_obsidian_pieces_eruption_vfx.bbmodel`, clip `animation`. Source SHA256: `42cb90162eb898abd162a0449539c4bc77f29e7ac23912cf80ac0f1d20b5bd84`.

All 66 source elements retain their coordinates, pivots, element rotations, UVs and face assignments. The 73 source bones remain beneath the identity `root`, for 74 bones total. **Every bone has rest rotation `[0,0,0]`**. The twelve `ef_stone_impact1` through `ef_stone_impact12` orientations are constant native format-5 animation rotations in `erupt` and `sink`; their source world poses are preserved without relying on bone rest rotations. Element rotations on the beveled rock geometry are retained.

Persistent solids are the twelve thrown cubes (`group`, `group2` through `group12`) and twelve two-element stone/obsidian clusters (`ef_stone_impact1` through `ef_stone_impact12`): 24 independently sinking pieces, 36 elements. The flat impact planes and six mini-flame groups are transient. The untextured source hitbox is retained.

The unchanged 32 x 32 RGBA atlas is embedded and stored as `pyro_conflag_debris.png` beside this file and under `src/assets/legendcraft/textures/entity/`. Resource location `legendcraft:entity/pyro_conflag_debris`; atlas SHA1 **`740d78c31a73cf35424ad59fd7899db8232b0e0b`**. No repaint or emissive companion.

## Clips and timing

| Clip | Playback | Length | Behavior |
| --- | --- | --- | --- |
| `erupt` | HOLD | **1.00 s / 20 ticks** | Preserve source launch, flight, bounces and landing. Hold every solid at full landed size. Transient effects finish hidden; no root hide. |
| `sink` | HOLD | **0.60 s / 12 ticks** | Exact held-pose start; each solid descends vertically by its own landed height while shrinking uniformly from 1 to 0.001 with cubic ease-in. Fully buried last frame holds. |
| `hidden` | LOOP | 0.05 s / 1 tick | Unchanged step scale 0.001 on all 73 source bones at times 0 and 0.05. |

| Pieces / event | Final landing time | Tick |
| --- | --- | --- |
| `group3`, `group6`, `group9`, `group12` | 0.50 s | 10 |
| `group2`, `group5` | 0.55 s | 11 |
| `group11` | 0.60 s | 12 |
| `group8` | 0.70 s | 14 |
| `group`, `group4`, `group7` | 0.75 s | 15 |
| `group10`: all thrown pieces now at rest | **0.85 s** | **17** |
| Last mini flame hidden | 0.95 s | 19 |
| Held clip endpoint | 1.00 s | 20 |
| Plugin swaps to `sink`; field begins cooling | 3.00 s after detonation | 60 |
| Prop removal; field gone | 3.60 s after detonation | 72 |

The stationary obsidian clusters finish their source scale-in by tick 3. Their later shrink keys are removed. Each thrown rock keeps its original rotation and position keys and its scale curve through its individual landing. Later scale keys are replaced by a full-size hold; this also removes the source Catmull-Rom size drift after landing. No root scale mask remains in `erupt`.

## Sink keys

Every sink channel starts from the exact `erupt(1.00)` value. Rotation and all transient channels are held constant. Solids get position and uniform scale samples at every tick, linearly interpolated between samples. With `f=(tick/12)^3`, uniform scale is `q=1-0.999*f` and each solid's world bounding-box centre is `C(t)=C(0)-[0,H*f,0]`, where H is its landed world height. The source ancestor scale (1.6, or 1.76 for the obsidian clusters) is already included in H.

| Tick | Seconds | Downward fraction f | Uniform scale q |
| --- | --- | --- | --- |
| 0 | 0.00 | 0.000000000 | 1.000000000 |
| 1 | 0.05 | 0.000578704 | 0.999421875 |
| 2 | 0.10 | 0.004629630 | 0.995375000 |
| 3 | 0.15 | 0.015625000 | 0.984390625 |
| 4 | 0.20 | 0.037037037 | 0.963000000 |
| 5 | 0.25 | 0.072337963 | 0.927734375 |
| 6 | 0.30 | 0.125000000 | 0.875125000 |
| 7 | 0.35 | 0.198495370 | 0.801703125 |
| 8 | 0.40 | 0.296296296 | 0.704000000 |
| 9 | 0.45 | 0.421875000 | 0.578546875 |
| 10 | 0.50 | 0.578703704 | 0.421875000 |
| 11 | 0.55 | 0.770254630 | 0.230515625 |
| 12 | 0.60 | 1.000000000 | 0.001000000 |

The following position vectors are native keyframe values. Each intermediate key is `P0 + f*(P12-P0)`. Off-centre clusters include horizontal compensation for shrinking about their source pivot, so their world centres move straight down. Positions and heights below are rounded for reading; the `.bbmodel` contains full precision.

| Solid bone | World height H (u) | Position at tick 0 | Position at tick 12 |
| --- | --- | --- | --- |
| `ef_stone_impact1` | 15.557503938 | `[0.000000, 0.000000, 0.000000]` | `[-0.000168, -6.259797, -5.707938]` |
| `ef_stone_impact2` | 17.313482884 | `[0.000000, 0.000000, 0.000000]` | `[-1.987281, -6.885624, -4.082620]` |
| `ef_stone_impact3` | 17.717374032 | `[0.000000, 0.000000, 0.000000]` | `[-5.223449, -7.515509, 0.002203]` |
| `ef_stone_impact4` | 21.792256722 | `[0.000000, 0.000000, 0.000000]` | `[-2.995181, -7.990548, -1.432509]` |
| `ef_stone_impact5` | 21.720918519 | `[0.000000, 0.000000, 0.000000]` | `[-2.404465, -7.378630, 1.922513]` |
| `ef_stone_impact6` | 15.059004571 | `[0.000000, 0.000000, 0.000000]` | `[-0.002293, -6.849008, 5.859952]` |
| `ef_stone_impact7` | 16.276629392 | `[0.000000, 0.000000, 0.000000]` | `[-2.143129, -6.468084, 4.161189]` |
| `ef_stone_impact8` | 14.418801434 | `[0.000000, 0.000000, 0.000000]` | `[5.882186, -5.458449, -0.002597]` |
| `ef_stone_impact9` | 17.469095394 | `[0.000000, 0.000000, 0.000000]` | `[4.457735, -7.028107, -1.538536]` |
| `ef_stone_impact10` | 19.835051278 | `[0.000000, 0.000000, 0.000000]` | `[1.735259, -6.947603, -3.544686]` |
| `ef_stone_impact11` | 15.392217514 | `[0.000000, 0.000000, 0.000000]` | `[2.464557, -6.022459, 4.097109]` |
| `ef_stone_impact12` | 19.690840435 | `[0.000000, 0.000000, 0.000000]` | `[3.953886, -7.870807, 2.216201]` |
| `group` | 8.792402869 | `[0.000000, 0.000000, -32.600000]` | `[-0.000000, -5.495252, -32.600000]` |
| `group2` | 8.603011436 | `[0.000000, 0.000000, -43.900000]` | `[-0.000000, -5.376882, -43.900000]` |
| `group3` | 10.452503719 | `[0.000000, -0.300000, -52.400000]` | `[-0.000000, -6.832815, -52.400000]` |
| `group4` | 8.792402869 | `[0.000000, 0.000000, -32.600000]` | `[-0.000000, -5.495252, -32.600000]` |
| `group5` | 8.603011436 | `[0.000000, 0.000000, -43.900000]` | `[-0.000000, -5.376882, -43.900000]` |
| `group6` | 10.452503719 | `[0.000000, -0.300000, -52.400000]` | `[0.000000, -6.832815, -52.400000]` |
| `group7` | 8.792402869 | `[0.000000, 0.000000, -32.600000]` | `[-0.000000, -5.495252, -32.600000]` |
| `group8` | 8.603011436 | `[0.000000, 0.000000, -43.900000]` | `[-0.000000, -5.376882, -43.900000]` |
| `group9` | 10.452503719 | `[0.000000, -0.300000, -52.400000]` | `[-0.000000, -6.832815, -52.400000]` |
| `group10` | 8.792402869 | `[0.000000, 0.000000, -32.600000]` | `[0.000000, -5.495252, -32.600000]` |
| `group11` | 8.603011436 | `[0.000000, 0.000000, -43.900000]` | `[0.000000, -5.376882, -43.900000]` |
| `group12` | 10.452503719 | `[0.000000, -0.300000, -52.400000]` | `[0.000000, -6.832815, -52.400000]` |

At the last frame, all 24 solid scales are 0.001 and their native world bounds are entirely below y=0. Transient effects stay hidden throughout `sink`; they do not replay.

## Reach and plugin sizing

**`DEBRIS_REACH_U = 84.40515062447152`**, use **`84.405151`**. This is the maximum horizontal element-centre radius at the held landed pose, measured from native Blockbench world transforms. It is **0.320000 u smaller than 84.725151**, which described the transient flight maximum. The launch curve still reaches that earlier transient radius.

The held maximum is element `36f0831a-7d1e-2cea-e7f0-3e6c7312ba5a`, bone `group12`, centre `[-79.306454513,1.920000000,-28.891447256]` u. For a desired landed radius R blocks, use `modelScale = 16*R/84.405151`. Do not multiply by the source 1.6 scale again. Cube corners can extend beyond the centre-based radius; source ground intersection is preserved.

## Verification and renders

Saved models were reloaded into isolated Blockbench projects. Native source/deliverable world matrices were compared at 0.01-second intervals: each thrown rock matches through its own landing, and all other source elements match through the checked 1.00-second interval. Only the intended post-landing size holds differ. All 74 bone rest rotations are zero. Tick alignment, clip bounds, unique key UUIDs, original atlas bytes and source/stage byte equality passed.

`erupt(1.00)` and `sink(0)` world matrices match exactly (maximum error 0). Thrown-rock centre motion follows the specified vertical sink within 1.5e-14 u. All solids end below ground at scale 0.001.

Native Blockbench geometry, UVs and animated world matrices supply the renders, with unlit texture materials, grey ground and a 2-block stand-in. The eye-level camera is `(0,25.6,192)` u looking horizontally at `(0,25.6,0)`, FOV 80 degrees. Geometry is not rescaled to fit the camera.

- [Eye-level erupt, hold to tick 60, then sink GIF](pyro_conflag_debris_render_erupt.gif), 50 ms per frame; 73 frames cover ticks 0-72
- [Held landed pose](pyro_conflag_debris_render_landed.png)
- [Motion contact sheet](pyro_conflag_debris_render_contact.png)

The stills and contact sheets were visually inspected. `deploy-rigs.ps1 -Prop` and `-Prop -Preflight`: **DEPLOYABLE**. Staged `dist/props/models/pyro_conflag_debris.bbmodel` SHA1 **`8a35299b9deb8ebe7c7d03229a5e40dd98c68adb`**. `build.ps1` and `check_pack_manifest.py --pack dist/LegendCraft-Pack-0.2.4.zip --source-tree src` passed: 490 item models, 17 sounds, 5 sounds.json. Plugin-contributed assets are unchecked because no plugin source was supplied.

The plugin must swap clips at tick 60 and remove at tick 72 without crossfading or restarting the launch. BetterModel playback, terrain intersection, brightness and alpha sorting remain in-game checks. This asset work does not implement those plugin changes or deploy to a server.
