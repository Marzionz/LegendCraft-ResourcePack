# Conflagration scorched field

Conflagration's ground flash opens into warm fractured lava rock, a thick white-yellow rim with a jagged flame crown, and 24 charged ground glyphs. The field holds, then cools through eight drawings into brown char with broken dark-red edges and faint cracks and runes. One item display swaps 16 flat drawings. The separate `pyro_conflag_explosion` owns the first 16 ticks of height; this prop stays on the ground. The reference is the unchanged eight-cell `pyro_conflag_field_concept.png`.

## Registration and geometry

The origin is the centre at ground level; north is -Z. The nominal rim outer radius is **28 u = 1.75 blocks**, matching `pyro_conflag_rim`. The crown stays inside the **31 u cap**. Measured at opaque pixel corners, the rim reaches **27.996652 u** and the crown **30.993951 u**.

All carrier planes span x/z **-32..32 u**. Transparent margins do not define the visible field. The layer order is disk **y 0.14**, cracks **0.26**, rim **0.40**, runes **0.54**, fringe **0.68**, flash **1.00 u**. All planes have zero thickness and only their up face textured. There are no vertical elements, loose rock chunks, detached embers or particle speckles.

The generator shrinks by **2**. Scale the generated item by **2 * trueRadius / 1.75**: 9.142857 at radius 8, or 13.714286 at radius 12. Scale the unshrunk authoring rig by `trueRadius / 1.75`. Do not re-centre or ground-snap it. The visible rim diameter becomes 16 or 24 blocks; the fringe cap becomes 17.714286 or 26.571429 blocks across.

Unyawed hierarchy: `root -> fx -> frame_1..frame_16`, with every pivot at [0,0,0]. Each frame owns its elements directly. **68 total elements; maximum 5 per frame**, below the 48-per-frame budget. Geometry, outliner and animation data remain equal to r1.

## Frames and runtime timing

`blast` remains a **0.80-second hold clip**. Each frame bone has a step scale key at every tick 0..16. Frame N shows on [N-1,N), at scale 1; hidden scale is 0.001. At tick 16 all frames are hidden. `hidden` is a one-second loop, all frames hidden at every tick 0..20. There are no position or rotation animation channels.

**Runtime timing belongs to the plugin, independently of the diagnostic authoring clip.** Frames 1..8 first appear on ticks 0..7 from detonation. Frame 8 stays worn through tick 59. Frames 9..16 start on ticks **60, 61, 63, 64, 66, 67, 69, 70**. The display is removed at **tick 72**.

| Frame | Authoring interval, ticks | Runtime interval, ticks | Elements | Drawing |
| --- | --- | --- | ---: | --- |
| 1 | [0,1) | [0,1) | 1 | 60% sun: 4.8 u body radius, cross rays to 9.6 u |
| 2 | [1,2) | [1,2) | 1 | Full sun: 8 u body radius, cross rays to 16 u |
| 3 | [2,3) | [2,3) | 4 | 14 u expanding ring, dark petals, central star and outward rays |
| 4 | [3,4) | [3,4) | 4 | 22 u expanding ring, dark petals and central star |
| 5 | [4,5) | [4,5) | 4 | Full warm fractured disk, hot rim and flame crown |
| 6 | [5,6) | [5,6) | 5 | Yellow-orange glyph ignition |
| 7 | [6,7) | [6,7) | 5 | White-yellow glyphs at full heat |
| 8 | [7,8) | [7,60) | 5 | Steady full field; held by runtime |
| 9 | [8,9) | [60,61) | 5 | Cooling 1/8; yellow rim and glyph cores |
| 10 | [9,10) | [61,63) | 5 | Cooling 2/8; orange glyphs and cracks |
| 11 | [10,11) | [63,64) | 5 | Cooling 3/8; orange-red rim |
| 12 | [11,12) | [64,66) | 5 | Cooling 4/8; broken red perimeter begins |
| 13 | [12,13) | [66,67) | 5 | Cooling 5/8; shrinking red crown, chipped disk |
| 14 | [13,14) | [67,69) | 5 | Cooling 6/8; darkening broken edge |
| 15 | [14,15) | [69,70) | 5 | Cooling 7/8; faint residual crown |
| 16 | [15,16) | [70,72) | 4 | Cold brown char; faint red glyphs/cracks; no crown |

`FLIPBOOKS.md` remains `pyro_conflag_field | pyro_conflag_field | blast | 2`. Runtime item keys remain `legendcraft:classes/pyro_conflag_field_1` through `_16`.

## Painted dimensions and palette

There are **68 embedded and editable 512 x 512 PNGs**, named `pyro_conflag_field_tex_<layer>_<frame>.png`. Painting uses a 256 x 256 grid and nearest-neighbour 2 x 2 stored clusters: one paint texel is **0.25 u**, one stored texel **0.125 u**. The disk spans about 224 paint texels / 448 stored texels, exceeding the 192-pixel floor before upscaling. Alpha is binary **0/255**.

| Feature | Dimensions and construction |
| --- | --- |
| Ground glyphs | About 4 u across: longest glyph body axis 15 paint texels / 3.75 u, plus a one-paint-texel edge; total envelope up to 4.25 u across that axis |
| Glyph placement | 24 centres at radius 22.6 u, 15-degree steps, tile 1 north, clockwise from above; no block background |
| Glyph strokes | Rim r4's actual white core drawings, nearest-sampled to a 13-paint-texel longest axis; a one-paint-texel yellow body expansion and one-paint-texel red-orange outside edge give the retained 17-paint-texel / 4.25 u envelope; cardinal checker diamonds retain a filled diamond face |
| Glyph radial envelope | **19.623009..25.455844 u** at pixel corners; boxed-square diagonal corners extend beyond the approximate 20..25 u band to preserve glyph size |
| Rock plates | Irregular cells around a 4.4 u spacing, roughly 3..5 u across; warm brown faces, broad bevel facets and a narrow dark seam |
| Main cracks | Twelve connected fork paths starting near the centre; three-paint-texel orange body and one-paint-texel yellow core inside a four-paint-texel red-orange footprint, about 0.75..1 u overall; branch intersections are wider |
| Hot rim | Nominal **2.5 u bright band**, radius 25.5..28: a **1 u #FFF4E0 core** between **0.75 u #FFD24A shoulders**; white centreline varies by up to 0.22 u and the inner shoulder by up to 0.25 u; conservative paint-pixel corner clipping holds the outer bound below 28 u |
| Inward heat | Another **2.75 u** inward from the bright band: **0.75 u #FF8A00**, **1 u #E8500F**, **1 u #B7331A**, with warm facets and darker seams retained; boundary variation and raster corners put the full layer's innermost opaque corner at **22.360680 u**; frames 5..11, dimmed through cooling |
| Crown | **31 overlapping flame masses**, **16 split into two tips**: 47 nominal tips with mixed heights, concave notches, broad shoulders and leans up to 1.15 u; nominal extension **1.5..2.98 u**, full-field root width **4.8..7.5 u**, clipped within 31 u; early-frame widths scale with ring radius |
| Flash | Frame 1 body radius 4.8 u and rays 9.6 u; frame 2 body radius 8 u and rays 16 u; ragged corona extends about 1.08..1.32 times body radius |
| Early blast | Ring outer radii 14/22 u; jagged rays reach about 2..4 u beyond the ring, with a bright four-point central star and diagonal points |
| Cold edge | Radially irregular, increasingly interrupted red fragments from frame 12 onward; no continuous circular stroke in frames 14..16 |

Allowed palette remains **#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310 #594037 #39281F**. Ten colours are used; the two greys #4A423C and #3B3430 remain allowed but unused. No colours were added.

The rock uses **#39281F** faces and **#594037** bevel facets, with #241F1B seams. Hot glyphs use #FFF4E0 cores, #FFD24A bodies and #E8500F edges. Cracks use #FFD24A inside #FF8A00/#E8500F. The bright rim uses #FFF4E0 and #FFD24A; its inward heat steps through #FF8A00, #E8500F and #B7331A. Crown tongues grow from overlapping yellow roots into orange bodies with red-orange edges and dark-red tips. The crown has no dark separator at its roots. Cooling moves through orange and red to #B7331A/#7A1F10; late glyphs retain brighter thin cores over dark-red bodies. Heat changes by discrete palette and silhouette steps, never translucent fades.

The crown retains its full height in cooling frame 9 while losing white/yellow heat, then uses height factors 0.90, 0.78, 0.65, 0.50, 0.35 and 0.22 in frames 10..15. Roots narrow and selected masses disappear in late cooling. Frame 16 has no crown. The broken rim drawings in frames 12..16, all rock layers, all cracks and all sun/burst flash layers remain byte-identical to r2.

## Rune continuity with the channel rim

The glyph silhouettes follow rim **r4, commit 07d6568**, using its charged `pyro_conflag_rim_tex_band_24.png`. The actual connected white cores of its major hooks, crosses and open squares are isolated from the small joining fragments and uniformly resized; the cardinal checker cores sit on diamond faces. The six-tile sector repeats **diamond checker, hook, cross, boxed square, cross, opposite hook**. Cardinal tiles 1/7/13/19 are diamond checkers; diagonal tiles 4/10/16/22 are open boxed squares, without the former centre dot. Existing bearings, 22.6 u centre radius, clockwise ordering and r2 size remain.

Only the glyph drawings transfer. There are no backing blocks, sockets, links or gap fragments behind the field's free-standing ground glyphs. R4's tile 24 has an isolated hook core, so it is sampled directly. Frame 6 lights the glyphs yellow-orange, frames 7/8 make their cores white, and cooling retains the same silhouettes through frame 16.

## Preview, renders and verification

The original MCP-native geometry was loaded into an isolated Blockbench project through `http://localhost:3000/bb-mcp`. Native Texture APIs refreshed the paintings in a scoped Undo transaction; the native project codec exported the model. The codec's group records were joined by UUID into the established inline outliner serialization for the pack reader. Editor selection flags and empty preview-created root/fx animators were normalized after inspection. Geometry, outliner and every authored animation key compare equal to r2 **c53774c**. Calls targeted project **203baad6-249a-68d2-18d6-5f9b96287131** and restored the previously selected project. Other rigs were not edited.

`PROP-PREVIEW.md`'s `prop_preview.py` generated the baseline and final real-model HTML. The final page has runtime, authored-blast and hidden timing modes; 8/12-block radius controls; top and player-eye cameras; a timeline and frame turnaround. Headless Chrome checks exercised the runtime boundaries, radius control, authored mode and hidden mode without script errors. The displayed full-glow preview was visually inspected.

Native renders clone this project's actual Blockbench meshes at the evaluated animation state into an isolated Three.js scene. They use #777777 ground, #11141C sky and nearest texture sampling. Top camera: (0,74,0.001) u toward the origin, FOV 50 degrees, north up. Eye camera: (0,25.6,96) u toward (0,8,0), FOV 70 degrees, rig scale 8/1.75. The eye is 1.6 blocks up and 6 blocks out, inside the field.

- `pyro_conflag_field_render_preview.html`: interactive real-model runtime and authoring preview.
- `pyro_conflag_field_render_contact.png`: all 16 native top-down frames.
- `pyro_conflag_field_render_vs_concept.png`: frames 1,3,5,7,8,11,14,16 beside the unchanged eight concept cells.
- `pyro_conflag_field_render_zoom_vs_concept.png`: frames 7/16 above their north-east quarter enlargements, beside the owner's unchanged concept 4/8 zoom. Full cells are 443 px; quarters crop x 221..443, y 0..222, enlarged to 443 px with nearest sampling.
- `pyro_conflag_field_render_frame_08_eye.png`: held field at the specified eye position.
- `pyro_conflag_field_render_handoff.png`: rim **r4** frame 24 beside field frame 8, identical native camera and scale. The read-only rim panel comes from its committed contact sheet.
- `pyro_conflag_field_render_runtime.gif`: 80 encoded frames at 50 ms each. Ticks 0..71 show the exact runtime schedule; tick 72 shows removal. Ticks 72..79 are an empty 0.4-second preview tail to make removal visible before looping, not extra field lifetime.
- `pyro_conflag_field_render_end_hidden.png` and `_render_hidden.png`: empty-ground native checks.

Both final vs-concept images, the contact sheet, handoff, eye view and browser screenshot were visually inspected. The concept image and both right-hand comparison panels remain unchanged. Verification covers unchanged geometry/outliner/clips, counts, flatness, single up faces, embedded/editable byte equality, binary alpha, allowed palette, rim/crown pixel-corner bounds, every animation key, hidden renders, runtime cadence and all 100 generated field files. The browser checks exercised all runtime ticks 0..72, both radii, all three timing modes, both cameras and frame turnaround without script errors. Pack/build and post-commit drift output are in `C:/Users/omarz/.claude/comms/pyro-rig-conflag-field-r3-report.md`.

## Remaining differences from the concept

The rim r4 checker diamonds, hooks and rotated crosses replace the concept's diamond-stars and simpler crosses. Boxed-square corners occupy a slightly wider radial band to preserve their size. Rock cells are smaller and more geometrically faceted than the concept's large soft clusters; the thick branching cracks keep their r2 distribution rather than concentrating farther inward. The broad rim and stepped inward heat are more regular and sharply banded than the concept's softer, broken illumination. The crown now has joined yellow roots, broad orange bodies and split red tips, but its low 31 u cap and crisp raster outlines still produce a flatter, tidier fire silhouette than the reference. The cold edge retains r2's larger dark gaps. Binary alpha omits additive bloom and translucent haze. Loose chunks and speckles remain absent because the plugin supplies particles.

Minecraft lighting, terrain contact, display scale at 8/12 blocks and the combined explosion/particle moment still require an in-game look.

## History

- **Round 2, c53774c:** bold ground glyphs, warm fractured rock, thick cracks, larger sun and burst drawings, broken cold edge.
- **Round 3:** expanded the bright rim and painted inward heat in frames 5..11; replaced every crown with overlapping, leaning and split flame masses; matched the free-standing glyphs to rim r4. The owner authorized scripted painting and completion through commit/report without a separate preview approval turn. Runtime, geometry, palette, binary alpha, registration and shrink remain unchanged.
