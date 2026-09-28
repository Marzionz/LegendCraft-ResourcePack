# Conflagration channel rim

Conflagration's ground rune ring charges clockwise during the Pyromancer ultimate's 70-tick channel. The plugin swaps one of 24 item models onto one ground display, then removes it for detonation. The art is a chunky chain of beveled rune blocks, with four cardinal diamonds, four boxed squares, hooks and crosses. The charged arc carries a flat cutout flame fringe on both edges. There are no raised flames, towers, embers or particle speckles.

## Registration

The ring is centred at the origin. North is -Z; tile 1 is centred there, with tiles 2..24 proceeding clockwise from above at 15-degree intervals. There are **24 painted tiles**, unchanged. Frame N lights tiles 1..N, covering N/24 of the angular sectors.

The ordinary blocks are 4.5 u deep, from radius 23.5 to 28 u; their tangential rectangle is 6.8 u wide before trimming to its sector and circular registration. Narrow 2.3 u radial links join the nodes. The four diamond nodes are centred at radius 25.25 u and measure 6.5 u tip to tip. Boxed-square nodes are 5.1 u across, with about 6.5 u of radial envelope after trimming. Node artwork stays within radii 22..28.5 u. All opaque pixel corners, rather than just pixel centres, respect those limits. Measured combined band/node artwork spans radii **22.000000..28.465988 u**.

Glyph strokes are 0.625..0.75 u thick. Cross/hook marks span about 3 u, boxed-square glyphs 2.6 u, and the diamond checker is about 3.2 u across. A stepped light top-left bevel and dark bottom-right bevel make each block read as relief while remaining planar.

The halo grows along the charged arc and reaches its greatest coverage in frame 24. Its measured full envelope is **20.155644..29.992707 u**; its outer edge remains inside 30 u, at most 2 u outside the band's 28 u outer radius. Orange/red tongues are connected to the rim, with no detached components. The inner fringe reaches about 1.85 u inside the deepest node edge.

The two carrier planes each span x/z -32..32 u with transparent margins. Their visible art, not the transparent rectangle, defines registration. Band and glyphs share one painted layer; the halo uses a separate plane 0.06 u above it and has no opaque overlap with the band. Band y = 0.20 + 0.02(N-1) u; halo y = band y + 0.06 u. All geometry is zero-thickness and lies at **y 0.20..0.72 u**.

28 u = 1.75 blocks. `FLIPBOOKS.md` retains `pyro_conflag_rim | pyro_conflag_rim | fuse | 2`. The generated item restores the shrink using `2 * trueRadius / 1.75`; the unshrunk authoring rig uses `trueRadius / 1.75`. No recentering or ground snapping is required. Runtime keys remain `pyro_conflag_rim_1` through `pyro_conflag_rim_24`.

## Frames and rig

Unyawed `root -> fx -> frame_1..frame_24`; every frame directly owns its two elements. The 24 painted blocks are texture detail, not 24 separate elements. Total: **48 elements; 2 per frame**, below the 48-per-frame budget.

`fuse` is a 1.2-second hold clip. Every frame bone has one scale key per tick from tick 0 through 24, with step interpolation: shown scale 1 for its one tick, hidden scale 0.001 otherwise. Frame N shows on [N-1, N). At tick 24 every frame is hidden, so the clip **ends hidden**. `hidden` is a one-second loop with 21 all-hidden tick keys per frame. There are no position or rotation animation channels.

The newest block is white-yellow; its two predecessors carry yellow centres, and older blocks have orange faces with yellow glyphs and white-hot stroke cores. Uncharged blocks are charcoal-brown with dark ember-red strokes. Frame 24 gives every glyph a white-hot face while preserving orange block faces and the full halo.

| Frame | Visible interval | Lit tiles | Band y (u) | Halo y (u) | Elements |
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

48 embedded, editable 512 x 512 PNGs: `pyro_conflag_rim_tex_band_01.png` through `_24.png`, and `pyro_conflag_rim_tex_halo_01.png` through `_24.png`. Each samples a 64 u canvas at 8 pixels/u. Ordinary blocks therefore have about 54 x 36 pixels of paint, exceeding the former 32 x 32 tile density. At a 12-block field radius the effective density is about 18.7 texels per world block. The halo uses deliberately stepped 2-pixel clusters. All texture alpha is binary 0/255; every plane has only its up face textured and uses double-sided preview rendering.

Approved palette: `#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`.

Two added brown mid-tones: **#594037** (warm bevel) and **#39281F** (charcoal-brown face). The final PNGs use those two additions plus eight approved colours; `#4A423C` and `#3B3430` remain allowed but unused. No other opaque RGB values occur.

## Mapping to the concept

`pyro_conflag_rim_concept.png` remains the untouched eight-cell source. The adaptation preserves its alternating block silhouettes, cardinal diamond checkers, boxed squares, hooks/crosses, ember-red uncharged runes, orange charged blocks, hot head and thickening inner/outer flame fringe. The final frame keeps colour in the band instead of whitening the whole ring. The 24-sector timing contract starts at north even where a concept cell's hot head falls elsewhere.

This is a crisp binary-alpha interpretation: the concept's soft glow, semi-transparent fire haze and scattered speckles are not reproduced. The halo is constrained to 30 u even where a reference lick extends farther. The glyph vocabulary is redrawn on a regular 24-sector layout, not traced pixel for pixel from the eight-cell sheet.

## Verification and renders

Geometry and animation were authored with native Cube, Group, Texture and Animation APIs through the Blockbench MCP, in a separate UUID-scoped project. Export uses Blockbench's project codec; no external script generated geometry JSON. Texture painting used scripts. The prop preview was generated from the saved `.bbmodel` through `PROP-PREVIEW.md`'s tool, with ground registration, binary cutout depth, 8/12-block scale choices and camera controls. Browser automation was unavailable in this session, so interaction with the HTML was not independently browser-tested. Native Blockbench geometry and real animation states supplied all final renders; the renderer used an isolated scene so existing sessions' offscreen views were untouched.

The ground is mid-grey `#777777`, with a dark `#11141C` sky. Top-down renders use camera (0,74,0.001) u, target origin, vertical FOV 50 degrees. Bystander frames use (0,25.6,96) u, target (0,8,0) u, vertical FOV 70 degrees, with the rig scaled by 8/1.75. That is an eye 1.6 blocks high and 6 blocks from the centre, **inside the 8-block field**, so the image shows the far arc rather than the whole ring.

- `pyro_conflag_rim_render_preview.html`: real-model interactive preview and tick table.
- `pyro_conflag_rim_render_contact.png`: all 24 frames, north up.
- `pyro_conflag_rim_render_vs_concept.png`: frames 1, 4, 7, 10, 13, 16, 20, 24 in a 4 x 2 panel beside the eight reference cells at matched ring scale; reference alpha is composited on the same grey.
- `pyro_conflag_rim_render_frame_12_eye.png` and `_render_frame_24_eye.png`: the requested scaled eye views.
- `pyro_conflag_rim_render_fuse.gif`: 72 encoded frames at 20 fps, each art frame held for three 50 ms ticks; total 3.6 seconds.
- `pyro_conflag_rim_render_end_hidden.png` and `_render_hidden.png`: empty-ground end/loop checks.

The side-by-side render was visually inspected before commit. Contract checks pass for topology, counts, flatness, single textured faces, embedded/editable PNG equality, palette, binary alpha, all opaque-pixel radial bounds, clockwise heat sectors, attached halo components, every fuse and hidden key, the hidden end state, and GIF cadence. Generated frame keys, geometry and texture bytes are verified against the generator. Pack build, manifest and post-commit drift output are recorded in the handoff report. Minecraft lighting, display scaling and particle integration remain in-game checks; no plugin code or deployment is part of this asset.
