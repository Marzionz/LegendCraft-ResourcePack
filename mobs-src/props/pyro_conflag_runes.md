# Conflagration crossed rune rings

`pyro_conflag_runes` is a BetterModel motion prop worn at the caster's feet during Conflagration's 70-tick (3.5-second) channel. Play `spin` at authored speed and remove the prop on detonation. The plugin supplies the per-tick heat tint and brightness. This asset contains no detonation, glow layer, emissive map, or plugin code.

## Source and texture

Owner art: `C:/Users/omarz/.claude/comms/pyro-rune-ring-source.png`, 1122 x 1402 RGBA. Source SHA256: `4e76a7d20d4b7bd0db09ecdab7b02d190d171abd16c7d31d850ecc3252c62b14`.

The twelve glyphs are cropped from the lower strip, left to right, matching the original ring clockwise from its top cross. No glyph was redrawn. Each ring uses that same sequence, viewed from the prop's front (-Z) at time zero. Source glyphs remain upright at rest and rotate with their whole ring. A source strip dot is reused twice in every gap.

`pyro_conflag_runes.png` is a **512 x 512 RGBA atlas**, embedded in the model, editable beside it, and copied byte-for-byte to `src/assets/legendcraft/textures/entity/pyro_conflag_runes.png`. Texture SHA1: `40d971c3108e120a4f3cb77c97650a16a58482ea`.

For every cropped pixel, RGB becomes `round(0.2126 R + 0.7152 G + 0.0722 B)` in all three channels. Alpha is copied unchanged, including partial transparency. The bright source cores become near white and the source outlines stay dark; multiplying this neutral atlas by a tint supplies all colour. No blur, glow, repaint, alpha threshold, or resampling was applied to the atlas. Preview texture filtering and contact-sheet reduction use nearest neighbour.

Crop rectangles are exclusive-right/exclusive-bottom source pixel coordinates. They are packed in row-major 96-pixel cells, with a four-pixel inset, four cells per row. UV rectangles retain each crop's original size.

| Strip index | Source rectangle (left, top, right, bottom) |
| --- | --- |
| 1 | 29, 1204, 102, 1290 |
| 2 | 134, 1205, 198, 1284 |
| 3 | 218, 1202, 288, 1290 |
| 4 | 313, 1206, 362, 1285 |
| 5 | 392, 1208, 457, 1282 |
| 6 | 485, 1206, 552, 1285 |
| 7 | 573, 1201, 644, 1294 |
| 8 | 671, 1201, 726, 1292 |
| 9 | 751, 1203, 822, 1290 |
| 10 | 850, 1203, 906, 1292 |
| 11 | 932, 1200, 998, 1291 |
| 12 | 1030, 1207, 1093, 1286 |
| Dot | 109, 1235, 128, 1257 |

## Bones and geometry

Five bones: identity `root` at `[0,0,0]`; `plane_a -> ring_a` and `plane_b -> ring_b` under it. Both carrier/ring pairs pivot at `[0,19.25,0]`. The fixed carriers have rest yaw +45 and -45 degrees; their vertical planes intersect at 90 degrees along the caster's vertical axis. The carriers keep the spin axes local to their planes. The root has no 180-degree mob yaw, as required by the prop-root entry in `legendcraft-blockbench/SIGNS.md`.

Each ring has a **16 u / one-block glyph-centre radius**. Twelve 5 u tall glyph quads are spaced by 30 degrees, with width preserving each crop's aspect ratio. Two 0.78 u square dot quads sit at +11 and +19 degrees after each glyph, on the same radius. Every element has zero Z thickness in its ring plane, one textured north face, and texture `render_sides: double`; the other five faces are untextured.

**72 elements:** 24 glyphs and 48 dots; 36 per ring. No stand-in, floor or preview helper belongs to the rig.

The centre height differs from the brief's initial 16 u by an explicit inbox ruling. PYRO-R7 (`5dbe1087`) first raised it to 18.5 u for the bottom glyph; a subsequent full-loop probe found rectangular glyph corners dipping 0.734 u during rotation. The follow-up ruling accepted a constant **19.25 u** centre, preserving radius, glyph size and motion. The starting bottom quad edge is y=0.75 u; the full rotating envelope approaches ground contact without penetrating it. The continuous geometric envelope has minimum y=0.0158738657 u and maximum y=38.4841261343 u. No animated height compensation or bobbing is used.

## Clips and hook contract

| Clip | Playback | Length | Behaviour |
| --- | --- | --- | --- |
| `spin` | LOOP | **4 seconds / 80 ticks** | `ring_a` local Z 0 to +360 degrees; `ring_b` 0 to -360. Linear keys every 0.05 s, 4.5 degrees per tick. Both scales remain 1. |
| `hidden` | LOOP | 0.05 second / 1 tick | Both ring bones at uniform scale 0.001 at both endpoints. |

The ring normals remain fixed throughout `spin`; the glyphs orbit inside their own planes. Positive local Z moves the top glyph clockwise when looking from the prop's front; the other ring counter-rotates. The unyawed-root Z-roll convention comes from `SIGNS.md`; native world transforms and the rendered quarter-turns verify it here. Native Blockbench format 5.0 is retained rather than relabelled as a legacy format.

The rotational endpoints are equal **world orientations**, not equal numeric angles. PYRO-R7 explicitly applies PYRO-R6's unwrapped full-turn exception here. Replacing +/-360 with literal zero would reverse or erase the spin. All scale endpoints are exactly equal. At detonation, tick 70, the clip has completed 315 degrees of its 360-degree cycle; the hook removes it without a terminal flourish.

## Verification and renders

Built through Blockbench MCP `http://localhost:3000/bb-mcp`, using native groups, cubes, face UVs and animations. The `.bbmodel` comes from Blockbench's project codec, not script-generated geometry JSON. Native v5 `groups` metadata is also expanded into the outliner for the existing staging/preview readers; geometry and native animation values are unchanged by that compatibility metadata.

Native mesh vertices were checked at all 81 tick poses. Minimum y was **0.0160531952 u** and maximum y **38.4839468048 u**; the analytic full-turn corner envelope also stays above ground. Maximum start/end world-vertex difference was **3.552713678800501e-15 u**. The texture checks preserve source alpha and verify equal RGB channels, embedded/external pixel equality and the pack texture copy. The GIF contains 80 frames of 50 ms each, exactly one four-second loop.

- [Contact sheet](pyro_conflag_runes_render_contact.png): the first row repeats time zero with `#FF3A1A`, `#FF8A1A`, `#FFE14A`, `#FFFFFF`, and `#6AD8FF`; the next three rows show 15 poses from 0 through 4 seconds, including the identical endpoint pose.
- [One-loop GIF](pyro_conflag_runes_render_spin.gif): 640 x 640, 20 fps; no duplicated endpoint dwell.
- [Above still](pyro_conflag_runes_render_above.png): elevated oblique view, camera `(1.5,6,-3)` blocks. An oblique angle keeps the vertical quads visible instead of viewing both edge-on.
- [Interactive preview](pyro_conflag_runes_render_preview.html): generated by the skill's `prop_preview.py`, adapted to replay native Blockbench bone-transform samples with playback, scrub, orbit, rotation timeline and five tint choices. Browser rendering, playback/pause and blue tint selection were visually verified. Three.js and fonts load from the template's external CDNs.

All views use mid-grey ground, dark sky and a 2-block stand-in at the prop origin. Front camera: `(0,1.6,-6)` blocks, looking at `(0,1.125,0)`, 38-degree vertical FOV. PNG/GIF frames use the native Blockbench mesh geometry and native sampled transforms, rendered through a separate Three.js scene in Blockbench; a neutral basic material multiplies the actual atlas by each requested tint. This preview material does not alter the saved rig or bake brightness.

`deploy-rigs.ps1 -Prop -Rig pyro_conflag_runes`, `-Prop -Preflight`, `build.ps1`, and `check_pack_manifest.py --pack dist/LegendCraft-Pack-0.2.4.zip --source-tree src` passed. Staged model: `dist/props/models/pyro_conflag_runes.bbmodel`, SHA1 **`d25b1716c5d4a7cf9ddd604ea8204af5cefd0c73`**. The pack check found 439 item models, 13 sounds and 4 sounds.json; plugin-contributed assets remain unchecked without a plugin source. Pack SHA1: `5f0245cd8d7c0049c6f148a31d21643c04a8e241`.

In-game wearer anchoring, simultaneous charge-swirl readability, BetterModel tint/brightness, alpha sorting at plane intersections, and removal at tick 70 remain hook-time checks. This is a local BetterModel stage, not an mc-dev deployment.

## History and instruction precedence

2026-09-28: built the owner's crossed rune prop; incorporated both centre-height rulings and the rotational endpoint ruling; rendered, verified and staged it.

The brief overrides the skill's instruction to "END THE TURN" and its prohibition on committing before a later preview ruling; `PROP-PREVIEW.md` also says "Then the turn ends". This brief expressly requires continuing to the final commit/report. Its branch/path-only rules also override the skill's "commit and push authoring work there" instruction. No push or PR was made.

A shared Blockbench tab switch caused one height edit in another session's temporary horn preview. Its sole undo entry was identified by exact project UUID and action name and reverted immediately; this session wrote no other rig file. Subsequent operations select the rune project by UUID within each atomic MCP evaluation and restore the previous tab. The correction is recorded in the orchestrator inbox.
