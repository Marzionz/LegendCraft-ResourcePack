# Knight War Cry horn flipbook

One owner-approved horn, played by one ItemDisplay swapping four item models. This authoring rig replaces the old four-horn BetterModel stack. It is a flat flipbook in the roster's playback sense; the approved horn remains voxel geometry.

## Geometry, origin and textures

Each of the four frame bones directly under `root` contains 379 cubes copied from `knight_horn.bbmodel`: `solid`, `fade65`, `fade35`, `fade12`. Total: 1,516 cubes, five bones, four embedded 64?64 textures. Cube dimensions, rotations, UVs, material pixels and geometry are preserved. The horn runs along ?z, with the terminal bell at its approved 22.5? upward pitch. No yaw copies or rise motion remain.

Every endpoint and cube pivot is translated by (?8,?8,?8) from the held-item source so the mouthpiece is at authoring (0,0,0). The generator adds (8,8,8), putting the exported mouthpiece at the ItemDisplay pivot (8,8,8). A literal coordinate copy would put it at (16,16,16). This coordinate-convention question is recorded OPEN in the orchestrator inbox; the build follows the recommended recentering. The held horn source, contract and runtime assets are unchanged.

One texture belongs to each frame. Solid uses the original embedded PNG bytes. Fades copy all RGB pixels unchanged and round each painted alpha multiplied by 0.65, 0.35 or 0.12 to the nearest integer. The painted alpha is uniformly 255, so the resulting values are 255, 166, 89 and 31. Editable atlases are `knight_horn_blast_solid.png`, `_fade65.png`, `_fade35.png`, `_fade12.png`. The obsolete 256?64 four-layer atlas `knight_horn_blast.png` is removed.

## Clips and hook contract

`war_cry`: 1.50 seconds, 30 ticks, hold. Scale keys are step interpolation on the four frame bones only. Shown scale is 1; hidden scale is 0.001 on all axes. Exactly one frame is shown before the hidden endpoint.

| Ticks | Seconds | Frame | Item-model stem |
| --- | --- | --- | --- |
| 0?18 | [0.00, 0.95) | solid | `knight_horn_blast_1` |
| 19?22 | [0.95, 1.15) | fade65 | `knight_horn_blast_2` |
| 23?25 | [1.15, 1.30) | fade35 | `knight_horn_blast_3` |
| 26?29 | [1.30, 1.50) | fade12 | `knight_horn_blast_4` |
| 30 onward | 1.50 onward | all hidden | hide/remove display |

`hidden`: looping 0.05-second clip, all four frame bones at 0.001 from time zero. There are no rotation or position keys, and no animated parent scale.

The plugin owns placement of four displays around the Knight and the rise transform about each mouthpiece. Those placements and transforms are outside this asset. Generated frames use scale 1 without shrink compensation. No transparent fifth frame is generated: the hook hides/removes the display at tick 30.

Registry row:

| frames | rig | clip | shrink | native | tint |
| --- | --- | --- | --- | --- | --- |
| `knight_horn_blast` | `knight_horn_blast` | `war_cry` | 1 | | |

Each stem has an item definition, element model and PNG under `src/assets/legendcraft/{items,models/item,textures/item}/classes/`. The generator accepted shrink 1.

## Verification

Built on 2026-09-28 on `knight-horn-flipbook`. The explicit build brief supplies the approved art and timing and authorizes final renders and commit; no additional design ruling was requested.

- `python tools/gen-flipbook-frames.py`: passed, 17 flipbooks / 125 frames / 468 files. The 12 new runtime files match a fresh in-memory build byte for byte.
- All 1,516 cubes match the source fields after the uniform coordinate translation, UUID replacement and frame texture remapping. RGB and UV comparisons passed. All 12,128 exported cube corners match the approved held-item coordinates within 0.000000496 model units (generator rounding).
- Visibility checked at every millisecond from 0.000 through 1.600 seconds: exact transitions at ticks 0, 19, 23, 26 and 30, no overlap or intermediate disappearance. All animation keys are tick-aligned, step and scale only. Hidden loop checked separately.
- Blockbench MCP loaded the real rig: 1,516 cubes, five groups, four textures. `pose.py` captured all four frames and the side profile. `gif.py` captured 31 samples at 50 ms, including the hidden endpoint at 1.50 seconds; the encoded GIF lasts 1.55 seconds because that endpoint is displayed for one sample. `sheet.py` produced the motion sheet. The mannequin is exactly 32 units / two blocks tall; horn scale is 1. Reference geometry exists only in the preview scene.
- Inspected the four-frame contact sheet, the full motion sheet and side view. The silhouette, rising bell, hollow mouth and hanging strap remain intact; alpha decreases at each requested boundary; final sample is hidden.
- `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1`: passed. Pack SHA1 `b4616d1b1914a7993df3b5809c2261e4dc4df370`.
- `python tools/check_pack_manifest.py --pack dist/LegendCraft-Pack-0.2.4.zip --source-tree src`: passed, 349 item models, 12 sounds, four sounds.json. All 12 new horn runtime files match the zip byte for byte. Plugin-contributed inputs were not part of this base-pack build.

Minecraft client translucency sorting and the plugin-owned rise/placement remain for the later integration check; these renders are from Blockbench, not a deployed client.

## Renders

- [Four-frame contact sheet](knight_horn_blast_render_contact_sheet.png)
- [20 fps bystander GIF](knight_horn_blast_render_bystander.gif)
- [Frame 1 side view](knight_horn_blast_render_side.png)
- [31-sample motion sheet](knight_horn_blast_render_timeline_sheet.png)
- [Interactive prop preview](knight_horn_blast_render_preview.html)

## History

2026-09-28: Replaced the 6,064-cube four-horn BetterModel rig with one horn in four texture-alpha frame bones and generated four flat-flipbook item frames. No plugin change or deployment.
