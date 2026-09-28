# Knight Vanguard landing flash

One soft, translucent spotlight surrounds the Knight at the landing origin,
alongside `knight_vanguard_burst` on the same tick. The Knight stands inside the
light and remains visible. The opening low flash becomes a rising beam,
which holds its full peak size and fades, then leaves rising gold motes
and a last ground glint. There are no radial rays, stars, replacement shapes,
separate shafts, rods, ribbons or beam caps.

The unchanged [concept](knight_vanguard_flash_concept.png) is the original
1536 × 1024 four-by-two reference, not a texture. The owner's revision of
`2167665` supersedes its separated-pillar silhouette with one spotlight.

## Geometry and game size

Authored units are 16 per block. At full size, the outer light shell is 25.6 u
across (1.6 blocks), and the inner shell is 21.504 u across. Each shell consists
of two equal broad boxes centred on the origin, one at yaw 0° and one at 45°.
Both shells rise to 62 u on frame 5, 63 u on frame 6, and exactly
64 u / 4 blocks on frame 7. Frames 7–13 hold that same peak geometry, from
y = 0.42 u to y = 64 u. They stay straight as they rise. All beam cubes have
their top and bottom faces disabled. The white centre and streaks are texture
marks, with no separate core or streak geometry.

Each paired box layer forms one octagonal painted shell. Its side UV rectangle
is `[8 - 3/(sqrt(2)-1), 0, 8 + 3/(sqrt(2)-1), 16]`. Only bitmap columns 20–43
of 64 carry light, restricting each painted face to the central `sqrt(2)-1`
fraction of its width. The eight painted sections meet at octagon corners;
transparent margins avoid four overlapping surfaces. Front-face culling is
part of this construction. Rotated invisible bounds still fit within x/z ±20 u
and y ≤64 u, so shrink 4 remains sufficient.

Frames 10–13 retain both shell pairs at full peak width and height. Only texture
alpha changes: 75%, 50%, 25%, then 0% of each pixel's peak alpha. No narrowing,
shortening, sinking or scale change drives the fade. Frames 8–9 retain their
moving streak textures at peak geometry; the fade copies frame 9's last held-peak
texture so its streaks do not jump backward. No ribbons replace the beam.

All 24 contact-ray elements are deleted, twelve each from frames 1 and 2.
The 122 original ring, mote and glint elements retain their geometry and UVs.
The ring radius remains 20 u / 1.25 blocks; its height remains
`0.25 + 0.035 × (frame - 1)` u. Frames 10–13 use alpha-scaled copies of the
peak ring texture at the same 75%, 50%, 25%, 0% factors. Frame 13's beam and
ring geometry is fully transparent; frames 14–16 have no beam or ring geometry
and retain the original shrinking glint. Flat planes have one textured face. Gold
motes remain 0.85 or 1.35 u cubes and rise between frames.

There are 174 elements across the frame stack, at most 13 in any frame,
including the five fully transparent beam/ring elements in frame 13.

## Textures and transparency

All 29 editable PNGs are embedded byte-for-byte in the `.bbmodel`. The 17
original PNGs are unchanged; twelve fade copies have been added. Beam textures
are 64 × 64 with logical UV dimensions 16 × 16; ring/mote/glint textures are
16 × 16. Every filename starts with
`knight_vanguard_flash`. Partial alpha must not be binarized.

| Texture suffix | Alpha bytes | Purpose |
| --- | --- | --- |
| `_outer.png` | 0, 31 | Widest, faintest shell and haze; 12.16% maximum |
| `_inner.png`, `_inner_02.png` … `_inner_09.png` | 0, 31, 56, 89, 115 | Main gradient, painted centre and moving streaks |
| `_inner_10.png` | 0, 31, 56 | Historical texture, no assigned faces |
| `_inner_11.png` | 0, 31 | Historical texture, no assigned faces |
| `_ring.png` | 0, 31, 56, 255 | Original faint disc and bright thin band |
| `_ring_fade.png` | 0, 31 | Historical texture, no assigned faces |
| `_ray.png` | 89, 255 | Historical texture, no assigned faces |
| `_mote.png` | 255 | Original gold/brass cubes |
| `_glint.png` | 0, 89 | Original final centre glint |

Fade files are `_outer_fade_<frame>.png`, `_inner_fade_<frame>.png` and
`_ring_fade_<frame>.png`, for frames 10–13. Their RGB pixels exactly copy
`_outer.png`, `_inner_09.png` and `_ring.png`, respectively. All alpha bands,
centre marks and streaks scale together with `floor(source_alpha × factor + 0.5)`.

| Frame | Peak alpha factor | Outer alpha bytes | Inner alpha bytes | Ring alpha bytes |
| --- | --- | --- | --- | --- |
| 10 | 75% | 0, 23 | 0, 23, 42, 67, 86 | 0, 23, 42, 191 |
| 11 | 50% | 0, 16 | 0, 16, 28, 45, 58 | 0, 16, 28, 128 |
| 12 | 25% | 0, 8 | 0, 8, 14, 22, 29 | 0, 8, 14, 64 |
| 13 | 0% | 0 | 0 | 0 |

Reading upward from the ground, main inner bitmap rows 48–63 use alpha 89
(34.90%), rows 28–47 use 56 (21.96%), and rows 4–27 use 31 (12.16%). Rows
4–15 become progressively sparse transparent pixels; rows 0–3 are fully clear.
Edge columns use at most 31. The painted white centre reaches 115 (45.10%) only
near the ground and follows the upward fade. Two short one-pixel-wide streaks
climb four bitmap rows per frame; their alpha never exceeds 89.

Column colours are white `#FFFFFF`, ice `#E8F2FF`, pale blue `#A9CFFF` and sky
`#6FA8FF`; sky is its darkest colour. The original broader effect palette still
permits azure `#1F5FB0`, deep azure `#123C75`, gold `#FFD86B` and brass `#C49A3A`.
Motes retain gold and brass. Only the peak ring and motes use opaque pixels.
The retired standalone core and middle-shaft textures are removed.

## Rig and timing

`root → fx → frame_1 … frame_16`. Bone names, UUIDs, pivots and both animation
records are retained. Root rotation is `[0,0,0]`; there are no animated position
or rotation channels. `flash` plays once for 0.8 seconds. Scale keys at ticks
0–16 use `step`: 1 shown, 0.001 hidden. All frames are hidden at tick 16. The
separate `hidden` animation loops with all frames hidden.

| Frame | Tick interval | Milliseconds | Shape | Elements |
| --- | --- | --- | --- | --- |
| 1 | 0–1 | 0–50 | Low broad flash, ring, six motes; no rays | 11 |
| 2 | 1–2 | 50–100 | Broad flash rises, ring, six motes; no rays | 11 |
| 3 | 2–3 | 100–150 | One beam rises to 24 u / 1.5 blocks | 13 |
| 4 | 3–4 | 150–200 | Beam reaches 40 u / 2.5 blocks | 13 |
| 5 | 4–5 | 200–250 | Full beam, 62 u; eight motes | 13 |
| 6 | 5–6 | 250–300 | Full beam, 63 u; rising streaks | 13 |
| 7 | 6–7 | 300–350 | Peak, 64 u / 4 blocks | 13 |
| 8 | 7–8 | 350–400 | Peak geometry holds at 64 u; moving streaks | 13 |
| 9 | 8–9 | 400–450 | Peak geometry holds; last full-alpha texture | 13 |
| 10 | 9–10 | 450–500 | Full peak beam and ring, alpha ×0.75 | 13 |
| 11 | 10–11 | 500–550 | Full peak beam and ring, alpha ×0.50 | 13 |
| 12 | 11–12 | 550–600 | Full peak beam and ring, alpha ×0.25 | 13 |
| 13 | 12–13 | 600–650 | Beam and ring alpha zero; eight motes visible | 13 |
| 14 | 13–14 | 650–700 | Three motes and centre glint | 4 |
| 15 | 14–15 | 700–750 | Two motes and smaller glint | 3 |
| 16 | 15–16 | 750–800 | One mote and last glint | 2 |
| End | 16 onward | 800 onward | All frame bones hidden | 0 visible |

## Item-model contract

`FLIPBOOKS.md` remains `knight_vanguard_flash | knight_vanguard_flash | flash | 4`.
Play `legendcraft:classes/knight_vanguard_flash_1` through
`legendcraft:classes/knight_vanguard_flash_16`, each for exactly one tick at the
ground-level landing origin. Display scale is shrink 4, reversing generation's
division by 4, with no additional artistic scale or vertical offset. Draw at
full brightness; remove or hide the display after frame 16. This is an item
flipbook source, not a BetterModel deployment.

Generation writes 16 item definitions, 16 geometry models and 58 texture PNGs
for this asset. PNGs preserve the embedded bytes and partial alpha. Regeneration
removes `_1_5.png` and `_2_5.png` from the ray-era outputs and adds `_12_4.png`
and `_13_4.png` for the full-size inner-shell fade.

## Verification and renders

Geometry was revised in live Blockbench through MCP at
`http://localhost:3000/bb-mcp`, using native Cube, Group and Texture objects and
an undo transaction. Painting scripts produced PNGs only. Native export was
adapted from Blockbench 5's separate group records to the toolkit's 4.10 nested
outliner, omitting empty animators; this did not author geometry.
No plugin code or production generator changed.

The `PROP-PREVIEW.md` loop generated before and after pages from the actual rig.
The updated [interactive preview](knight_vanguard_flash_render_preview.html)
was regenerated with a two-block mannequin, the actual clip, scrubber
and timeline. Browser security policy blocked opening the local HTML this
session, so browser inspection of this revision is unverified; native
Blockbench captures below were inspected. It requires network access for the toolkit's three.js/font CDN
URLs. Cuboids use front-face culling; the ring/glint planes remain double-sided
in the inspection page. Playback defaults to 1× speed.

Final native Blockbench renders use mid-grey ground `#777777`, dark sky `#171E29`,
full-bright effect materials and disabled translucent depth writing. The
bystander camera is `[0,25.6,96]` u, looking at `[0,31,0]`, with 48° field of view.
The side camera is `[96,25.6,0]`. The underside camera is `[0,-8,0]`, looking at
`[0,64,0]`, with 80° field of view and the floor hidden. With caps absent and
front-face culling, that inside-the-beam view sees motes rather than dark discs.
The stage and exactly 32 u / two-block stand-in figure are render-only.

- [Contact sheet](knight_vanguard_flash_render_contact_sheet.png): frames 1–16;
  frames 10–13 label the full-size 75%, 50%, 25%, 0% alpha steps.
- [Bystander GIF](knight_vanguard_flash_render_bystander.gif): 16 frames at
  50 ms each, exactly 20 fps.
- [Frame 7](knight_vanguard_flash_render_frame7.png),
  [90° view](knight_vanguard_flash_render_frame7_side90.png),
  [below](knight_vanguard_flash_render_frame7_below.png).
- [Figure inside the beam](knight_vanguard_flash_render_frame7_occupant.png) and
  [hidden endpoint](knight_vanguard_flash_render_end_hidden.png).

The sheet, main, side, underside and occupant captures were inspected. The
previous revision's alpha-aware ray check sampled 32 azimuths, seven elevations (−90°, −60°, −30°,
0°, 30°, 60°, 90°), and a 41 × 41 image grid: 376,544 rays per frame on frames
1–13. Maximum distinct painted front surfaces were two on frames 1–11 and one
on its former frames 12–13. This respects UV masks and disabled faces, excludes
ring/motes, and counts coincident octagon corner hits once. The new fade's
geometry and UVs are verified identical to frame 7's two-shell peak, and its
alpha masks only lose coverage. Thus it inherits that peak's two-layer
construction. This is preservation evidence, not a new exhaustive sight-line test.

Checks verified exact animation records and bone identities; every surviving
element in frames 1–7; all elements and groups in frames 14–16; all 122 retained
ring/mote/glint geometries; identical peak beam geometry and UVs on frames 7–13;
disabled caps; the element ceiling; unchanged original textures; exact fade RGB
and alpha math; embedded/editable PNG byte equality; generated PNG byte equality;
generated element counts; and sixteen GIF frames at 50 ms each. Whole-table generation
reports 16 flipbooks / 121 frames / 456 files.

`build.ps1` and `check_pack_manifest.py` pass for `LegendCraft-Pack-0.2.4.zip`:
345 item models, 12 sounds and four sound indexes. Plugin-contributed assets
are unchecked because no plugin source pack was supplied. Precommit drift
reports the expected 28 changed generated paths. The required
postcommit result is quoted in
`C:\Users\omarz\.claude\comms\knight-vanguard-flash-r3-report.md`.

Minecraft translucent sorting, full-bright display and simultaneous composition
with the Knight, `knight_vanguard_burst` and banner remain in-game checks. No
deployment was performed.

## History and brief precedence

`2167665` introduced the original shafts and ribbons. The following revision
replaced them with broad painted beam shells. This revision deletes all 24 rays,
holds the frame-7 peak geometry through the beam's end, and replaces the
shrinking tail with four texture-alpha steps. The ring, motes, final glint,
clip and shrink contract remain.

The invoked [SKILL.md](C:/Users/omarz/.codex/skills/legendcraft-blockbench/SKILL.md)
says to write "Blockbench pass owed after the owner's ruling" and "END THE TURN",
and forbids "the commit and the handoff" before a later ruling.
[PROP-PREVIEW.md](C:/Users/omarz/.codex/skills/legendcraft-blockbench/PROP-PREVIEW.md)
says "Then the turn ends: the ruling is the next message". These explicit skill
requirements yield to this brief's instruction to keep building and finish in
one session. The skill's "commit and push authoring work there" and README
index guidance also yield to the named worktree, one local commit, no push and
named-file scope. The preview, final renders and commit proceed without a pause.
