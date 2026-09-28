# Knight Vanguard landing flash

One soft, translucent spotlight surrounds the Knight at the landing origin,
alongside `knight_vanguard_burst` on the same tick. The Knight stands inside the
light and remains visible. The opening ground starburst becomes a rising beam,
which briefly holds, narrows and fades, then leaves low haze, rising gold motes
and a last ground glint. There are no separate shafts, rods, ribbons or beam caps.

The unchanged [concept](knight_vanguard_flash_concept.png) is the original
1536 × 1024 four-by-two reference, not a texture. The owner's revision of
`2167665` supersedes its separated-pillar silhouette with one spotlight.

## Geometry and game size

Authored units are 16 per block. At full size, the outer light shell is 25.6 u
across (1.6 blocks), and the inner shell is 21.504 u across. Each shell consists
of two equal broad boxes centred on the origin, one at yaw 0° and one at 45°.
Both shells share the same height: 62–64 u on frames 5–9, peaking at exactly
64 u / 4 blocks on frame 7. They stay straight as they rise. All beam cubes have
their top and bottom faces disabled. The white centre and streaks are texture
marks, with no separate core or streak geometry.

Each paired box layer forms one octagonal painted shell. Its side UV rectangle
is `[8 - 3/(sqrt(2)-1), 0, 8 + 3/(sqrt(2)-1), 16]`. Only bitmap columns 20–43
of 64 carry light, restricting each painted face to the central `sqrt(2)-1`
fraction of its width. The eight painted sections meet at octagon corners;
transparent margins avoid four overlapping surfaces. Front-face culling is
part of this construction. Rotated invisible bounds still fit within x/z ±20 u
and y ≤64 u, so shrink 4 remains sufficient.

Frames 10–11 narrow both shells together to 22 u then 18 u, with heights 56 u
then 46 u and falling alpha. Frames 12–13 use only the outer pair: widths 20 u
then 17 u and heights 20 u then 10 u. No ribbons replace the beam.

The original ring, spokes, motes and glint retain their geometry, UVs and texture
pixels, subject only to native export's five-decimal coordinate rounding
(≤0.000005 u). The ring radius remains 20 u / 1.25 blocks; its height remains
`0.25 + 0.035 × (frame - 1)` u. Frames 10–13 use the faint ring, and frames
14–16 retain the shrinking glint. Flat planes have one textured face. Gold
motes remain 0.85 or 1.35 u cubes and rise between frames.

There are 194 elements across the frame stack, at most 23 in a visible frame.

## Textures and transparency

All 17 editable PNGs are embedded unchanged in the `.bbmodel`. Twelve beam
textures are 64 × 64 with logical UV dimensions 16 × 16. The five retained
ring/spoke/mote/glint textures remain 16 × 16. Every filename starts with
`knight_vanguard_flash`. Partial alpha must not be binarized.

| Texture suffix | Alpha bytes | Purpose |
| --- | --- | --- |
| `_outer.png` | 0, 31 | Widest, faintest shell and haze; 12.16% maximum |
| `_inner.png`, `_inner_02.png` … `_inner_09.png` | 0, 31, 56, 89, 115 | Main gradient, painted centre and moving streaks |
| `_inner_10.png` | 0, 31, 56 | Narrowing beam, 21.96% maximum |
| `_inner_11.png` | 0, 31 | Narrower beam, 12.16% maximum |
| `_ring.png` | 0, 31, 56, 255 | Original faint disc and bright thin band |
| `_ring_fade.png` | 0, 31 | Original faint ring |
| `_ray.png` | 89, 255 | Original contact spokes, frames 1–2 |
| `_mote.png` | 255 | Original gold/brass cubes |
| `_glint.png` | 0, 89 | Original final centre glint |

Reading upward from the ground, main inner bitmap rows 48–63 use alpha 89
(34.90%), rows 28–47 use 56 (21.96%), and rows 4–27 use 31 (12.16%). Rows
4–15 become progressively sparse transparent pixels; rows 0–3 are fully clear.
Edge columns use at most 31. The painted white centre reaches 115 (45.10%) only
near the ground and follows the upward fade. Two short one-pixel-wide streaks
climb four bitmap rows per frame; their alpha never exceeds 89.

Column colours are white `#FFFFFF`, ice `#E8F2FF`, pale blue `#A9CFFF` and sky
`#6FA8FF`; sky is its darkest colour. The original broader effect palette still
permits azure `#1F5FB0`, deep azure `#123C75`, gold `#FFD86B` and brass `#C49A3A`.
Motes retain gold and brass. Only ring, spokes and motes use opaque pixels.
The retired standalone core and middle-shaft textures are removed.

## Rig and timing

`root → fx → frame_1 … frame_16`. Bone names, UUIDs, pivots and both animation
records are retained. Root rotation is `[0,0,0]`; there are no animated position
or rotation channels. `flash` plays once for 0.8 seconds. Scale keys at ticks
0–16 use `step`: 1 shown, 0.001 hidden. All frames are hidden at tick 16. The
separate `hidden` animation loops with all frames hidden.

| Frame | Tick interval | Milliseconds | Shape | Elements |
| --- | --- | --- | --- | --- |
| 1 | 0–1 | 0–50 | Twelve spokes, low broad flash, ring, six motes | 23 |
| 2 | 1–2 | 50–100 | Shorter spokes, broad flash rises, six motes | 23 |
| 3 | 2–3 | 100–150 | One beam rises to 24 u / 1.5 blocks | 13 |
| 4 | 3–4 | 150–200 | Beam reaches 40 u / 2.5 blocks | 13 |
| 5 | 4–5 | 200–250 | Full beam, 62 u; eight motes | 13 |
| 6 | 5–6 | 250–300 | Full beam, 63 u; rising streaks | 13 |
| 7 | 6–7 | 300–350 | Peak, 64 u / 4 blocks | 13 |
| 8 | 7–8 | 350–400 | Full beam, 63 u | 13 |
| 9 | 8–9 | 400–450 | Last full beam, 62 u | 13 |
| 10 | 9–10 | 450–500 | Width 22 u, height 56 u; alpha ≤56 | 13 |
| 11 | 10–11 | 500–550 | Width 18 u, height 46 u; alpha ≤31 | 13 |
| 12 | 11–12 | 550–600 | One 12% haze shell, 20 u high | 11 |
| 13 | 12–13 | 600–650 | Lower haze, 10 u; higher motes | 11 |
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
for this asset. PNGs preserve the embedded bytes and partial alpha. Obsolete
texture outputs from the old shafts are removed by regeneration.

## Verification and renders

Geometry was rebuilt in live Blockbench through MCP at
`http://localhost:3000/bb-mcp`, using native Cube, Group and Texture objects and
an undo transaction. Painting scripts produced PNGs only. Native export was
adapted from Blockbench 5's separate group records to the toolkit's 4.10 nested
outliner, omitting empty effect animators; this did not author geometry.
No plugin code or production generator changed.

The `PROP-PREVIEW.md` loop generated before and after pages from the actual rig.
The updated [interactive preview](knight_vanguard_flash_render_preview.html)
was opened and checked with a two-block mannequin, the actual clip, scrubber
and timeline. It requires network access for the toolkit's three.js/font CDN
URLs. Cuboids use front-face culling; the ring/glint planes remain double-sided
in the inspection page. Playback defaults to 1× speed.

Final native Blockbench renders use mid-grey ground `#777777`, dark sky,
full-bright effect materials and disabled translucent depth writing. The
bystander camera is `[0,25.6,96]` u, looking at `[0,31,0]`, with 48° field of view.
The side camera is `[96,25.6,0]`. The underside camera is `[0,-8,0]`, looking at
`[0,64,0]`, with 80° field of view and the floor hidden. With caps absent and
front-face culling, that inside-the-beam view sees motes rather than dark discs.
The stage and exactly 32 u / two-block stand-in figure are render-only.

- [Contact sheet](knight_vanguard_flash_render_contact_sheet.png): frames 1–16.
- [Bystander GIF](knight_vanguard_flash_render_bystander.gif): 16 frames at
  50 ms each, exactly 20 fps.
- [Frame 7](knight_vanguard_flash_render_frame7.png),
  [90° view](knight_vanguard_flash_render_frame7_side90.png),
  [below](knight_vanguard_flash_render_frame7_below.png).
- [Figure inside the beam](knight_vanguard_flash_render_frame7_occupant.png) and
  [hidden endpoint](knight_vanguard_flash_render_end_hidden.png).

The sheet, main, side, underside and occupant captures were inspected. An
alpha-aware ray check sampled 32 azimuths, seven elevations (−90°, −60°, −30°,
0°, 30°, 60°, 90°), and a 41 × 41 image grid: 376,544 rays per frame on frames
1–13. Maximum distinct painted front surfaces were two on frames 1–11 and one
on frames 12–13. This respects UV masks and disabled faces, excludes ring/motes,
and counts coincident octagon corner hits once. It is sampled evidence, not an
exhaustive proof over every sight line.

Checks also verified unchanged animations and bone identities, 146 retained
ring/spoke/mote/glint elements, the element ceiling, column palette and alpha
ceiling, transparent tops, embedded/editable PNG byte equality, generated PNG
byte equality and per-frame generated element counts. Whole-table generation
reports 16 flipbooks / 121 frames / 456 files.

`build.ps1` and `check_pack_manifest.py` pass for `LegendCraft-Pack-0.2.4.zip`:
345 item models, 12 sounds and four sound indexes. Plugin-contributed assets
are unchecked because no plugin source pack was supplied. Precommit drift
reports expected changes from the old committed generated frames. The required
postcommit result is quoted in
`C:\Users\omarz\.claude\comms\knight-vanguard-flash-r2-report.md`.

Minecraft translucent sorting, full-bright display and simultaneous composition
with the Knight, `knight_vanguard_burst` and banner remain in-game checks. No
deployment was performed.

## History and brief precedence

`2167665` introduced the original shafts and ribbons. This owner-requested
revision replaces their 108 elements with 48 broad beam/haze cubes, retaining
the ring, spokes, motes, clip and shrink.

The invoked [SKILL.md](C:/Users/omarz/.codex/skills/legendcraft-blockbench/SKILL.md)
says to write "Blockbench pass owed after the owner's ruling" and "END THE TURN",
and forbids "the commit and the handoff" before a later ruling.
[PROP-PREVIEW.md](C:/Users/omarz/.codex/skills/legendcraft-blockbench/PROP-PREVIEW.md)
says "Then the turn ends: the ruling is the next message". These explicit skill
requirements yield to this brief's instruction to keep building and finish in
one session. The skill's "commit and push authoring work there" and README
index guidance also yield to the named worktree, one local commit, no push and
named-file scope. The preview, final renders and commit proceed without a pause.
