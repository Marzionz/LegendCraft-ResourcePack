# Conflagration channel rim

Conflagration's ground rune chain charges clockwise during the Pyromancer ultimate's 70-tick channel. The plugin swaps one of 24 item models onto one ground display, then removes it for detonation. Each major piece follows its glyph: heavy crosses and stepped hooks, with cardinal diamonds and boxed squares. Two small hook/bar fragments per sector overlap neighbouring outlines into a packed chain. There are no square backings behind crosses or hooks. Charged strokes carry thin white cores, broad yellow-orange bodies and heavy orange-red rims; cold strokes are warm red-brown with brighter red cores. Attached flame tongues lie flat on the ground.

## Registration and dimensions

The centre is the origin. North is -Z; sector 1 is centred there, and sectors 2..24 proceed clockwise from above in 15-degree steps. Frame N lights sectors 1..N. The 28 u nominal rim radius, 30 u absolute flame cap and runtime registration are unchanged.

| Feature | Dimensions |
| --- | --- |
| Cross pieces | Nominal 5.75..6 u across; 14..16-source-pixel strokes (1.75..2 u), before diagonal raster joins |
| Stepped S/L hooks | Nominal 5.75 x 4.125 u; 14-source-pixel strokes (1.75 u) |
| Cardinal diamonds | About 6.5 u tip to tip before radial clipping; centre radius 25.25 u |
| Boxed squares | About 5 x 5 u before radial clipping; 1.75 u strokes; screen-axis aligned |
| Gap fragments | 48 per frame, two per sector; retained short hooks/bars, thickened toward 14..15-source-pixel strokes (1.75..1.875 u); intersections and sector/radial clipping vary the local width |
| Outline and bevel | Two-source-pixel dark outline (0.25 u; diagonal raster footprint reaches 2.83 pixels), one-source-pixel lighter upper/left bevel; lower/right recess |
| Glyph cores | Approximately 5 source pixels (0.625 u) down major strokes; inherited marks and bearings retained; head mostly white-yellow |
| Flame tongues | Nominal 6..10 x 5..6 art texels on a two-source-pixel grid: 12..20 x 10..12 PNG pixels (1.5..2.5 x 1.25..1.5 u); length shortened at the 30 u cap; two/three overlapping tongues make each mass |
| Piece/fragment envelope | 22.000000..28.474221 u, measured at opaque pixel corners |
| Flame envelope | 24.987810..29.992968 u, measured at opaque pixel corners; below the 30 u cap |
| Carrier planes | Two 64 x 64 u planes per frame, x/z -32..32 u, zero thickness |
| Block plane y | 0.20 + 0.02(N-1) u |
| Flame plane y | Block plane y + 0.06 u; no opaque overlap |
| Complete geometry y | 0.20..0.72 u |

The major pieces and fragments form one eight-connected opaque chain, with touching outlines and small ground cutouts inside the glyphs. There are no square backings behind the crosses/hooks. Older lit pieces have two tongues; the three newest have three. Frame 24 has three per major piece, 72 nominal tongues total. Tongues cluster on the outer edge; all are attached and flat. Each mass progresses from #FFD24A roots through #FF8A00 body into #E8500F and #B7331A tips. The head alone keeps a mostly white-yellow body and pale roots. Flame coverage grows from 357 pixels in frame 1 to 7,510 in frame 24 (r4 final: 2,066). No opaque flame pixel overlaps the lower plane.

The flame art-texel interpretation is recorded as OPEN in `C:/Users/omarz/.claude/comms/orchestrator-inbox.md`, CONFLAG-RIM-R5: literal 6..10 PNG pixels remained tiny in native comparison. This pass uses a two-PNG-pixel flame art grid to deliver broad visible masses while preserving the 512px textures and 30 u cap. Glyph outlines still use source pixels.

28 u = 1.75 blocks. `FLIPBOOKS.md` remains `pyro_conflag_rim | pyro_conflag_rim | fuse | 2`. Item display scale remains `2 * trueRadius / 1.75`; the unshrunk rig uses `trueRadius / 1.75`. Runtime keys remain `pyro_conflag_rim_1` through `pyro_conflag_rim_24`. No recentering or ground snapping is introduced.

## Rig and timing

Unyawed `root -> fx -> frame_1..frame_24`. Each frame directly owns two elements: glyph/fragment plane and flame plane. **Two elements per frame, 48 total**, within the 48-element per-frame budget. The pieces are texture artwork, not separate cubes. The elements, outliner and animation data compare equal to r4 commit `07d6568` (and r3 `5055d8c`).

`fuse` is a 1.2-second hold clip. Each frame bone has a step scale key on every tick 0..24: shown scale 1 for its one tick, hidden scale 0.001 otherwise. Frame N is shown on [N-1, N). At tick 24 all frames are hidden. `hidden` is a one-second loop with 21 all-hidden tick keys per frame. There are no position or rotation channels. The plugin's existing 70-tick channel scheduling is unchanged; the diagnostic GIF holds each drawing for three ticks, totalling 72 ticks.

| Frame | Visible interval | Lit sectors | Band y (u) | Halo y (u) | Elements |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | 0 <= tick < 1 | 1..1 | 0.20 | 0.26 | 2 |
| 2 | 1 <= tick < 2 | 1..2 | 0.22 | 0.28 | 2 |
| 3 | 2 <= tick < 3 | 1..3 | 0.24 | 0.30 | 2 |
| 4 | 3 <= tick < 4 | 1..4 | 0.26 | 0.32 | 2 |
| 5 | 4 <= tick < 5 | 1..5 | 0.28 | 0.34 | 2 |
| 6 | 5 <= tick < 6 | 1..6 | 0.30 | 0.36 | 2 |
| 7 | 6 <= tick < 7 | 1..7 | 0.32 | 0.38 | 2 |
| 8 | 7 <= tick < 8 | 1..8 | 0.34 | 0.40 | 2 |
| 9 | 8 <= tick < 9 | 1..9 | 0.36 | 0.42 | 2 |
| 10 | 9 <= tick < 10 | 1..10 | 0.38 | 0.44 | 2 |
| 11 | 10 <= tick < 11 | 1..11 | 0.40 | 0.46 | 2 |
| 12 | 11 <= tick < 12 | 1..12 | 0.42 | 0.48 | 2 |
| 13 | 12 <= tick < 13 | 1..13 | 0.44 | 0.50 | 2 |
| 14 | 13 <= tick < 14 | 1..14 | 0.46 | 0.52 | 2 |
| 15 | 14 <= tick < 15 | 1..15 | 0.48 | 0.54 | 2 |
| 16 | 15 <= tick < 16 | 1..16 | 0.50 | 0.56 | 2 |
| 17 | 16 <= tick < 17 | 1..17 | 0.52 | 0.58 | 2 |
| 18 | 17 <= tick < 18 | 1..18 | 0.54 | 0.60 | 2 |
| 19 | 18 <= tick < 19 | 1..19 | 0.56 | 0.62 | 2 |
| 20 | 19 <= tick < 20 | 1..20 | 0.58 | 0.64 | 2 |
| 21 | 20 <= tick < 21 | 1..21 | 0.60 | 0.66 | 2 |
| 22 | 21 <= tick < 22 | 1..22 | 0.62 | 0.68 | 2 |
| 23 | 22 <= tick < 23 | 1..23 | 0.64 | 0.70 | 2 |
| 24 | 23 <= tick < 24 | 1..24 | 0.66 | 0.72 | 2 |

## Texture and palette

48 embedded, editable 512 x 512 PNGs: `pyro_conflag_rim_tex_band_01.png` through `_24.png` and `pyro_conflag_rim_tex_halo_01.png` through `_24.png`. The retained filenames describe the carrier layers; their contents are glyph silhouettes, packed fragments and attached flame tongues. All embedded PNG bytes equal their editable counterparts. Sampling remains 8 pixels/u over the 64 u canvas, about 18.7 texels per world block at a 12-block field radius. Alpha is binary 0/255. Only the up face is textured on each plane, with double-sided preview rendering.

| Role | Colours |
| --- | --- |
| Lit glyph | `#FFF4E0` |
| Lit face | `#FFD24A`, `#FF8A00` |
| Lit rim and glyph socket | `#E8500F`, `#B7331A` |
| Cold face and recess | `#7A1F10`, `#39281F` |
| Cold outline | `#171310`, `#241F1B` |
| Cold bevel | `#594037` |
| Cold glyph and lit edge | `#B7331A`, `#E8500F` |
| Flames | `#FFD24A` roots, `#FF8A00` body, `#E8500F` upper flame and `#B7331A` tips; pale head roots |

All ten used colours belong to the retained palette. The approved greys `#4A423C` and `#3B3430` remain unused. No palette additions. In frame 24, charged band pixels excluding the newest head measure **23.21% white core, 48.63% yellow-orange body, 28.16% orange-red rim**. The head is excluded because it intentionally remains mostly white-yellow.

## Renders and verification

Round 5 retains all geometry, outliner data, animation data, registration and non-source texture metadata exactly from r4. Only the 48 embedded texture sources change. Existing MCP-native planes were loaded into isolated project UUID `022eabb1-d15a-f99b-4580-df445dd67f95` at `http://localhost:3000/bb-mcp`; texture refresh used native Texture APIs and a scoped Undo transaction. The project codec verified the export. Its new group serialization, float normalization and preview-created empty animators were kept out of the deliverable by transferring only the verified native texture sources into the unchanged r4 structure. All native operations target that UUID and restore the previously selected project.

`PROP-PREVIEW.md`'s generator produced baseline and final HTML from the real model. The final page retains r4's 8/12-block radius, top/bystander, tick/clip and turnaround controls. Its embedded rig data equals the final source model. HTML interaction was not browser-tested.

The full render set was replaced using cloned native Blockbench meshes and native evaluated animation states in a separate Three.js renderer:

- `pyro_conflag_rim_render_contact.png`: all 24 frames, north up.
- `pyro_conflag_rim_render_vs_concept.png`: frames 1, 4, 7, 10, 13, 16, 20, 24 beside the untouched concept cells.
- `pyro_conflag_rim_render_zoom_vs_concept.png`: frames 1/24 and north-east quarter crops beside the untouched owner zoom panel.
- `pyro_conflag_rim_render_frame_12_eye.png` and `_render_frame_24_eye.png`: original 8-block-radius shallow eye views.
- `pyro_conflag_rim_render_distance.png`: frame 24 at radii 8/12 blocks, from 8/12 blocks outside the nominal rim, eye height 1.6 blocks.
- `pyro_conflag_rim_render_fuse.gif`: 72 encoded frames at 50 ms; each drawing held three ticks.
- `pyro_conflag_rim_render_end_hidden.png` and `_render_hidden.png`: freshly rendered empty ground; byte-identical to r4.
- `pyro_conflag_rim_render_preview.html`: final real-model interactive preview.

Ground is #777777, sky #11141C. Native top camera: (0,74,0.001) u, target origin, FOV 50 degrees, 768px square. Original eye camera: (0,25.6,96) u, target (0,8,0) u, FOV 70 degrees, rig scale 8/1.75. Distance-sheet cameras use z = 16 * (fieldRadius + distanceFromRim) u and scale = fieldRadius/1.75.

Comparison framing corrects r4's roughly 12% undersized native ring against the reference. Zoom cells remain 443px; native views are resized to 482px and centred/cropped, retaining all opaque art. North-east crops remain (221,0)..(443,222), enlarged with nearest sampling. Full comparison cells use 392px native views centred in 360px cells. Both reference panels compare pixel-identical to r4. This is a presentation correction only; the rig radius and runtime registration are unchanged.

Both final vs-concept renders, the contact sheet, eye view and distance sheet were inspected before commit. Verification passes for exact retained model data, two elements per frame, flatness, single up face, 512px texture size, editable/embedded equality, binary alpha, palette membership, pixel-corner radial bounds, clockwise heat sectors, connected band, attached nonoverlapping flames, fuse/hidden states, hidden renders and GIF timing. All 96 generated rim outputs equal an independent fresh generator build; all 48 runtime JSON files equal r4. Shrink remains 2. The build, manifest and post-commit drift output are recorded in the r5 report.

## Remaining differences from the concept

The repeated crosses/hooks, diamond grid marks and open-centred boxed squares retain r4's vocabulary. The reference has less regular shapes and inner cross motifs in its boxes. This chain is more regular and crisply rastered; its flame masses are more evenly distributed and bend less organically. The flame tips stay inside 30 u, so some are shortened at the cap. The head is a hard white-yellow glyph rather than a soft flare. Binary alpha excludes bloom, translucent haze and detached sparks.

At shallow eye angles the flat ring is strongly foreshortened: the band and heat progression read, but fine glyph and flame details compress. Minecraft lighting, terrain contact, z-sorting, 8/12-block scaling and actual playback still need an in-game look.

## Round 5 authorization

The owner's brief authorizes this texture polish, native renders, regeneration, one local commit and the handoff without a separate preview ruling turn. It overrides the skill's END THE TURN / later-ruling gate, the equivalent PROP-PREVIEW loop step 1, and the instruction to push authoring work. No push, PR, plugin code or field rig change is part of this pass.
