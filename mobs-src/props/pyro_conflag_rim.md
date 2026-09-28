# Conflagration channel rim

The owner's concept art is used directly: 24 registered frames form the clockwise ground charge for Conflagration's 70-tick channel. Each supplied `rim_NN.png` is copied unchanged, including its semi-transparent alpha, into one embedded texture and its editable `pyro_conflag_rim_tex_frame_NN.png` counterpart. The supplied recut frames blend cold into charged over an **18-degree leading edge** and a **45-degree tail** where the charge began. There is no repainting, palette conversion, alpha thresholding or layer separation.

## Geometry and registration

The hierarchy is `root -> fx -> frame_1..frame_24`, with the existing bone names, UUIDs, origins and rotations retained. Every frame owns exactly one zero-thickness horizontal plane: **1 element per frame, 24 total**. Only its up face is textured. Full-texture UV is `[0, 0, 512, 512]`, without rotation; image top maps to north (-Z), image right to east (+X). Frame 1's bright head sits at north, and charging proceeds clockwise when viewed from above.

Each plane spans **x/z -38.1275..38.1275 u**, a **76.255 x 76.255 u** square centred on the origin. Every frame plane is at **y = 0.20 u**, with no rising offset during the charge. Transparent margins belong to the registered drawing; the carrier bounds do not define the ring radius.

The supplied registration places the true-radius ring edge at **28 u = 1.75 blocks**. This corresponds to 188.000787 source pixels from image centre at 512 / 76.255 pixels/u. Soft glow, flames and other artwork remain exactly as supplied; they are not clipped to a radial alpha mask.

## Textures

There are 24 embedded, editable **512 x 512 RGBA PNGs**, named `pyro_conflag_rim_tex_frame_01.png` through `_24.png`. Embedded PNG bytes and editable copies match the owner's corresponding source files byte-for-byte. Semi-transparent alpha is preserved exactly. Textures use emissive, double-sided preview rendering; only the up face carries the image, avoiding a second mirrored drawing.

## Clips and runtime

`fuse` is the unchanged **1.20-second hold** clip. Every frame bone has step scale keys on ticks 0..24. Frame N is shown at scale 1 during `[N-1, N)`; other frames use scale 0.001. At tick 24 all frames are hidden. `hidden` remains a **1-second loop**, with all-hidden keys at ticks 0..20. No position or rotation animation channels are added. Every authored animation record is unchanged.

The plugin's 70-tick channel scheduling remains independent of this diagnostic authoring clip. `FLIPBOOKS.md` retains `pyro_conflag_rim | pyro_conflag_rim | fuse | 2`, and runtime keys remain `legendcraft:classes/pyro_conflag_rim_1` through `_24`.

At shrink 2 the item-model x/z bounds are **-11.06375..27.06375**, inside the generator's -16..32 box. Item display scale remains `2 * trueRadius / 1.75`; the unshrunk rig uses `trueRadius / 1.75`. Registration is centred on the origin, without recentering or ground snapping.

## Verification

Geometry was edited through native Blockbench APIs over the MCP, in an isolated session-owned project. The native codec supplied the exported elements and textures; existing bone metadata and animation records were retained. Verification checks every frame's sole element, constant plane height, full up-face UV, dimensions, embedded/editable/source byte equality, semi-transparent alpha and generated model bounds.

`pyro_conflag_rim_render_contact.png` is the current top-down contact sheet of all 24 native Blockbench meshes over #777777 grey, north up and east right. Each cell has a 92 u orthographic view width. The frame 1 head and clockwise sequence were visually inspected. `pyro_conflag_rim_render_side.png` shows frames 1, 12 and 24 side-on at the same y = 0.20 u. Cyan native plane edges are shown against a y = 0 ground line, with the vertical scale enlarged and labelled. Other render/preview files beside this model do not represent this texture pass.

Flipbook generation, pack build, manifest verification and post-commit drift results are recorded in `C:/Users/omarz/.claude/comms/pyro-rig-conflag-frames-r2-report.md`. Minecraft lighting, translucent sorting and terrain contact still require an in-game look.
