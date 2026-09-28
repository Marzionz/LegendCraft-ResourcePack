# Conflagration eruption debris

`pyro_conflag_debris` is a BetterModel motion prop spawned at the detonation centre on the ground. Play `erupt` once with HOLD playback and remove it when its 1.75-second clip ends. The plugin scales the prop using **`DEBRIS_REACH_U = 84.725151`**, the measured maximum horizontal piece-centre distance in model units.

## Source and extraction

Bought source: `C:/Repositories/Animation training/samus2002_AWAKENED_PYROMANCER [v1.1]/ModelEngine/blueprints/RPG_Class_Awakened_Pyromancer/Pyro Combo/lava_obsidian_pieces_eruption_vfx.bbmodel`, clip `animation`, 1.75 seconds. Source SHA256: `42cb90162eb898abd162a0449539c4bc77f29e7ac23912cf80ac0f1d20b5bd84`; unchanged after extraction.

The Pyro Combo source is used because its native clip visibly launches three-dimensional lava/obsidian rocks outward, arcs them through the air and lands them around the origin. The Infernal Judgement fallback was unnecessary. The source also contains impact shapes, small flames and a central rising flame effect; those remain because the brief requires the source geometry and bones intact.

The source was copied to scratch and loaded through the Blockbench MCP at `http://localhost:3000/bb-mcp`. Native outliner operations parented the complete source hierarchy under a new identity root. All **66 elements and 73 source bones** retain their UUIDs, coordinates, pivots, rest rotations, UVs, face assignments and hierarchy. No geometry was generated as JSON. The source's untextured hitbox is retained as part of the complete extraction.

## Bones and orientation

74 bones total: new identity `root`, plus all 73 source bones. The original top-level `lava_obsidian_pieces_eruption_vfx` and `hitbox` bones are unchanged children of the new root.

| Source bones | Count |
| --- | ---: |
| `lava_obsidian_pieces_eruption_vfx`, `hitbox` | 2 |
| `allef_impactv1`, `allef_impactv2`, `allef_impact_mini`, `allef_stone_impact`, `allef_stone`, `allef_mini_flame` | 6 |
| `ef_impactv1_1` through `ef_impactv1_5` | 5 |
| `ef_impactv2_1` through `ef_impactv2_4` | 4 |
| `ef_impact_mini_1` through `ef_impact_mini_8` | 8 |
| `ef_stone_impact1` through `ef_stone_impact12` | 12 |
| `ef_stone1` through `ef_stone12` | 12 |
| `ef_mini_flame1` through `ef_mini_flame6` | 6 |
| `group`, `group2` through `group18` | 18 |

The new root has origin and rest rotation `[0,0,0]`, following the skill's `SIGNS.md` unyawed prop-root rule. There is no mob-facing yaw, geometry rotation, pivot relocation, lift or corrective rescale. Source animation rotation and position channels are preserved in native Blockbench format 5.0 and verified through native poses; they are not reinterpreted using legacy 4.x signs. The model includes native groups and expanded outliner metadata for the staging reader.

## Clips

| Clip | Playback | Length | Content |
| --- | --- | --- | --- |
| `erupt` | HOLD | 1.75 s / 35 ticks | Source `animation`, with all 493 source keys and their timing, values, UUIDs and interpolation unchanged. Added whole-prop terminal hiding on the new root. |
| `hidden` | LOOP | 0.05 s / 1 tick | Every one of the 73 source bones has step scale `[0.001,0.001,0.001]` at times 0 and 0.05. |

All source keys were already on the 0.05-second grid; snapping changes none of them. Source linear and Catmull-Rom interpolation are retained. The new root has step scale 1 at time 0 and step scale 0.001 at time 1.75, so the final held frame hides the entire prop without changing any source animation channel. This terminal mask multiplies the source's own end scales; it does not replace individual source keys. The source effects already finish disappearing before the clip endpoint, and the final rendered frame is empty apart from the ground and stand-in.

| Beat | Time / tick | Native visible result |
| --- | --- | --- |
| Start | 0.00 / 0 | Source pieces start hidden. |
| Launch | 0.05-0.30 / 1-6 | Impact shapes and flames rise; rocks travel outward through an arc. |
| Maximum measured reach | 0.45 / 9 | Outermost rock centre reaches 84.725151 u. |
| Grounded debris | 0.60-1.05 / 12-21 | Scattered rocks and impact pieces remain around the origin. |
| Disappearance | 1.20-1.40 / 24-28 | Source scale curves remove the remaining pieces. |
| Held hidden end | 1.75 / 35 | Additional root step mask is 0.001; remove the prop. |

### Reach and plugin sizing

**`DEBRIS_REACH_U = 84.72515061084928`** (use **84.725151 u**). Measurement transforms each element's native geometry bounding-box centre into world/model space and takes `sqrt(x*x + z*z)`. It covers all 66 elements over the full clip at 0.001-second intervals, then refines around the maximum at 0.00001-second intervals. The tick-grid maximum is the same. The largest rock-only result is also the same; a flame or impact plane does not determine the sizing constant.

The maximum occurs at **0.45 s / tick 9**, on element UUID `36f0831a-7d1e-2cea-e7f0-3e6c7312ba5a`, bone `group12`, at centre approximately `[-79.607156, 0.67, -29.000894]` u. This includes the source carrier's authored 1.6 scale and all ancestor transforms. Do not multiply by that 1.6 again.

For a desired field radius `R` in blocks, use model scale `16 * R / 84.725151`. This sizes the farthest piece centre to the field radius; cube corners can extend beyond it. It is a maximum during the entire eruption, not a guarantee that every rock lands on the circumference. Source below-ground geometry remains unchanged.

## Texture

The source-bound 32 x 32 RGBA `lava_obsidian_pieces_eruption_vfx.png` atlas is retained byte-for-byte, embedded and exported as `pyro_conflag_debris.png` beside the model and at `src/assets/legendcraft/textures/entity/pyro_conflag_debris.png`. Resource location: `legendcraft:entity/pyro_conflag_debris`. Atlas SHA1: **`740d78c31a73cf35424ad59fd7899db8232b0e0b`**. No repaint, UV resampling, palette change, alpha change or emissive companion.

## Verification and renders

Verified unchanged source SHA256, all 66 source element UUIDs and geometry fields, all 73 source bone UUIDs and rest transforms, every face UV and texture assignment, all 493 source keyframes including interpolation, exact atlas bytes in all three locations, identity root, clip modes and lengths, tick alignment, hidden scales, terminal mask and staged/source byte equality. Native source poses established the outward trajectory before selecting this source.

The delivered model was reloaded into an isolated Blockbench project before rendering and measuring. Native animated meshes and materials were rendered over mid-grey ground with a 2-block-tall stand-in. The eye-level camera is `(0,25.6,192)` u, looking horizontally at `(0,25.6,0)`, with 80-degree vertical FOV. This is a 12-block viewing distance with a 1.6-block eye height. The native model is not rescaled for the render; the framing includes the tall inherited flame effect.

- [Eye-level contact sheet](pyro_conflag_debris_render_contact.png): 16 poses covering launch, outward flight, landing, disappearance and the held empty endpoint; visually inspected.
- [Full eruption GIF](pyro_conflag_debris_render_erupt.gif): 36 frames at 50 ms each, covering ticks 0-35. The endpoint frame is shown for one tick before the demonstration restarts.

`deploy-rigs.ps1 -Prop` and `-Prop -Preflight` passed. Staged model: `dist/props/models/pyro_conflag_debris.bbmodel`, SHA1 **`a2221ca1213b2f274e7985d2713508ba4983a0d0`**. `build.ps1` and the source-tree manifest check passed: 489 item models, 17 sounds, 5 sounds.json. Plugin-contributed assets were not checked because no plugin source was supplied.

The explicit build brief authorizes the final renders, staging and commit without the skill's intermediate preview pause. This is staging only; no plugin code or live server was changed. In-game BetterModel playback, field-radius sizing, terrain intersection, brightness, alpha sorting and removal at the held endpoint remain hook-time checks.
