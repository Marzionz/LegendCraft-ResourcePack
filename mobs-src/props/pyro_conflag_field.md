# Conflagration scorched field

The ground beneath the Pyromancer ultimate, from the detonation flash through the persistent burning field to cold char. One item display swaps 16 flat drawings. The separate `pyro_conflag_explosion` owns the first 16 ticks of height; this prop provides only the ground. The reference is the unchanged eight-cell `pyro_conflag_field_concept.png`.

## Registration and shape

The origin is the centre at ground level. North is -Z. All bones and elements are unyawed, with origin [0,0,0]. The full field's rim has an outer radius of **28 u = 1.75 blocks**, matching `pyro_conflag_rim`. The flame fringe stays inside **31 u**. Every opaque pixel corner is checked against those outer radii. Rune artwork occupies approximately **21.5..25.5 u**; the raster pixel envelope is within 0.09 u of those boundaries.

Every carrier plane spans x/z **-32..32 u**; transparent margins do not define the visible field. The layered height is **y 0.14..1.00 u**: disk 0.14, cracks 0.26, rim 0.40, runes 0.54, fringe 0.68, flash 1.00. All planes have zero thickness and only their up face textured. There are no vertical elements, rock chunks, detached embers or particle speckles.

The generator shrinks by 2. Scale the generated item by **2 * trueRadius / 1.75**: 9.142857 at radius 8, or 13.714286 at radius 12. Scale the unshrunk authoring rig by `trueRadius / 1.75`. Do not re-centre or ground-snap it. The visible rim diameter becomes 16 or 24 blocks; the maximum fringe diameter becomes 17.714286 or 26.571429 blocks.

## Frames and clips

Unyawed `root -> fx -> frame_1..frame_16`. Each frame owns its elements directly. Total: **68 elements; 1..5 per frame**, below the 48-per-frame budget. Each element has its own embedded 512 x 512 editable PNG named `pyro_conflag_field_tex_<layer>_<frame>.png`.

`blast` is a 0.80-second hold clip. Each frame bone has a scale key at every tick 0..16, with step interpolation. Shown scale is 1; hidden scale is 0.001. Frame N shows on [N-1,N); every changing segment is exactly one tick. At tick 16 all frames are hidden: **the clip ends hidden**. `hidden` is a one-second loop with all 16 frames hidden at every tick 0..20. There are no position or rotation animation channels.

The plugin owns runtime timing. The GIF samples the brief's explicit timeline at 20 fps: frames 1..7 take one tick each; frame 8 holds until tick 58; eight cooling states fill ticks 58..72. Their ideal spacing is 1.75 ticks; integer GIF samples produce 2,2,2,1,2,2,2,1 ticks. Runtime hold lengths are not baked into `blast`.

| Frame | Authoring clip interval | Runtime GIF ticks | Elements | Drawing |
| --- | --- | --- | ---: | --- |
| 1 | 0 <= tick < 1 | 0..1 | 1 | White-yellow star and orange corona, small cross rays |
| 2 | 1 <= tick < 2 | 1..2 | 1 | Expanded flash and four long cross rays |
| 3 | 2 <= tick < 3 | 2..3 | 4 | 14 u blast ring, radial petals and bright centre |
| 4 | 3 <= tick < 4 | 3..4 | 4 | 22 u blast ring, radial petals and fading centre |
| 5 | 4 <= tick < 5 | 4..5 | 4 | Full cracked basalt disk; hot rim and attached fringe |
| 6 | 5 <= tick < 6 | 5..6 | 5 | Half-bright charged runes ignite |
| 7 | 6 <= tick < 7 | 6..7 | 5 | Runes reach white-yellow heat |
| 8 | 7 <= tick < 8 | 7..58 | 5 | Steady full-glow field; runtime hold |
| 9 | 8 <= tick < 9 | 58..60 | 5 | Cooling 1/8; white leaves rim |
| 10 | 9 <= tick < 10 | 60..62 | 5 | Cooling 2/8; yellow rim and glyphs |
| 11 | 10 <= tick < 11 | 62..64 | 5 | Cooling 3/8; orange rim and glyphs |
| 12 | 11 <= tick < 12 | 64..65 | 5 | Cooling 4/8; orange-red cracks |
| 13 | 12 <= tick < 13 | 65..67 | 5 | Cooling 5/8; shrinking red fringe |
| 14 | 13 <= tick < 14 | 67..69 | 5 | Cooling 6/8; deep red perimeter |
| 15 | 14 <= tick < 15 | 69..71 | 5 | Cooling 7/8; faint fringe, rune outlines |
| 16 | 15 <= tick < 16 | 71..72 | 4 | Cold char; dark-red cracks and rune outlines; no fringe |

The pack row is `pyro_conflag_field | pyro_conflag_field | blast | 2`. Runtime item keys are `legendcraft:classes/pyro_conflag_field_1` through `_16` (frame stems `pyro_conflag_field_1` through `_16`).

## Texture and palette

The basalt, cracks, ring and fringe are painted on a 256-pixel working grid and stored at 512 pixels with nearest-neighbour 2 x 2 clusters. The full disk is about **220 distinct working pixels / 440 stored pixels across**, exceeding the 192-pixel requirement before upscaling. At the 24-block diameter this is about 9.2 distinct clusters / 18.3 stored texels per block. Runes retain the rim's 512-pixel sampling.

All texture alpha is binary 0/255. The palette is **#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310**, plus the rim's existing named tones **#594037** (warm bevel) and **#39281F** (charcoal-brown face). All 12 occur; no other opaque RGB values occur. Heat changes by palette steps and thinning shapes, never translucent fades.

## Rune continuity

All rune art is sampled directly from the rim's charged `pyro_conflag_rim_tex_band_24.png`. The polar angle is unchanged. Its painted 22..28.5 u node envelope maps inward to 21.5..25.5 u; radial compression leaves room for the burning outer ring. Tile 1 remains at north (-Z), and the 24 tiles proceed clockwise at 15-degree intervals.

Each six-tile sector repeats **diamond checker, hook, cross, boxed square, cross, opposite hook**. Cardinal tiles 1/7/13/19 are diamond checkers; tiles 4/10/16/22 are boxed squares. The source's stepped top-left light bevel and bottom-right recess remain, with the block backgrounds darkened into basalt so the glyphs carry the light. The original hot glyph bitmap is preserved by nearest-neighbour radial remapping; its orange socket separates the white-yellow core from stone. Frame 6 uses orange half-bright cores, 7..8 white-yellow, then eight cooling steps end in dim dark-red outlines.

## Mapping to the concept

Cells 1 and 2 become two frames each, exposing the flash growth and ring expansion. Cell 3 becomes frame 5. Cell 4 becomes the half/full rune ignition in frames 6/7. Cell 5 is the held field in frame 8. Cells 6..8 guide the cooling ladder, extended to the colder frame 16. The cracked plates, continuous hot rim, thick attached flame fringe and inner glyph band are the four main reads.

This is an original pixel repaint, not a trace of the concept's fracture network. The crack layout and basalt clusters differ. The concept's soft additive glow and semi-transparent fire haze become hard palette bands under binary alpha. The outside flame tongues stop at 31 u. Scattered dark rocks and speckles are intentionally absent. The runes use the existing rim vocabulary and bevel, rather than the concept's independent glyph drawings. Frame 1 is deliberately smaller than reference cell 1; frame 2 is its expanded state.

## Verification and renders

Geometry, texture embedding and clips were authored through native Group/Cube/Texture/Animation APIs over the Blockbench MCP, in a separate UUID-scoped project. Blockbench's project codec supplied the saved model. No external script generated the geometry JSON, and the rim rig was read-only.

The real-model three.js preview is generated through `PROP-PREVIEW.md`'s `prop_preview.py`, adapted to ground level, binary cutout depth, and 8/12-block scale controls. It shows the authored one-tick clip; runtime timing appears only in the GIF. A headless Chrome check loaded all 68 textures, selected frame 8 alone, exercised the 12-block scale control, and confirmed all frames hidden at tick 16 without script errors. Its screenshot was visually inspected. The native Blockbench render pass uses a separate THREE scene and renderer cloned from this project's actual geometry and evaluated animation state. Existing sessions' offscreen views are untouched.

All renders use mid-grey #777777 ground and dark #11141C sky. The top-down camera is (0,74,0.001) u toward the origin at vertical FOV 50 degrees. The eye view is (0,25.6,96) u toward (0,8,0), FOV 70 degrees, with unshrunk rig scale 8/1.75. The eye is 1.6 blocks up and 6 blocks out, inside the 8-block field.

- `pyro_conflag_field_render_preview.html`: interactive real-model clip, scale/camera controls and tick table.
- `pyro_conflag_field_render_contact.png`: all 16 native top-down frames.
- `pyro_conflag_field_render_vs_concept.png`: frames 1,3,5,7,8,11,14,16 beside the unchanged eight-cell concept, composited on grey.
- `pyro_conflag_field_render_frame_08_eye.png`: the held field from the specified eye position.
- `pyro_conflag_field_render_handoff.png`: rim frame 24 and field frame 8 at identical scale. The rim panel reuses its committed native contact-sheet cell and its documented identical camera, without opening or editing the rim project.
- `pyro_conflag_field_render_runtime.gif`: 72 encoded frames, 50 ms each, total 3.6 seconds.
- `pyro_conflag_field_render_end_hidden.png` and `_render_hidden.png`: hidden-state native checks.

The contact sheet, final versus-concept comparison, handoff and eye view were visually inspected. Automated contract checks cover direct frame ownership, counts, flatness, origins and rotations, one textured face per plane, embedded/editable byte equality, palette, binary alpha, rim/fringe pixel-corner bounds, attached fringe components, exact charged glyph remapping, every clip key, the hidden end state and GIF cadence. Generator, pack and manifest results are recorded in the handoff report. Minecraft lighting, display scaling against terrain and integration with the explosion/particle layer remain in-game checks.
