# Ember Shell block detonation

`pyro_shell_detonation` is the Level 60 payoff when Ember Shell is broken, spending its last shield point. It plants two Burning stacks on enemies within five blocks. An expired shell gutters out using the separate wrap rig; it does not detonate.

This rig is the authoring source for an item-model flipbook, not a BetterModel deployment. One item display swaps `legendcraft:classes/pyro_shell_detonation_1` through `_16`, one per tick, and is removed at tick 16. The burst is centred at the caster's chest. Its authored centre is (0,0,0); the runtime supplies chest placement. Preview chest placement is 1.2 blocks above the feet. Never ground-snap this burst.

## Shape and reach

Approved Ember Shell concept panels 2-8 are interpreted as a three-dimensional block burst: a white star with thin rays and cyan flecks; carved, tapering rune shards; an expanding shell of shaded fire lobes with edge glyph cubes; red cooling breakup; falling embers and three slender smoke wisps; final low embers. Every frame is distinct geometry.

The Scorch lobe recipe is retained: a full cube and an overlapping partner at 45-degree yaw, 84% in x/z and 91% in y. Two outer clusters and the early core have a third cube at 76% size, pitched 32 degrees and rolled 15 degrees. Fourteen outer lobe clusters cover the six axial and eight diagonal directions. The peak lobe size is 14.5 u. Each cluster is oriented so one core-cube corner points along its radial direction; its centre sits at radius minus half the cube diagonal. The companion rotations compose inside that cluster orientation, retaining the Scorch recipe. This keeps every lobe corner inside the reach sphere. Rune shards comprise three overlapping tapered cuboids with a block-glyph band. Four edge glyphs each use three solid cubes.

At frame 9 the outer lobe shell reaches **-28 to +28 u on x, y and z**, or **1.75 blocks from the burst centre at scale 1**, in all six axial directions. This is a faceted cube silhouette, not a mathematically smooth sphere. Reloaded Blockbench world bounds confirm exactly +/-28 u on all three axes. A separate transformed-corner check gives maximum peak lobe radius 28.000000000000004 u, within floating-point precision of 28. From frames 7 through 11, a thin horizontal 56 x 56 u rune-banded ring plane at y=0 marks the chest-height reach. Only its up face is textured; binary-cutout texture shows the circular band and clears the centre. The ring already marks full reach while the lobe shell expands to it at frame 9.

`FLIPBOOKS.md` retains **shrink 4**. The radius multiplier for authored geometry is `5.0 / 1.75 = 20/7`. Generated item geometry additionally needs shrink restoration: total item-display scale is `4 * 5.0 / 1.75 = 80/7`, approximately 11.428571, unless the runtime already restores shrink separately. An OPEN block in `C:/Users/omarz/.claude/comms/orchestrator-inbox.md` asks the hook owner to confirm where that restoration occurs. No plugin source was read or changed.

All transformed geometry fits inside x/z [-28,28] and y [-28.6,28] u. The slightly lower frame-10 extent comes from falling breakup after peak. These bounds comfortably fit the requested shrink-4 authored box [-64,128] u; the generator also verifies its actual item-model box. Negative y is intentional for a chest-centred air burst.

## Frame table

| Frame | Tick | Elements | Ring | Read |
| --- | ---: | ---: | --- | --- |
| 1 | 0 | 22 | No | Small white flash, fourteen rays, five cyan flecks |
| 2 | 1 | 22 | No | Larger flash and longer rays, cyan flecks |
| 3 | 2 | 39 | No | Ten rune shards emerge from white-hot core |
| 4 | 3 | 39 | No | Shards move outward and taper |
| 5 | 4 | 39 | No | Widely separated shards, shrinking hot core |
| 6 | 5 | 45 | No | Fourteen yellow fire lobes form the shell |
| 7 | 6 | 46 | Yes | Shell expands; full-reach ring appears |
| 8 | 7 | 46 | Yes | Orange lobe shell approaches its edge |
| 9 | 8 | 46 | Yes | Peak: 1.75-block axial reach |
| 10 | 9 | 48 | Yes | Red lobe breakup and five bright embers |
| 11 | 10 | 48 | Yes | Smaller red lobes and five embers |
| 12 | 11 | 48 | No | Last lobe fragments, six embers |
| 13 | 12 | 20 | No | Eleven falling embers and three three-piece smoke wisps |
| 14 | 13 | 20 | No | Lower embers, thinner dark wisps |
| 15 | 14 | 20 | No | Last falling sparks and smoke |
| 16 | 15 | 7 | No | Seven low embers |

Total: **555 elements**, maximum **48 per frame**.

## Bones and timing

Unyawed identity `root` -> `fx` -> `frame_1` through `frame_16`. Frame bones own their cubes directly. `SIGNS.md`'s unyawed prop convention applies. There are no rotation or position animation channels; all placement and orientation are resting geometry.

`detonate`: 16 ticks, 0.8 seconds, hold mode. Frame N shows from tick N-1 to tick N. Each frame bone has a step scale key at every tick 0-16: 1 at its own tick, 0.001 at every other tick. Every changing segment is exactly one tick. At tick 16 every frame is hidden, and the clip holds hidden.

`hidden`: 20 ticks, one-second loop. Every frame stays at 0.001 with a key every tick. This stack is only for preview and generator consumption. Runtime plays the generated models on one display; do not send this scale-step sequence to BetterModel.

## Texture craft

Thirteen embedded 16 x 16 textures, also editable as `pyro_shell_detonation_texture_*.png`: six Scorch materials (`white_hot`, `yellow`, `orange`, `ember_red`, `smoke_grey`, `dark_smoke`), a brighter shaded `flash_white` variant, `cyan_fleck`, the cutout `reach_ring`, and four blocky rune-band glyphs (cross, diamond, boxed square, hooked stroke). Scorch's materials retain their curled shaded cores, bright rim and darker underside; up faces sample the upper ten rows, down faces the lower eight and vertical faces the whole tile. The white flash variant shifts the warm ramp up one value step. No flat-fill material substitutes for the lobe shading.

Every visible pixel uses only `#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`, plus `#9FE8FF` exclusively in the frame-1/2 flash flecks. Alpha is always 0 or 255.

## Verification and renders

Geometry, textures, groups and keyframes were authored through native Blockbench APIs over localhost MCP. The native codec's group descriptors were folded into the legacy inline outliner format expected by pack tooling. No geometry was generated as external model JSON. The downward flash ray uses an equivalent unrotated symmetric cube because the generator rejects an exact diagonal 180-degree transform as a mirrored element.

The initial flat rig preview is `C:/Users/omarz/AppData/Local/Temp/bb-ember-shell/detonation_before.html`. The final real-model preview is `detonation_preview.html` in the same folder. The sixteen-frame Blockbench GIF and contact sheet were rendered and visually inspected, plus a three-quarter peak image and the terminal hidden pose. The GIF is sixteen 50-ms frames (20 fps). The bystander render camera is at world (0,1.6,6) blocks relative to feet, with the rig centre at chest height 1.2 blocks. Renders are `pyro_shell_detonation_render_detonate.gif`, `pyro_shell_detonation_render_contact.png`, `pyro_shell_detonation_render_detonate.png`, `pyro_shell_detonation_render_peak_3d.png`, `pyro_shell_detonation_render_end_hidden.png`, and `pyro_shell_detonation_render_hidden.png`.

Verified: sixteen one-tick spans; every hidden endpoint; 48-element cap; palette and binary alpha; cyan used only in frames 1-2; single-face ring present only in frames 7-11; all transformed corners within shrink-4 bounds; saved-file reload, frame-9 world bounds and every peak lobe corner within the 28-u sphere; all 97 generated files byte-identical to the row's generator output; GIF count and 50-ms duration. The row produces sixteen item definitions, sixteen geometry models and 65 texture copies.

`python tools/gen-flipbook-frames.py`: `OK: 16 flipbook(s), 129 frame(s), 529 file(s) written`.

`build.ps1`: built `dist/LegendCraft-Pack-0.2.4.zip`, pack format 88. `check_pack_manifest.py --pack dist/LegendCraft-Pack-0.2.4.zip --source-tree src`: `OK: LegendCraft-Pack-0.2.4.zip carries 353 item model(s), 12 sound(s), 3 sounds.json`. Plugin-contributed assets were not checked because this is a pack-only art change. Pre-commit drift reports this row's 97 new/changed generated files; the post-commit drift result is recorded verbatim in the handoff.

The brief overrides `legendcraft-blockbench/SKILL.md`'s explicit line "the commit and the handoff are all forbidden" before a subsequent owner ruling, and `PROP-PREVIEW.md`'s "Then the turn ends: the ruling is the next message". The brief authorizes completion here. It also overrides the skill's separate model-repository/index/push workflow. The previously named `pyro_shell_detonation.md` did not exist in this worktree; this contract was created from the brief and the existing shrink-4 table row.

In-game checks remain with the hook owner: chest attachment, restoration of shrink 4, five-block alignment, one-model-per-tick cadence, display removal at tick 16, Minecraft lighting and cutout rendering. No server copy or plugin change occurred.

## History

2026-09-28: Replaced the eight-frame flat drawing with the approved sixteen-frame block burst, rune shards, fire shell, chest ring, falling embers and smoke.
