# Scorch land explosion

Scorch's meteor explodes where it stops, damaging enemies within 4.0 blocks and applying a Burning stack. This ground-snapped effect lasts 16 ticks: eight drawings, two ticks each. The ground ring communicates the damage edge to a bystander.

The rig is the source for `tools/gen-flipbook-frames.py` and the prop preview. Runtime uses **one item display swapping item models**, `legendcraft:classes/pyro_scorch_explosion_1` through `_8`. Never deploy this rig to BetterModel; its scale steps select authoring frames only.

## Approved sources

- `pyro_scorch_explosion_concept_ground.png`: 1774 x 887 RGBA, ground ring and char.
- `pyro_scorch_explosion_concept_side.png`: 1774 x 887 RGBA, flash, dome, flames, smoke and sparks.

Both sheets contain four columns and two rows, read left to right, then top to bottom. Their art is cropped, registered, palette-quantized and nearest-neighbour downsampled, without repainting or synthesizing the ring. Previous frame art, emissive pairs, GIF and sheet are superseded and are not inputs.

## Geometry and radius contract

Hierarchy: unyawed `root` -> `fx` -> `frame_1` through `frame_8`. Each frame contains four zero-thickness planes (32 total):

- `disc_N`: 64 x 64 model units, centred on the origin, horizontal at y = 0.25 + 0.035(N-1). Ground cell: 128 x 128 pixels.
- `cross_a_N`, `cross_b_N`, `cross_c_N`: each 56 units wide x 42 tall, standing at y = 0, with rest yaw 0, 60 and 120 degrees around the origin. Local depth stagger: 0.035(N-1) units. Each carries the same 112 x 84 side cell.

One model unit is 1/16 block. Each plane has one textured face and textures render double-sided. The six half-planes are spaced 60 degrees apart. The generator accepts these rotations; no 0/45/-45 fallback was needed.

**The ring's outer radius is 56 texture pixels at 32 px/block: 28 model units, or 1.75 blocks at authored scale 1.** The disc square is 4 blocks wide; the star is 3.5 blocks wide and 2.625 blocks tall. The 56-pixel radius must not be confused with a 56-model-unit radius.

Frames 2-8 are individually centred and rescaled to the same 56-pixel outer-radius target. Frame 1 retains its smaller flash. Measured outer occupied pixel-centre radii after nearest-neighbour sampling:

| Frame | Radius (texture pixels) |
| --- | ---: |
| 1 | 32.932 (flash) |
| 2 | 55.933 |
| 3 | 56.147 |
| 4 | 56.147 |
| 5 | 55.700 |
| 6 | 55.376 |
| 7 | 55.556 |
| 8 | 55.879 |

Every ring is within one output texel of the target; the subpixel differences come from nearest-neighbour rasterization. Registration reuses the resumed session's centres and per-cell scales. All side cells use 0.28 output pixels per source pixel and source-cell x centre 221.5. Baselines are 406 for the top row and 399 for the bottom row, aligning both rows to y = 0. Frame 3 fills most of the height; later frames retain that scale.

The FLIPBOOKS row uses **shrink 2** to fit the item-model box. Display scale must be `2 * trueRadius / 1.75`; for a 4-block damage radius this is `32/7`, approximately 4.571429. The factor 2 restores generator shrink; the remaining factor aligns the ring with damage. Ground-snap at impact and remove the display at tick 16.

## Textures

Eight embedded 128 x 212 RGBA atlases contain the ground cell at `(0,0)-(128,128)` and the side cell at `(8,128)-(120,212)`. Each generated frame copies its atlas unchanged. No `_e` emissive pair is used. Every visible output pixel belongs to this ramp, with alpha exclusively 0 or 255:

`#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`

The resumed texture pass rejects alpha below 128 and desaturated soft fringe, then maps retained fire/char colours to the nearest ramp entry. Raw concept RGB values are quantized, not required to equal a ramp hex before conversion. Sampling is nearest-neighbour throughout. Saved atlases were reused after checking their palette, binary alpha, ring registration and side scale.

## Clips and timing

`burst`: 0.8 seconds, hold mode. Scale 1 shows a frame; 0.001 hides it. Every changing segment has a key one tick before the step and at the step, using step interpolation. Exactly one frame is visible at ticks 0-15. All frames have hidden keys at tick 16: **the clip ends hidden**. `hidden` loops with every frame at 0.001. Both clips use only scale keys on the 20-tps grid. Rest geometry follows the unyawed prop convention from `SIGNS.md`; there are no animated rotation or position signs.

| Frame | Visible ticks | Seconds [start, end) | Ground | Upright |
| --- | --- | --- | --- | --- |
| 1 | 0-1 | 0.00-0.10 | Flash disc | Small flash |
| 2 | 2-3 | 0.10-0.20 | Forming fire ring | Spiky starburst |
| 3 | 4-5 | 0.20-0.30 | Full ring over char | Peak dome |
| 4 | 6-7 | 0.30-0.40 | Full ring over char | Breaking flame tongues |
| 5 | 8-9 | 0.40-0.50 | Flames sink to embers | Thinning flames, first smoke |
| 6 | 10-11 | 0.50-0.60 | Ember ring | Low flames, embers and smoke |
| 7 | 12-13 | 0.60-0.70 | Cooling ember ring | Last flame, puffs and embers |
| 8 | 14-15 | 0.70-0.80 | Cooling char and embers | Last sparks |
| Hidden | 16 onward | 0.80 onward | Hidden | Hidden |

## Verification

Geometry was edited in Blockbench through its MCP and exported by Blockbench's project codec. Legacy outliner serialization keeps the file compatible with the existing generator. No external script generated model geometry JSON.

The real saved rig feeds the prop preview (`--clip burst --chest 0`): `C:/Users/omarz/AppData/Local/Temp/bb-pyro_scorch_explosion/preview.html`. The brief explicitly overrides the skill's intermediate owner-ruling stop.

Inspected Blockbench renders: `pyro_scorch_explosion_render_frame_01.png` through `_08.png`, eye height 1.6 blocks, horizontal distance 6 blocks, looking at the origin; `_frame_03_top.png` and `_frame_06_top.png` look straight down. `_contact.png` collects all eight bystander views. `_burst_end_hidden.png` and `_hidden.png` document both hidden states. These views show authored scale.

Verification passed: eight frames, four planes each, 24 generated files; tick selection, one-tick changing segments, final hidden state, exact output palette, binary alpha and ring registration. `LegendCraft-Pack-0.2.4.zip` passed the source manifest gate; all 24 Scorch ZIP entries were additionally compared byte-for-byte with generated output. The handoff records post-commit drift output.

Owner review of the new renders and in-game checks remain: ring alignment at the 4-block boundary, six-sided read, item-model face visibility and alpha sorting, lighting, and two-tick model swaps. No deployment was performed.

## History

2026-09-27: rebuilt from the two owner-approved transparent sheets. Reused registered textures and scale clips from the resumed session; replaced its two-plane cross with the requested 0/60/120-degree star. Generated the shrink-2 item-model flipbook, replaced the obsolete contract, and captured the new render set.
