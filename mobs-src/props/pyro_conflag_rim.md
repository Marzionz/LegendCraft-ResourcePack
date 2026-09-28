# Conflagration channel rim

A ground-level rune ring burns clockwise from north (-Z) over the 70-tick ultimate channel. This is an item-model flipbook authoring rig, never a BetterModel deployment. The plugin maps channel progress to one of 24 item models, about one change every three ticks, then removes the display.

## Sources and art

`pyro_conflag_rim_concept.png` is the owner's eight-cell 1774 x 887 top-down sheet. The 24-frame adaptation keeps its charcoal rune band, cross/diamond/boxed-square/hooked glyph vocabulary, advancing hot head and completed orange ring. Faint red speckle haze is omitted. `pyro_scorch_explosion.md` supplies the shaded block-fire material treatment. Geometry, frame bones and clips were built through the Blockbench MCP native Cube, Group and Animation APIs in Undo transactions, then exported through the project codec. No geometry was generated as external model JSON.

## Radius and resolution contract

All 24 flat tiles share the same radius and ground height within a frame. Their outer edge is authored at 28 u = **1.75 blocks**, with a 3.2 u = **0.2-block** band width. Tangent rectangles span 15 degrees each; binary cutout masks trim their outer corners to the circular edge and trim overlaps at sector boundaries. Pixel centres approximate that edge within one radial texel. Tile 1 is centred on north; tile numbers increase clockwise from above. Frame N uses y = 0.25 + 0.035(N-1) u.

Each tile samples its own 32 x 32 PNG, giving about 10.2 pixels per block circumferentially at the maximum 12-block true radius. The band does not sample a single stretched disc. All tiles at a given heat retain one small readable block glyph and deliberate stepped edge/underside shading.

FLIPBOOKS shrink is **2**, unchanged from the brief. Restore shrink when sizing the generated item: display scale = `2 * trueRadius / 1.75`; the unshrunk authored rig uses `trueRadius / 1.75`. Whole-rig rotated bounds: x [-28.003856, 28], y [0.25, 8.239023], z [-28, 28] u, within the prescribed box. The tiny x overhang belongs to an ember, not the ring edge.

## Frames

Frame N lights tiles 1..N. Older tiles carry yellow runes on orange, the newest three carry white-yellow heat, and unburnt tiles remain charcoal with dark ember-red rune outlines. Each moving head has three successively narrower flame cubes and two embers. Frame 24 turns all runes white-hot and carries flame/ember clusters at tiles 1, 7, 13 and 19.

| Frame | Visible tick | Lit tiles | Head tiles | Ground y (u) | Elements |
| --- | --- | --- | --- | ---: | ---: |
| 1 | 0..1 | 1..1 | 1 | 0.250 | 29 |
| 2 | 1..2 | 1..2 | 2 | 0.285 | 29 |
| 3 | 2..3 | 1..3 | 3 | 0.320 | 29 |
| 4 | 3..4 | 1..4 | 4 | 0.355 | 29 |
| 5 | 4..5 | 1..5 | 5 | 0.390 | 29 |
| 6 | 5..6 | 1..6 | 6 | 0.425 | 29 |
| 7 | 6..7 | 1..7 | 7 | 0.460 | 29 |
| 8 | 7..8 | 1..8 | 8 | 0.495 | 29 |
| 9 | 8..9 | 1..9 | 9 | 0.530 | 29 |
| 10 | 9..10 | 1..10 | 10 | 0.565 | 29 |
| 11 | 10..11 | 1..11 | 11 | 0.600 | 29 |
| 12 | 11..12 | 1..12 | 12 | 0.635 | 29 |
| 13 | 12..13 | 1..13 | 13 | 0.670 | 29 |
| 14 | 13..14 | 1..14 | 14 | 0.705 | 29 |
| 15 | 14..15 | 1..15 | 15 | 0.740 | 29 |
| 16 | 15..16 | 1..16 | 16 | 0.775 | 29 |
| 17 | 16..17 | 1..17 | 17 | 0.810 | 29 |
| 18 | 17..18 | 1..18 | 18 | 0.845 | 29 |
| 19 | 18..19 | 1..19 | 19 | 0.880 | 29 |
| 20 | 19..20 | 1..20 | 20 | 0.915 | 29 |
| 21 | 20..21 | 1..21 | 21 | 0.950 | 29 |
| 22 | 21..22 | 1..22 | 22 | 0.985 | 29 |
| 23 | 22..23 | 1..23 | 23 | 1.020 | 29 |
| 24 | 23..24 | 1..24 | 1, 7, 13, 19 | 1.055 | 44 |

711 elements total; frames 1-23 each contain 24 tiles + 3 flame cubes + 2 embers = 29; frame 24 contains 24 tiles + 12 flame cubes + 8 embers = 44. Maximum 44 is below 48.

## Textures

93 embedded editable PNGs: 90 per-tile heat variants and three 32 x 32 shaded fire materials (`white_hot`, `yellow`, `orange`). File prefix `pyro_conflag_rim_tex_`. Material faces have a curled shaded core, stepped upper highlight and darker underside. Up faces sample rows 0-20, down faces 16-32, vertical faces the full swatch. Unused variants are removed.

Palette exclusively `#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`; alpha is binary 0/255. No cyan occurs in this rig. The original concept image is retained unchanged as reference, not a runtime texture.

## Rig and clips

Unyawed `root -> fx -> frame_1..frame_24`, as required by `SIGNS.md`. Each frame directly owns its elements. Scale-only `fuse` holds for 1.2 seconds: frame N shows at tick N-1, disappears at tick N, and all frames are hidden at tick 24. Every bone has a step key on every tick 0..24, scale 1 or 0.001. `hidden` is a one-second loop, every frame 0.001 at every tick. No rotation/position animation keys. Exact 180-degree tile turns are baked into coordinates with a 180-degree up-face UV turn so the existing generator does not mistake their diagonal rotation matrices for mirrors.

## Verification and renders

The real-model prop preview is `C:/Users/omarz/AppData/Local/Temp/bb-pyro-conflagration/rim_preview.html`, clip fuse, grounded at chest offset 0. Final Blockbench renders were viewed as a full contact sheet and at full frame size. Top-down camera is (0,90,0.001) u, target origin, perspective FOV 50; the negligible z epsilon supplies a stable north-up camera. Bystander camera is (0,25.6,96) u, target origin, FOV 50: 1.6 blocks up, 6 blocks out.

- `pyro_conflag_rim_render_contact.png`: all 24 top-down frames.
- `pyro_conflag_rim_render_fuse.gif`: 24 frames, approximately 7 fps; GIF's centisecond timing alternates 140/150 ms, total 3.43 seconds.
- `pyro_conflag_rim_render_frame_24_eye.png`: completed ring from bystander eye.
- `pyro_conflag_rim_render_end_hidden.png` and `_render_hidden.png`: final hidden state and hidden loop.

Verification checks every rotated corner, per-frame count, all 25 fuse tick states, hidden keys, one-tick changing segments, palette/binary alpha, embedded-to-editable PNG equality, 24 generator spans, all 696 generated files byte-for-byte and GIF frame count/timing. Pack build and manifest validation are recorded in the handoff; post-commit generator drift is quoted there.

The brief explicitly overrides `legendcraft-blockbench/SKILL.md`: “the commit and the handoff are all forbidden” before a later owner ruling, and `PROP-PREVIEW.md`: “Then the turn ends: the ruling is the next message”. These are explicit skill gates; this build brief authorizes completing renders and commits now. Its named-path scope also replaces the skill's unrelated index/push workflow.

No plugin code or deployment. In-game checks still require the owner: actual-radius alignment at 8/12 blocks, item-display shrink restoration, channel cadence, cutout lighting and display removal.

## History

2026-09-28: created the tiled 24-frame fuse rim from the owner's concept; authored and rendered through Blockbench MCP, generated item frames and retained shrink 2.
