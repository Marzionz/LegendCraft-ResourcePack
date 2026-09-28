# knight_ghost_shield — Bulwark absorbed-hit ghost heater

A heater of white light glowing blue at its edge appears on the incoming hit's bearing, expands, and fades over
six ticks (0.3 s). This is an item-model flipbook source, not a BetterModel deployment.
The silhouette reuses the shipped `knight_bulwark_shields` shield_0 front texture's
opaque outline, resampled with nearest neighbour; the emblem and trim are removed.

## Assets

| File | Purpose |
| --- | --- |
| `knight_ghost_shield.bbmodel` | Blockbench-authored rig with embedded textures |
| `knight_ghost_shield_1.png` through `_6.png` | Six editable 64×64 RGBA textures |
| `knight_ghost_shield_sheet.png` | Six-frame Blockbench contact sheet |
| `knight_ghost_shield_preview.gif` | Six frames at 20 fps, 50 ms each |

## Geometry and colour

Base size: **12.8×16.8 u = 0.8×1.05 blocks**, centred on the origin. Each frame
contains one flat cube, 0.5 u deep before its baked expansion. Front faces **+Z**;
the opposite face also draws. Only the north and south faces are textured, with
outward-facing materials, so a view does not blend two copies of the same fill.
There is no rim geometry, emblem, gold or baked lighting.

Fill: white light `#F5FCFF` at the core, glowing `#80C7FF` toward the edge over the
outermost eight pixels, with a one-pixel `#DBF0FF` boundary. The edge band carries up
to 15% more alpha than the core, so the glow reads brighter than the fill. Transparent pixels stay empty;
the outline has no antialiasing. Full brightness is the plugin's display setting.

The 64×64 atlas contains a 52×64 silhouette, mapped using UV `[6,0,58,64]`.
The brief's exact 4 px/u and 16.8 u height cannot both fit 64 pixels. The explicit
atlas and geometry sizes take priority: base density is 4.0625 px/u horizontally
and 3.8095 px/u vertically, decreasing as the baked geometry expands. This choice
is recorded as OPEN in the orchestrator inbox.

## Rig and timing

`root > fx > frame_1 ... frame_6`, all pivots at the origin. Geometry contains the
expansion; the clip only selects frames using uniform step scale 1 or 0.001.
Every frame bone has a key on every tick, including tick 6. No position or rotation
keys, native bones, tint, or display-transform animation are required.

| Frame | Tick interval | Time (s) | Baked scale | Core alpha | Core / edge alpha byte | Width × height (u) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0–1 | 0.00–0.05 | 0.90 | 86% | 220 / 255 | 11.520 × 15.120 |
| 2 | 1–2 | 0.05–0.10 | 1.00 | 82% | 210 / 255 | 12.800 × 16.800 |
| 3 | 2–3 | 0.10–0.15 | 1.08 | 72% | 184 / 211 | 13.824 × 18.144 |
| 4 | 3–4 | 0.15–0.20 | 1.15 | 59% | 150 / 172 | 14.720 × 19.320 |
| 5 | 4–5 | 0.20–0.25 | 1.22 | 39% | 100 / 115 | 15.616 × 20.496 |
| 6 | 5–6 | 0.25–0.30 | 1.26 | 18% | 47 / 54 | 16.128 × 21.168 |

`flare`: 0.30 s, hold its final all-hidden pose. Frame N is the only shown bone
from tick N−1 to N. At tick 6 every bone is 0.001: **ENDS HIDDEN**.
`hidden`: 0.05 s loop, every frame held at 0.001.

## Hook and row

One ItemDisplay per stance. On every absorbed hit, place it about 1.15 blocks
out from the Knight's chest along the attacker's bearing, yaw +Z toward the
attacker, restart at frame 1, and replace the item model once per tick. Frame 6
is the last drawn frame; hide the display at tick 6. The plugin owns placement,
yaw, full brightness, and the display transform. Shrink compensation is **1**.

| frames | rig | clip | shrink | native | tint |
| --- | --- | --- | --- | --- | --- |
| `knight_ghost_shield` | `knight_ghost_shield` | `flare` | 1 | | |

Item-model keys: `legendcraft:classes/knight_ghost_shield_1` through `_6`.
`tools/gen-flipbook-frames.py` generates the item definitions, models, and textures.
The largest frame fits the item box at shrink 1: x −0.064 to 16.064,
y −2.584 to 18.584, z 7.685 to 8.315, inside the allowed [−16,32] range.

## Verification

Frame 1 was authored, generated, and pack-built before adding frames 2–6. The
PROP-PREVIEW page generated from the real rig visibly blended the mannequin
through the 55% fill. Blockbench's final captures also show partial alpha and
the all-hidden tick-6 pose. **Partial alpha is retained; no cutout dither was used.**

This proves preview blending, not Minecraft ItemDisplay render-path selection.
The preview uses Three.js transparency explicitly. A target-client check remains
OPEN in the orchestrator inbox: verify alpha blending, full brightness, sorting,
and placement/restart feel. If the client renders the fill solid, use the brief's
ordered-dither fallback without changing the plugin contract.

The committed sheet and GIF are Blockbench captures from a bystander's eye:
1.6 blocks high, 4 blocks along +Z, looking at a shield centred 1.2 blocks high.
In origin-relative model units the camera is `[0,6.4,64]`, target `[0,0,0]`,
perspective FOV 38°. A neutral mannequin behind the plane supplies scale and
transparency evidence; it is render staging only and is absent from the rig.
The six GIF frames last 50 ms each; the clip's hidden endpoint was checked separately.

Blockbench authored and exported the rig. A temporary export adapter serialised
its live bones into the nested 4.10 layout consumed by the existing generator;
no geometry or animation was generated by writing `.bbmodel` JSON outside Blockbench.

## History

2026-09-28: Owner brief defines the silhouette, palette, six-tick cadence, frame
scales, and final delivery. Built and rendered directly under that authorization.
