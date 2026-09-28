# Flame Surge — independently scaled ground rune ring

The ground rune ring extracted from `pyro_surge_burst.bbmodel` as drawn in pack commit `80f5f73`. It plays beside the [pillar](pyro_surge_burst.md) on a separate item display so blast reach and pillar height scale independently. This is a FRAME STACK authoring rig for generated item models, not a BetterModel deployment.

## Rows and heat bands

| Frames stem | Clip | Stacks | Shrink | Frames |
| --- | --- | --- | ---: | ---: |
| `pyro_surge_ring_low` | `ring_low` | 0–2 | 2 | 12 |
| `pyro_surge_ring_mid` | `ring_mid` | 3–4 | 2 | 12 |
| `pyro_surge_ring_high` | `ring_high` | 5 | 2 | 12 |

**Three rows are required.** Frames 1–9 use distinct low, mid and high heat textures; frames 10–12 share the dying texture. One clip would lose the heat colors. Embedded textures and existing editable `pyro_surge_burst_ring_{low,mid,high,dying}.png` files are unchanged.

## Registration and runtime scale

Each frame is exactly one horizontal 64×64 u plane, x/z −32 to +32, centered on the origin, at `y = 0.25 + 0.035 × (frame − 1)` model units. Only its up face is textured; authoring is double-sided. The original 64×64 textures have center (31.5,31.5), one pixel per model unit, and outer edge **28 u = 1.75 blocks**. Maximum occupied pixel-center radius is 27.973201 pixels in all four textures, within half a pixel of the target. Ground glyphs include diamonds, boxed squares, crosses and hooked strokes. The ring keeps its radius while dimming.

**Shrink 2 is the smallest supported fit.** Shrink 1 bakes the plane to x/z [−24,40], outside item-model bounds [−16,32]. Shrink 2 bakes it to [−8,24]. Geometry and per-frame heights are preserved; transparent borders are not cropped.

Runtime ring display scale: `true blast reach / 1.75 × shrink`.

At 4-block blast reach with shrink 2: **`4 / 1.75 × 2 = 32/7 ≈ 4.571428571`**. This restores the authored registration and scales the visible outer edge to the true reach. The pillar display uses **4**, its shrink restoration only. Both displays share the spawn origin and frame clock. Pair ring low/mid/high with pillar low/mid/full; `pillar_high` is the full-band clip. Original per-frame y offsets receive the ring display scale.

## Bones, timing and budget

Unyawed identity `root` → `fx` → `low_f1`…`low_f12`, `mid_f1`…`mid_f12`, `high_f1`…`high_f12`. Each leaf owns its original ground plane. There are 36 authoring elements and exactly one visible element per frame.

`ring_low`, `ring_mid`, `ring_high`: hold, 0.6 seconds, **ENDS HIDDEN**. Every frame bone retains the source step scale keys at all ticks 0–12. Frame N is shown at scale 1 from tick N−1 to N; other frames are at 0.001. Every changing key segment lasts one tick. All frame bones hide at tick 12. `hidden` retains its 0.05-second loop hiding all frames. No position or rotation animation channels.

| Frames | Ticks | Read |
| --- | --- | --- |
| 1–9 | 0–8 | Selected band's lit ring, full radius |
| 10–12 | 9–11 | Shared dying texture, same radius |
| End | 12 | All hidden; runtime removes both displays |

Each row generates 12 item definitions, 12 geometry models and 12 unchanged texture copies: 36 files per row, 108 total. Ring and pillar together preserve every original per-frame element budget.

## Verification and renders

Native Blockbench MCP operations removed non-ring cubes from a copy of the source and renamed the clips. The raw native codec exported the rig; group metadata was folded into legacy outliner objects for the existing generator. No external script constructed geometry. All 36 retained elements compare exactly with `80f5f73`; embedded texture bytes, coordinates, UVs, animation keys and heights match exactly. Ring and pillar form an exact disjoint partition of the source's 1,020 elements.

Verified twelve one-tick spans per row, one shown frame per tick, hidden terminal/parked states, original registration, failure at shrink 1, success at shrink 2, and emitted bytes against generator output. See [pillar verification](pyro_surge_burst.md#verification-and-renders) for pack build and manifest results; post-commit drift is quoted in the handoff report.

`pyro_surge_ring_render_{low,mid,high}_contact.png`: one inspected twelve-frame contact sheet per ring row. Matching `.gif` files have twelve 50 ms frames; `_peak.png` shows frame 8. Native camera (0,85,72) u, target (0,0,0), perspective FOV 50, at authored scale. Terminal `_ring_high_hidden.png` and parked `_hidden_hidden.png` renders are empty. `pyro_surge_ring_render_preview.html` comes from the delivered rig with per-texture UV resolution; browser playback was not verified. Runtime reach scaling still needs in-game hook verification.

## History

2026-09-28: extracted unchanged ground planes from `80f5f73` into three clips/rows with shrink 2. The owner's ruling authorizes this split through commit. Skill gate and repository-workflow overrides are recorded in [the pillar contract](pyro_surge_burst.md#history-and-skill-overrides). No plugin changes, deploy, push or PR.
