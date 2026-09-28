# Flame Surge — three-dimensional rune-flame eruption

Flame Surge's stack read is a tapering, twisted cube-flame pillar over a registered ground rune ring. `burst_low` (0–2 stacks) is dull red/deep orange with one diamond and smoke; `burst_mid` (3–4 stacks) is orange/yellow with three diamonds; `burst_high` (5 stacks) is yellow/white-hot with five diamonds and cyan flecks, without smoke. Each has 12 frames at one tick each, 0.6 seconds, ending hidden.

This is a FRAME STACK authoring rig. Runtime uses the three existing `FLIPBOOKS.md` rows, each at **shrink 4**, as item-model flipbooks. It is not a BetterModel deployment. No plugin changes are included. `surge_volcano` is unchanged.

## Shape and materials

The approved Flame Surge concept supplies the silhouette and heat bands. Scorch's accepted explosion supplies the lobe recipe and its six hand-shaded 16×16 material tiles: each central flame tier pairs a cube with a 45-degree-yawed companion at 84% width/depth and 91% height. Tiers taper upward and advance their yaw per frame. Short off-axis tongues carry smaller raised tips. Five basalt chunks kick up at the foot; embers remain during collapse. Small cutout diamond glyph cubes rise with the core. Low alone carries three smoke cubes.

Peak geometry reaches 25.84 / 41.84 / 57.84 model units (about 1.62 / 2.62 / 3.62 blocks), including the tip overlap. These are the requested approximate 1.5 / 2.5 / 3.5-block bands. Surface UVs use the full 16×16 side tile, brighter upper ten rows on tops, darker lower eight rows on undersides. The new basalt tile has deliberately clustered chipped plates; the rune tiles have stepped hot diamonds with darker borders. Editable PNGs beside this file match all embedded textures.

All visible pixels use only `#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`, with `#9FE8FF` exclusively on high-band fleck cubes. Alpha is exclusively 0 or 255. No emissive-pair textures or painted side billboards.

## Ring registration and runtime scale

One horizontal 64×64 u plane per frame, centred on the origin, at y = 0.25 + 0.035(frame−1) u; only its up face is textured, double-sided in authoring. The 64×64 ring textures follow Scorch's one pixel per model unit registration: centre (31.5,31.5), outer edge 28 pixels = 28 u = **1.75 blocks**. Maximum occupied pixel-centre radius is 27.973201 pixels in all four heat states, within half a pixel of the target. This registration is identical in every band and every frame. Ground glyphs include diamonds, boxed squares, crosses and hooked strokes. The ring remains at full radius as it dims.

The ring reach multiplier is `trueRadius / 1.75`; at 4 blocks it is `16/7`. Including shrink restoration, its item-display scale is `4 × 16/7 = 64/7` (9.142857).

**OPEN hook dependency:** one existing item display draws both ring and pillar, so its transform cannot scale only the ring. Applying the reach multiplier to the pillar produces about 3.69 / 5.98 / 8.26 blocks of height. That is not recommended: keep the pillar near its authored height and split the ring into an independently driven display in a hook follow-up, with separate generated art rows requested at that time. The OPEN block “Flame Surge burst ring reach versus pillar scale (2026-09-28)” is in the orchestrator inbox. The combined existing rows are retained; no unauthorized plugin or row-contract expansion was made.

## Bones and clips

Unyawed identity `root` → `fx` → `low_f1`…`low_f12`, `mid_f1`…`mid_f12`, `high_f1`…`high_f12`. Existing frame names 1–6 remain; 7–12 extend each band. Each frame owns all its cubes and ground plane.

`burst_low`, `burst_mid`, `burst_high`: hold, 0.6 s. Every frame bone has a step scale key on every tick 0–12. Exactly frame N of the chosen band is at 1 from tick N−1 to N; all other frame bones are at 0.001. All bones are hidden at tick 12. Every changing key segment lasts exactly one tick. `hidden` retains its 0.05-second loop and hides every frame. No position or rotation keys; static cube turns use the unyawed-prop convention in the skill's `SIGNS.md`.

| Frames | Ticks | Read |
| --- | --- | --- |
| 1–2 | 0–1 | Ground ring lit, basalt kicking up, low sparks |
| 3–6 | 2–5 | Pillar erupts upward; glyphs rise through its core |
| 7–9 | 6–8 | Full height; tongue/tip yaw and roll change each tick |
| 10–12 | 9–11 | Cooling collapse to embers; low smoke; dim ring |
| End | 12 | All hidden |

| Band | Element counts, frames 1–12 | Maximum |
| --- | --- | ---: |
| Low | 9, 9, 27, 27, 27, 27, 27, 27, 27, 27, 26, 12 | 27 |
| Mid | 9, 9, 34, 34, 34, 34, 34, 34, 34, 34, 31, 9 | 34 |
| High | 9, 9, 44, 44, 44, 44, 44, 44, 44, 44, 39, 9 | 44 |

1,020 total authoring elements, with at most 44 drawn at once. The generator emits 36 frame models across the three rows: low 97 files, mid 79, high 88 (264 total item definitions, geometry and per-frame texture copies).

## Verification and renders

Geometry, bones and animation keys were created with native Blockbench Cube/Group/Animation APIs through `bb.py` at `http://localhost:3000/bb-mcp`, in Undo transactions. The native project codec exported the result; group metadata was folded into legacy outliner objects for the generator. No geometry was constructed as external JSON. Reloaded Blockbench world bounds agree with the independent rotated-corner bounds; all shown corners are above ground (minimum 0.03 u). All frames fit shrink 4; `FLIPBOOKS.md` needed no change.

The `PROP-PREVIEW.md` loop produced a before page in `%TEMP%/bb-pyro-surge/burst_before.html` and the delivered `pyro_surge_burst_render_preview.html` from the actual exported rig. The scratch renderer handles each texture's UV resolution. The browser security policy refused local-file navigation, so browser playback was not verified; native Blockbench supplied the visual review.

`pyro_surge_burst_render_{low,mid,high}.gif`: exactly twelve 50 ms frames, 20 fps. Matching `_contact.png` and `_peak.png` files show each band. Camera (0,25.6,96) u, target (0,22,0), perspective FOV 50: bystander eye 1.6 blocks high and six blocks out, at authored scale. The contact sheets were visually inspected. The `_burst_high_hidden.png` and `_hidden_hidden.png` renders show the terminal and parked states.

Verified palette/binary alpha; identical ring radius in every ground state; 12 spans per clip; exactly one frame active per tick; one-tick changes and hidden ends; per-frame element budgets; rotated bounds; all 264 generated outputs byte-for-byte; GIF count and duration. `python tools/gen-flipbook-frames.py`: `OK: 16 flipbook(s), 147 frame(s), 721 file(s) written`. The required pre-commit drift check reports the expected uncommitted generated changes. `build.ps1` succeeds for `dist/LegendCraft-Pack-0.2.4.zip`; `check_pack_manifest.py --source-tree src` passes with 371 item models, 12 sounds, three sounds.json files. The post-commit drift result is quoted in the handoff report.

In-game checks still owed: 12 one-tick swaps and removal at tick 12, reach scaling after the OPEN hook decision, cutout/lighting against terrain and target bodies, and ground placement on slopes.

## History and skill overrides

2026-09-28: replaced the six-frame crossed side paintings with 12-frame three-dimensional rune pillars at three strengths, preserved the row names/shrink and regenerated their item frames. The old `tools/build_pyro_surge_frames.py` and `tools/build_pyro_surge_rigs.py` are STALE for this asset; the committed model is authoritative.

The brief explicitly overrides `legendcraft-blockbench/SKILL.md`'s line “the commit and the handoff are all forbidden” before a later owner ruling, and `PROP-PREVIEW.md`'s “Then the turn ends: the ruling is the next message”. Those are explicit skill gates, overridden here by the instruction to finish renders, checks and commits without pausing. It also overrides the skill's separate models-repository index/push workflow: only this pack worktree's named asset paths are committed, with no push or PR.
