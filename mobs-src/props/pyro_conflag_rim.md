# Conflagration channel rim

Conflagration's ground rune chain charges clockwise during the Pyromancer ultimate's 70-tick channel. The plugin swaps one of 24 item models onto one ground display, then removes it for detonation. Each major piece follows its glyph: thick crosses and stepped hooks, with cardinal diamonds and boxed squares. Two small hook/bar fragments per sector overlap neighbouring outlines into a packed chain. There are no square backings behind crosses or hooks. Charged strokes carry white cores, yellow-orange faces and orange-red rims; cold strokes are warm red-brown with brighter red cores. Attached flame tongues lie flat on the ground.

## Registration and dimensions

The centre is the origin. North is -Z; sector 1 is centred there, and sectors 2..24 proceed clockwise from above in 15-degree steps. Frame N lights sectors 1..N. The 28 u nominal rim radius, 30 u absolute flame cap and runtime registration are unchanged.

| Feature | Dimensions |
| --- | --- |
| Cross pieces | Nominal 5.5..5.75 u across; 12..14-source-pixel strokes (1.5..1.75 u), before raster rotation |
| Stepped S/L hooks | Nominal 5.5 x 3.875 u; 12-source-pixel strokes (1.5 u) |
| Cardinal diamonds | 6.25 u tip to tip; centre radius 25.25 u |
| Boxed squares | 4.75 x 4.75 u before raster/radial clipping; 1.5 u strokes; screen-axis aligned |
| Gap fragments | 48 per frame, two per sector: short hooks about 1.5 x 2 u, bars about 1.5 x 0.75 u; stroke widths 6..7 pixels (0.75..0.875 u); clipped at the heat-sector boundary |
| Outline and bevel | One source texel (0.125 u) dark silhouette outline and one lighter inset edge; lower-right recess shading |
| Glyph cores | 4 source pixels (0.5 u) down the middle of major strokes; 2 pixels (0.25 u) in fragments |
| Flame tongues | Nominal 6..8 source texels long (0.75..1 u), 3..4 texels wide (0.375..0.5 u), narrowing at the tip; raster diagonals can span an additional pixel; attached root overlap removed from the flame layer |
| Piece/fragment envelope | 22.000000..28.463244 u, measured at opaque pixel corners |
| Flame envelope | 23.143911..29.433452 u, measured at opaque pixel corners; below the 30 u cap |
| Carrier planes | Two 64 x 64 u planes per frame, x/z -32..32 u, zero thickness |
| Block plane y | 0.20 + 0.02(N-1) u |
| Flame plane y | Block plane y + 0.06 u; no opaque overlap |
| Complete geometry y | 0.20..0.72 u |

The major pieces and fragments form one eight-connected opaque chain, with touching or overlapping outlines and small ground cutouts inside the glyphs. There are no long one-texel links. Older lit pieces have two tongues; the three newest have three. Frame 24 has three per major piece, 72 nominal tongues total. Most point outward; selected third tongues point inward. The newest piece remains white-yellow with two pale tongues, including in frame 24. All flames attach to the chain and have no opaque overlap with the lower plane.

28 u = 1.75 blocks. `FLIPBOOKS.md` remains `pyro_conflag_rim | pyro_conflag_rim | fuse | 2`. Item display scale remains `2 * trueRadius / 1.75`; the unshrunk rig uses `trueRadius / 1.75`. Runtime keys remain `pyro_conflag_rim_1` through `pyro_conflag_rim_24`. No recentering or ground snapping is introduced.

## Rig and timing

Unyawed `root -> fx -> frame_1..frame_24`. Each frame directly owns two elements: glyph/fragment plane and flame plane. **Two elements per frame, 48 total**, within the 48-element per-frame budget. The pieces are texture artwork, not separate cubes. The elements, outliner and animation data compare equal to r3 commit `5055d8c`.

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
| Cold outline | `#171310` (`#241F1B` remains allowed) |
| Cold bevel | `#594037` |
| Cold glyph and lit edge | `#B7331A`, `#E8500F` |
| Flames | `#E8500F`, `#FF8A00`, occasional `#B7331A` tips; head licks `#FFD24A`/`#FFF4E0` |

All nine used colours belong to the r3 palette. `#241F1B` and the approved greys `#4A423C` and `#3B3430` remain allowed but unused. No colours were added.

## Renders and verification

The existing MCP-native geometry was loaded into an isolated Blockbench project, textures refreshed through native Texture APIs in an Undo transaction, and the result exported through the native project codec at `http://localhost:3000/bb-mcp`. Mutations and rendering targeted project UUID `55179775-ccf4-005c-55eb-6e20ae0ffbb0`. Other rigs and sessions' render slots were not modified.

The `PROP-PREVIEW.md` generator produced a baseline preview and the final real-model HTML. The final render loop used cloned native Blockbench geometry and actual evaluated animation states in an isolated Three.js renderer. The HTML has 8/12-block radius choices, clip/tick controls, top/bystander views and frame turnaround. HTML interaction was not browser-tested in this session.

- `pyro_conflag_rim_render_contact.png`: all 24 frames, north up.
- `pyro_conflag_rim_render_vs_concept.png`: frames 1, 4, 7, 10, 13, 16, 20, 24 beside the eight untouched concept cells at matched nominal ring scale.
- `pyro_conflag_rim_render_zoom_vs_concept.png`: frames 1/24 above their north-east quarter enlargements, beside the owner's unchanged cell 1/8 zoom panel. Both full cells are 443 px; the quarter crop is x 221..443, y 0..222, enlarged to 443 px with nearest sampling. Native full views are fitted to 429 px within the grey cell using the same scale ratio as the full comparison.
- `pyro_conflag_rim_render_frame_12_eye.png` and `_render_frame_24_eye.png`: eye-level views of the 8-block-radius ring.
- `pyro_conflag_rim_render_fuse.gif`: 72 frames at 20 fps, each of the 24 drawings held for three ticks.
- `pyro_conflag_rim_render_end_hidden.png` and `_render_hidden.png`: empty-ground checks.
- `pyro_conflag_rim_render_preview.html`: final real-model interactive preview.

Ground is `#777777`, sky `#11141C`. Top camera: (0,74,0.001) u, target origin, FOV 50 degrees. Eye camera: (0,25.6,96) u, target (0,8,0) u, FOV 70 degrees, rig scale 8/1.75. That eye is 1.6 blocks high and 6 blocks from the centre, inside the ring.

Both final vs-concept renders, the full contact sheet and the final eye view were visually inspected before commit. The glyph silhouettes, touching fragment chain and enlarged tongues were checked against the concept at full-cell and quarter-zoom sizes. Checks pass for unchanged geometry/outliner/clips, per-frame count, flatness, single textured face, embedded/editable equality, binary alpha, exact palette, pixel-corner radial bounds, 24 clockwise heat sectors, attached nonoverlapping tongues, fuse/hidden keys, hidden renders and GIF cadence. All 96 rim outputs equal a fresh generator build; generated keys, shrink and geometry remain unchanged. The pack build, manifest and post-commit drift output are recorded in the handoff report.

## Remaining differences from the concept

The chain is more regular and finely rastered than the concept. Crosses and stepped hooks repeat symmetrically; boxed squares have open centres rather than the reference's inner cross motifs. The flame tongues are larger than r3 and visible along the charged arc, but remain smaller and more evenly distributed than the concept's broad irregular flame masses. Their specified 6..8-source-texel bodies are literal; diagonal raster coverage can add one pixel. The head is a crisp white-yellow glyph rather than a soft flare. Binary alpha omits bloom and translucent haze; detached speckles and particles remain absent. At the shallow eye camera, the flat ground artwork is strongly foreshortened. Minecraft lighting, terrain contact, 8/12-block display scaling and playback still need the in-game look.
