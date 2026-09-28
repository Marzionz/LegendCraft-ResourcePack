# Knight Vanguard landing flash

A translucent spotlight flashes at the Knight's landing point, alongside
`knight_vanguard_burst` on the same tick. The Knight remains visible inside it.
The light rises, holds briefly, separates into three curved ribbons, then leaves
faint haze, rising gold motes and a last ground glint. This asset contains no fire,
rocks or banner; those belong to the accompanying landing effects.

The owner-supplied [concept](knight_vanguard_flash_concept.png) is the 1536 × 1024,
four-by-two timing and silhouette reference. It is committed unchanged and is not
used as a texture. The block-shaped construction follows the brief's Scorch and
Ember Shell direction, with deliberately translucent light instead of their solid
explosion masses.

## Geometry and game size

Authored units are 16 per block. The peak core reaches 63.965 u, approximately
4 blocks. The four-shaft beam spans about 17.51 × 18.36 u in plan (1.09 × 1.15
blocks), close to the requested 1.2-block base. Its white core is 2.4 u across;
the surrounding pale-blue, blue and azure shafts are 3.8 u across. Surrounding
shafts are offset around the axis and lean by 0.3 degrees in alternating directions.
Each has a broad lower segment and a narrower upper segment, with unequal heights
and tick-to-tick length flicker. Internal horizontal caps are omitted to avoid
stacking translucent surfaces. The lowest bottom and highest top caps remain.

The ground disc has a 20 u / 1.25-block outer radius. Its single upward face carries
a pixel-stepped bright ring band and a very faint interior. Its height is
`0.25 + 0.035 × (frame - 1)` u. Frames 10–13 use the faint ring texture; frames
14–16 retain only the shrinking centre glint. Only one face is textured on each
flat plane. Gold motes are 0.85 or 1.35 u cubes and rise between frames.

The ribbons each use seven short cuboids bent into a gentle S. Their interior
caps are omitted; widths narrow upward. The haze uses two broad cuboids at the
lowest alpha level. There are 254 elements across the frame stack and at most
30 in any visible frame.

## Textures and transparency

All nine editable PNGs are 16 × 16 and are also embedded in the `.bbmodel`.
Each shaft has a brighter centre stripe, stepped colour bands, softer alpha edges
and a few deliberately placed interrupted highlights. The motes have a gold face
and brass edge shading. No concept pixels were sampled into the textures.

| Texture suffix | Alpha bytes | Purpose |
| --- | --- | --- |
| `_outer.png` | 31 | Azure shaft and haze, 12.16% |
| `_middle.png` | 31, 56 | Blue shaft and first ribbons, up to 21.96% |
| `_inner.png` | 31, 56, 89 | Pale-blue inner shaft, up to 34.90% |
| `_core.png` | 31, 56, 115 | White core, at most 45.10% |
| `_ring.png` | 0, 31, 56, 255 | Clear background, faint disc, bright thin band |
| `_ring_fade.png` | 0, 31 | Faint ring and disc |
| `_ray.png` | 89, 255 | Early contact spokes only |
| `_mote.png` | 255 | Gold and brass cubes |
| `_glint.png` | 0, 89 | Translucent final centre glint |

Every filename starts with `knight_vanguard_flash`. Nonzero-alpha texture pixels
use only the specified palette: white `#FFFFFF`, ice `#E8F2FF`, pale blue `#A9CFFF`,
sky `#6FA8FF`, azure `#1F5FB0`, deep azure `#123C75`, gold `#FFD86B` and brass
`#C49A3A`. Silver is permitted by the brief but is not needed in the effect textures.
Only the early spokes, ring band and motes use opaque pixels. Partial alpha is
intentional and must not be binarized.

## Rig and timing

`root → fx → frame_1 … frame_16`. The root is unyawed, with rotation `[0,0,0]`,
as required for props by the toolkit's `SIGNS.md`. There are no animated position
or rotation channels. All changing animation segments are one tick long. Scale
keys exist at every tick from 0 through 16, using `step`, with `1` shown and
`0.001` hidden. `flash` plays once for 0.8 seconds; every frame is hidden at tick
16. The separate `hidden` animation loops with every frame hidden.

| Frame | Tick interval | Milliseconds | Shape | Elements |
| --- | --- | --- | --- | --- |
| 1 | 0–1 | 0–50 | Twelve low spokes, small core, ring, six motes | 22 |
| 2 | 1–2 | 50–100 | Shorter spokes, core rises, six motes | 22 |
| 3 | 2–3 | 100–150 | Four shafts rise to about 1.46 blocks | 17 |
| 4 | 3–4 | 150–200 | Column reaches about 2.15 blocks | 17 |
| 5 | 4–5 | 200–250 | Full pillar establishes, eight rising motes | 17 |
| 6 | 5–6 | 250–300 | Peak-length flicker | 17 |
| 7 | 6–7 | 300–350 | Tallest core, approximately 4 blocks | 17 |
| 8 | 7–8 | 350–400 | Shafts flicker independently | 17 |
| 9 | 8–9 | 400–450 | Last full-pillar frame | 17 |
| 10 | 9–10 | 450–500 | Three seven-segment ribbons, faint ring | 30 |
| 11 | 10–11 | 500–550 | Narrower, shorter 12% ribbons | 30 |
| 12 | 11–12 | 550–600 | Two 12% haze shafts, eight motes | 11 |
| 13 | 12–13 | 600–650 | Lower haze, higher motes | 11 |
| 14 | 13–14 | 650–700 | Three motes and centre glint | 4 |
| 15 | 14–15 | 700–750 | Two motes and smaller glint | 3 |
| 16 | 15–16 | 750–800 | One mote and last glint | 2 |
| End | 16 onward | 800 onward | All frame bones hidden | 0 visible |

## Item-model contract

`FLIPBOOKS.md` declares `knight_vanguard_flash | knight_vanguard_flash | flash | 4`.
The generated items are `legendcraft:classes/knight_vanguard_flash_1` through
`legendcraft:classes/knight_vanguard_flash_16`. Play each for exactly one tick at
the ground-level landing origin. The only display scale is the row's shrink, 4,
which reverses the generator's division by 4; there is no additional artistic
scale or vertical offset. Draw at full brightness. Remove or hide the display
after frame 16. The rig is an authoring source, not a BetterModel deployment.

Shrink 4 is sufficient. All authored geometry fits within x/z ±20 u and y below
64 u, well inside the brief's bounds. The generator writes 16 item definitions,
16 geometry models and 68 texture PNGs for this asset. The 68 PNGs are byte-for-byte
copies of the embedded textures, preserving all partial alpha.

## Verification and renders

Geometry was created and refined in the live Blockbench project through the
MCP driver at `http://localhost:3000/bb-mcp`, using native groups, cubes, textures
and animation tools. A compatibility export folds Blockbench 5's separate group
records into the 4.10 nested outliner expected by the existing generator and
preview toolkit; it does not generate or change geometry. No production tool or
plugin code changed.

The `PROP-PREVIEW.md` loop was run against the exported rig and then followed by
the final Blockbench render pass. The interactive
[preview](knight_vanguard_flash_render_preview.html) includes the actual clip,
timeline and a two-block mannequin. It loads three.js and fonts from the toolkit's
existing CDN URLs, so it needs network access. Cuboid faces use front-face culling;
the single-face disc remains double-sided in this inspection page.

The final Blockbench captures use a mid-grey ground, dark sky, full-bright effect
materials and disabled translucent depth writing. The bystander camera is
`[0,25.6,96]` u: 1.6 blocks high and 6 blocks out, aimed at `[0,31,0]`, with a 48°
field of view. The side camera is `[96,25.6,0]`. The underside camera is
`[0,-8,0]`, aimed straight up at `[0,64,0]`, with an 80° field of view; the floor
is hidden for that below-ground inspection so it cannot occlude the effect.
The mannequin and render stage are preview-only and are absent from the asset.

- [Contact sheet](knight_vanguard_flash_render_contact_sheet.png): all 16 frames.
- [GIF](knight_vanguard_flash_render_bystander.gif): exactly 16 frames at 50 ms each, 20 fps.
- [Frame 7](knight_vanguard_flash_render_frame7.png),
  [90° side](knight_vanguard_flash_render_frame7_side90.png),
  [straight below](knight_vanguard_flash_render_frame7_below.png).
- [Occupant visibility](knight_vanguard_flash_render_frame7_occupant.png) and
  [hidden endpoint](knight_vanguard_flash_render_end_hidden.png).

Overlap was measured on the exported cuboids, respecting their rotations and
disabled faces. For each frame 3–13, 85 × 85 perspective rays were sampled at
24 azimuths and seven elevations (−90°, −60°, −30°, 0°, 30°, 60°, 90°), from a
96 u radius around the beam. Maximum textured front-surface intersections were
3 for frames 3–11 and 2 for frames 12–13. This is sampled evidence, not a proof
over every possible sight line. The count excludes the ground ring and opaque
motes. Removing internal taper/ribbon caps and reducing the pillar to four
shafts eliminated the five-surface overlaps of the initial draft. The sheet,
side and underside renders were inspected; the mannequin remains clearly legible.

Additional checks confirmed exact one-tick visibility, the hidden endpoint,
the hidden loop, ≤48 elements per frame, 16 × 16 palette-only textures, matching
embedded/editable PNGs, preserved generated PNG bytes and model element counts.
The generator accepts partial alpha. Generation reports 16 flipbooks / 121 frames /
466 files for the whole table. Pack build and manifest checks pass; the manifest
carries 345 item models, 12 sounds and 4 sound indexes. Plugin-contributed assets
are unchecked because no plugin source pack was supplied. The precommit drift
check reports only this asset's 100 new uncommitted outputs; the postcommit result
is recorded in the external session report.

Actual Minecraft sorting, the full-bright display and simultaneous composition
with `knight_vanguard_burst`, banner and Knight remain in-game checks. No deployment
was performed.

## Brief precedence

The invoked skill's Review surface section says to write "Blockbench pass owed
after the owner's ruling" and "END THE TURN", and prohibits "the commit and the
handoff" before a later ruling. `PROP-PREVIEW.md` similarly says "Then the turn
ends: the ruling is the next message". These are explicit skill requirements;
the owner's brief explicitly overrides them and requires completion in this
session. The preview, final renders and local commit therefore proceed without
that pause. The skill's "commit and push authoring work there" instruction and
README index requirement also yield to this brief's named worktree, one local
commit, no push and named-file scope. No README or other lane's assets were edited.
