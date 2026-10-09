# Conflagration scorched field

The owner's concept art is used directly: 16 registered frames show the ground flash, hot fractured field and cooling residue. Each supplied `field_NN.png` is copied unchanged, including its semi-transparent alpha, into one embedded texture and its editable `pyro_conflag_field_tex_frame_NN.png` counterpart. All burst cells share one registered centre. Cooling frames 9..16 use concept cell 4's art recoloured cooler in place, so the rock pattern and field footprint stay fixed while fading. The separate explosion prop owns height; this prop stays flat.

## Geometry and registration

The hierarchy is `root -> fx -> frame_1..frame_16`, with the existing bone names, UUIDs, origins and rotations retained. Every frame owns exactly one zero-thickness horizontal plane: **1 element per frame, 16 total**. Only its up face is textured. Full-texture UV is `[0, 0, 384, 384]`, without rotation; image top maps to north (-Z), image right to east (+X).

Each plane spans **x/z -42.414..42.414 u**, an **84.828 x 84.828 u** square centred on the origin. Every frame plane is at **y = 0.14 u**, including the two opening flash frames. Transparent margins belong to the registered drawing; carrier bounds do not define the visible field radius.

The supplied full-field registration places the true-radius ring edge at **28 u = 1.75 blocks**. This corresponds to 126.750601 source pixels from image centre at 384 / 84.828 pixels/u. Early flash and expanding-ring drawings retain their supplied size within the same registered canvas. Flames, glow and scattered artwork are not radially clipped or removed.

## Textures

There are 16 embedded, editable **384 x 384 RGBA PNGs**, named `pyro_conflag_field_tex_frame_01.png` through `_16.png`. Embedded PNG bytes and editable copies match the owner's corresponding source files byte-for-byte. The project texture resolution is 384 x 384, and UV covers the full texture. Fixed per-texel grain on the rock and glow gives about 16 texels per block across the ring at the 8-block field. Semi-transparent alpha is preserved exactly, with no binarisation, palette conversion or repainting. Textures use emissive, double-sided preview rendering, with only the up face carrying the image.

## Clips and runtime

`blast` remains the **0.80-second hold** clip. Every frame bone has step scale keys on ticks 0..16. Frame N is shown at scale 1 during `[N-1, N)`; other frames use scale 0.001. At tick 16 all frames are hidden. `hidden` remains a **1-second loop**, with all-hidden keys at ticks 0..20. Every authored animation record is unchanged, with no position or rotation channels added.

Runtime timing remains independent of the diagnostic authoring clip:

| Frame | Authoring ticks | Runtime ticks | Elements |
| --- | --- | --- | ---: |
| 1 | [0,1) | [0,1) | 1 |
| 2 | [1,2) | [1,2) | 1 |
| 3 | [2,3) | [2,3) | 1 |
| 4 | [3,4) | [3,4) | 1 |
| 5 | [4,5) | [4,5) | 1 |
| 6 | [5,6) | [5,6) | 1 |
| 7 | [6,7) | [6,7) | 1 |
| 8 | [7,8) | [7,60) | 1 |
| 9 | [8,9) | [60,61) | 1 |
| 10 | [9,10) | [61,63) | 1 |
| 11 | [10,11) | [63,64) | 1 |
| 12 | [11,12) | [64,66) | 1 |
| 13 | [12,13) | [66,67) | 1 |
| 14 | [13,14) | [67,69) | 1 |
| 15 | [14,15) | [69,70) | 1 |
| 16 | [15,16) | [70,72) | 1 |

Frame 8 remains worn through tick 59. Cooling frames start at ticks 60, 61, 63, 64, 66, 67, 69 and 70; the display is removed at tick 72.

`FLIPBOOKS.md` retains `pyro_conflag_field | pyro_conflag_field | blast | 2`. Runtime keys remain `legendcraft:classes/pyro_conflag_field_1` through `_16`. At shrink 2 the item-model x/z bounds are **-13.207..29.207**, inside the generator's -16..32 box. Item display scale remains `2 * trueRadius / 1.75`; the unshrunk rig uses `trueRadius / 1.75`. No recentering or ground snapping is introduced.

## Verification

Geometry was edited through native Blockbench APIs over the MCP, in an isolated session-owned project. The native codec supplied the exported elements and textures; existing bone metadata and animation records were retained. Verification checks every frame's sole element, constant plane height, full up-face UV, dimensions, embedded/editable/source byte equality, semi-transparent alpha and generated model bounds.

`pyro_conflag_field_render_contact.png` is the current top-down contact sheet of all 16 native Blockbench meshes over #777777 grey, north up and east right. Each cell has a 92 u orthographic view width. The flash, full-field and cooling sequence were visually inspected. `pyro_conflag_field_render_side.png` shows frames 1, 8 and 16 side-on at the same y = 0.14 u. Cyan native plane edges are shown against a y = 0 ground line, with the vertical scale enlarged and labelled. Other render/preview files beside this model do not represent this texture pass.

Flipbook generation, pack build, manifest verification and post-commit drift results are recorded in `C:/Users/omarz/.claude/comms/pyro-rig-conflag-frames-r2-report.md`. Minecraft lighting, translucent sorting, terrain contact and combined explosion/particle playback still require an in-game look.
