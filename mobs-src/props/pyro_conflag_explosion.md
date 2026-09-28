# Conflagration rolling block detonation

Conflagration's ultimate begins as a small white flash and rune-shard burst, then releases a much larger shell of fire blocks. Its lobes roll outward as they expand and break into red fragments, followed by falling embers and smoke. One detonation covers an 8-block radius, increasing to 12 at Level 60.

The source is `pyro_shell_detonation.bbmodel` at `025a565d5a98a2f7d4af471513e08e503132e178`. All 555 elements, thirteen embedded textures, bones, placements, dimensions, materials and clip timing were copied through Blockbench. Only 156 off-axis lobe cube rotations differ. Ember Shell is unchanged. The former Conflagration fireball remains in git history at `b44a84c`.

This is an item-model flipbook source, not a BetterModel deployment. Runtime swaps `legendcraft:classes/pyro_conflag_explosion_1` through `_16` on one display, one per tick, then removes it at tick 16. The existing `FLIPBOOKS.md` row remains `pyro_conflag_explosion | pyro_conflag_explosion | detonate | 4`.

## Outward roll

Scorch's lobe recipe is preserved: a full cube and an overlapping 45-degree-yaw companion at 84% x/z and 91% y size. Two outer clusters also carry a 76%-size companion with 32-degree pitch and 15-degree roll. The source's baseline radial orientation stays beneath the accumulated roll.

For cluster centre `(x,y,z)`, set `d = (x,0,z)/sqrt(x*x+z*z)` and tangent axis `(d.z,0,-d.x)`. Compose `qRoll * qBaseline` in Blockbench rest-space ZYX order. Positive rotation tips the top outward and down. No Euler components are averaged. Every member of a cluster receives the same quaternion roll about its shared centre.

The twelve off-axis shell clusters begin at phase 0 on their first appearance, frame 6, then accumulate exactly 22.5 degrees per frame through frame 12. The phase is tied to the clip frame, not a local lobe number, so renumbering cannot reset it. The two vertical-axis lobes and central cores do not roll. Flash, rays, rune shards, edge glyphs, ring, embers and smoke remain unchanged.

## Registration and bounds

The authored centre `(0,0,0)` is the burst centre. No ground-snap, lift or recentering was applied. At frame 9 the lobe shell reaches a radial maximum of exactly **28 u = 1.75 blocks at scale 1**. The unrolled vertical lobes retain +/-28 u reach; horizontal lobes tumble within that envelope, and the source's chest-height ring retains x/z +/-28 u. The full peak's reloaded Blockbench mesh bounds are exactly `[-28,-28,-28]` to `[28,28,28]` u.

Runtime places the burst centre and applies `blastRadius / 1.75`, with shrink 4 restored once. Total item-display scale is `4 * blastRadius / 1.75`: approximately 18.285714 at radius 8, or 27.428571 at radius 12. Authoring renders use scale 1 and centre height 1.2 blocks.

All shown geometry stays inside the source envelope: x/z `[-28,28]`, y `[-28.6,28]` u. The lower frame-10 extent is inherited falling breakup. Every peak lobe corner remains within the 28-u sphere. **Bounds corrections: none.** All element positions, dimensions and origins are exactly the source's; only the specified rotations changed.

## Per-frame contract

| Frame | Visible ticks | Elements | Off-axis roll | Read |
| --- | --- | ---: | ---: | --- |
| 1 | 0-1 | 22 | No shell lobes | Small white flash, rays and cyan flecks |
| 2 | 1-2 | 22 | No shell lobes | Larger flash and longer rays |
| 3 | 2-3 | 39 | No shell lobes | Ten rune shards emerge |
| 4 | 3-4 | 39 | No shell lobes | Shards spread and taper |
| 5 | 4-5 | 39 | No shell lobes | Wide shards, shrinking white core |
| 6 | 5-6 | 45 | 0 degrees | Fourteen yellow shell lobes appear |
| 7 | 6-7 | 46 | 22.5 degrees | Expanding rolling shell; ring appears |
| 8 | 7-8 | 46 | 45 degrees | Orange lobes approach full reach |
| 9 | 8-9 | 46 | 67.5 degrees | Peak 28-u shell and ring |
| 10 | 9-10 | 48 | 90 degrees | Red breakup, five bright embers |
| 11 | 10-11 | 48 | 112.5 degrees | Smaller red fragments, ring persists |
| 12 | 11-12 | 48 | 135 degrees | Last lobe fragments, six embers |
| 13 | 12-13 | 20 | No lobes | Eleven falling embers, three smoke wisps |
| 14 | 13-14 | 20 | No lobes | Lower embers, thinner wisps |
| 15 | 14-15 | 20 | No lobes | Last sparks and smoke |
| 16 | 15-16 | 7 | No lobes | Seven low embers |

Total: **555 elements**, maximum **48 per frame**. Frames 6-12 each have fourteen clusters / thirty lobe cubes; twelve clusters / twenty-six cubes are off-axis. Frame 6 preserves their baseline; 26 cubes in each of frames 7-12 receive the new rotation.

Hierarchy is unyawed identity `root -> fx -> frame_1 ... frame_16`. The unyawed prop convention in `SIGNS.md` applies. No rotation or position animation channels were added.

`detonate` is 0.8 seconds / sixteen ticks, hold mode. Each frame bone has a step scale key at every tick 0-16: scale 1 only at tick N-1 for frame N, and 0.001 otherwise. Every changing segment is one tick. At tick 16 all frames are hidden; **ENDS HIDDEN**. `hidden` remains a one-second loop with all frame bones at 0.001 on every tick 0-20.

## Textures

All thirteen embedded 16 x 16 PNGs retain the source bytes. Editable copies are `pyro_conflag_explosion_texture_*.png`. Materials are white-hot, yellow, orange, ember-red, smoke-grey, dark-smoke, cyan fleck, cutout reach ring, four rune bands and flash-white. Alpha is binary. Cyan stays confined to the first two flash frames. The ring has only its up face textured and appears in frames 7-11.

The obsolete fireball texture set and obsolete generated texture copies were removed by explicit path. The concept reference images remain as history.

## Verification and renders

Geometry was edited through native Blockbench APIs over `http://localhost:3000/bb-mcp`, inside an Undo transaction. Native project-codec output was serialized with group descriptors folded into the pack tooling's inline outliner form. No external script generated geometry JSON.

The prop-preview loop has `before.html` and the final real-model `preview.html` in `C:/Users/omarz/AppData/Local/Temp/bb-conflag-r2/`. The final saved model was independently reloaded into Blockbench before rendering. Render-only scene dressing does not enter the rig: mid-grey ground, dark sky, camera at world `(0,1.6,6)` blocks, burst centre `(0,1.2,0)`, 50-degree vertical FOV. The second view uses `(6,1.6,0)`, exactly 90 degrees around.

- `pyro_conflag_explosion_render_contact.png`: sixteen numbered frames, visually inspected.
- `pyro_conflag_explosion_render_detonate.gif`: sixteen 50-ms frames, 20 fps, 0.8-second loop.
- `pyro_conflag_explosion_render_frame_09_side.png`: second-side frame 9, visually inspected.
- `pyro_conflag_explosion_render_end_hidden.png`: detonate at tick 16.
- `pyro_conflag_explosion_render_hidden.png`: hidden loop at tick 10.

Verification confirms source equality to its committed JSON; unchanged non-lobe elements, textures, bones and clip data (apart from editor selection state); exactly 156 rotation-only element changes; independent rotation-matrix agreement with quaternion composition; all transformed corner bounds; reloaded Blockbench peak bounds; every one-tick show/hide span; and sixteen 50-ms GIF frames. All **97** generated outputs for this row are byte-identical to the generator's in-memory result: sixteen definitions, sixteen geometry models and 65 textures.

`python tools/gen-flipbook-frames.py`: `OK: 20 flipbook(s), 215 frame(s), 1554 file(s) written`.

`build.ps1`: built `dist/LegendCraft-Pack-0.2.4.zip`, pack format 88. Manifest check: `OK: LegendCraft-Pack-0.2.4.zip carries 439 item model(s), 12 sound(s), 3 sounds.json`. Plugin-contributed assets were unchecked because no plugin source is part of this task. The pre-commit drift gate reported 440 generated changes relative to the former build; the required post-commit output is quoted in the handoff report.

The brief overrides `legendcraft-blockbench/SKILL.md`'s explicit requirement that "the commit and the handoff are all forbidden" before a subsequent owner ruling, and `PROP-PREVIEW.md`'s "Then the turn ends: the ruling is the next message". This session was explicitly authorized to complete the renders and one worktree commit. The skill's separate model-repository push workflow is also overridden. No push, PR, plugin edit or deployment occurred.

Remaining in-game checks: runtime centre placement, single shrink restoration, 8/12-block reach, one-tick model cadence, removal at tick 16, Minecraft lighting and ring cutout. No unanswered asset decision required an OPEN block.

## History

2026-09-28: Replaced the former `b44a84c` fireball with Ember Shell's sixteen-frame block detonation and Scorch-style accumulated outward lobe roll. Preserved source registration and timing; regenerated item models and replaced renders.
