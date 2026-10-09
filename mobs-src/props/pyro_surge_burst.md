# Flame Surge — independently scaled flame pillar

The tapering, twisted cube-flame pillar, basalt chunks, rising diamond runes, embers and smoke are preserved from pack commit `80f5f73`. The ground planes now live in [pyro_surge_ring.bbmodel](pyro_surge_ring.bbmodel); see [the ring contract](pyro_surge_ring.md). Two synchronized item displays let the ring reach the blast radius while the pillar keeps its authored height.

This is a FRAME STACK authoring rig for item-model flipbooks, not a BetterModel deployment. No plugin code or `surge_volcano` changes are included.

## Rows and runtime scale

| Frames stem | Clip | Stacks | Shrink | Frames |
| --- | --- | --- | ---: | ---: |
| `pyro_surge_pillar_low` | `pillar_low` | 0–2 | 4 | 12 |
| `pyro_surge_pillar_mid` | `pillar_mid` | 3–4 | 4 | 12 |
| `pyro_surge_pillar_full` | `pillar_high` | 5 | 4 | 12 |

The item-model stem calls the five-stack band `full`; its authoring clip calls it `high`. The pillar display scale is **4**, restoring shrink only. Do not apply the ring reach multiplier to it. Pair pillar low/mid/full with ring low/mid/high at the same origin and tick. The retired `pyro_surge_burst_low|mid|high` rows and all 264 generated files are removed.

Peak geometry remains 25.84 / 41.84 / 57.84 model units, about 1.62 / 2.62 / 3.62 blocks including tip overlap. The ring can cover the true 4-block blast reach without stretching the high pillar to about 8.26 blocks.

## Shape and materials

The approved Flame Surge concept supplies the silhouette and heat bands. Scorch's accepted explosion supplies the lobe recipe and six hand-shaded 16×16 material tiles: each central flame tier pairs a cube with a 45-degree-yawed companion at 84% width/depth and 91% height. Tiers taper upward and advance their yaw per frame. Off-axis tongues carry raised tips. Five basalt chunks kick up at the foot; embers remain during collapse. Cutout diamond glyph cubes rise with the core. Low alone carries three smoke cubes.

Low is dull red/deep orange with one diamond and smoke; mid is orange/yellow with three diamonds; high is yellow/white-hot with five diamonds and cyan flecks, without smoke. Surface UVs use the full 16×16 side tile, brighter upper ten rows on tops, darker lower eight rows on undersides. The basalt tile has clustered chipped plates; rune tiles have stepped hot diamonds with darker borders. Existing editable PNGs remain unchanged and match embedded textures.

Visible pixels use only `#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`, with `#9FE8FF` exclusively on high-band flecks. Alpha is 0 or 255. No emissive-pair textures or painted side billboards. Both rigs retain the original embedded texture collection; the generator emits only textures used by each frame.

## Bones, timing and budgets

Unyawed identity `root` → `fx` → `low_f1`…`low_f12`, `mid_f1`…`mid_f12`, `high_f1`…`high_f12`. Each frame owns its original cubes, with its single ground plane removed.

`pillar_low`, `pillar_mid`, `pillar_high`: hold, 0.6 seconds, **ENDS HIDDEN**. Every frame bone retains step scale keys at every tick 0–12. Exactly frame N of the selected band is at scale 1 from tick N−1 to N; all other frame bones are at 0.001. All frame bones hide at tick 12. Every changing key segment is exactly one tick. `hidden` retains its 0.05-second loop and hides every frame. No position or rotation keys changed; static cube turns retain the original unyawed-prop convention.

| Frames | Ticks | Read |
| --- | --- | --- |
| 1–2 | 0–1 | Basalt kicking up, low sparks |
| 3–6 | 2–5 | Pillar erupts; glyphs rise through its core |
| 7–9 | 6–8 | Full height; tongue/tip yaw and roll change each tick |
| 10–12 | 9–11 | Cooling collapse to embers; low smoke |
| End | 12 | All hidden; runtime removes both displays |

| Band | Pillar elements, frames 1–12 | Maximum |
| --- | --- | ---: |
| Low | 8, 8, 26, 26, 26, 26, 26, 26, 26, 26, 25, 11 | 26 |
| Mid | 8, 8, 33, 33, 33, 33, 33, 33, 33, 33, 30, 8 | 33 |
| High | 8, 8, 43, 43, 43, 43, 43, 43, 43, 43, 38, 8 | 43 |

984 pillar elements plus 36 ring planes exactly partition the original 1,020 elements. Adding the one visible ring plane preserves the original combined maxima of 27 / 34 / 44. Pillar rows emit 85 / 67 / 76 files (228 total); ring rows emit 108 files. The split has 72 frame models and 336 generated files total.

## Verification and renders

The split used native Blockbench `Cube.remove()` operations through `bb.py` at `http://localhost:3000/bb-mcp`, inside Undo transactions. Clips were renamed in Blockbench. The native project codec's raw export preserves full floating-point precision; exported group metadata was folded into legacy outliner objects for the existing generator. No external JSON constructed or edited geometry.

Independent comparison against `80f5f73` confirms exact equality of every retained element, including coordinates, origins, rotations, faces and UVs. All embedded texture bytes and animation data are unchanged apart from clip names. The rigs have disjoint element UUID sets whose union is exactly the source. All six rows have twelve one-tick spans, one visible frame bone per tick, and hidden terminal/parked states. Generated bytes match generator output. Original geometric bounds and above-ground placement are preserved by exact comparison; shrink 4 passes generator bounds validation.

`pyro_surge_burst_render_{low,mid,high}.gif` and matching `_contact.png` / `_peak.png` files were regenerated because the ground ring is absent. Each GIF has twelve 50 ms frames. All contact sheets were visually inspected. Native camera (0,25.6,96) u, target (0,22,0), perspective FOV 50, at authored scale. Terminal and parked states were rendered again and are empty; existing `_burst_high_hidden.png` and `_hidden_hidden.png` artifacts remain because those states did not change. The former filename is retained as an artifact name; the clip is now `pillar_high`.

`pyro_surge_burst_render_preview.html` was regenerated from the delivered rig with per-texture UV resolution. Browser playback was not verified this session; native Blockbench supplied visual verification.

Required checks: generator `OK: 19 flipbook(s), 183 frame(s), 793 file(s) written`; pre-commit drift reports the expected 600 uncommitted changes (264 removals plus 336 additions); `build.ps1` passes for `dist/LegendCraft-Pack-0.2.4.zip`; manifest check with `--source-tree src` passes with 407 item models, 12 sounds and three sounds.json files. Post-commit drift and commit SHA are quoted in `C:/Users/omarz/.claude/comms/pyro-rig-flame-surge-split-report.md`.

The generator only removes stale frames for rows still in its table. Retired combined outputs were removed using its existing `stale_frames` matcher, restricted to the three retired stems, before regeneration; generator code is unchanged.

In-game checks owed to the hook session: synchronized swaps and removal at tick 12, independent ring reach scaling, cutout/lighting against terrain and targets, and placement on slopes.

## History and skill overrides

2026-09-28, `80f5f73`: replaced six-frame crossed paintings with the twelve-frame three-dimensional eruption. `tools/build_pyro_surge_frames.py` and `tools/build_pyro_surge_rigs.py` remain STALE for this asset; committed rigs are authoritative.

2026-09-28: split the registered ring into its own rig and three heat-band rows; retained the pillar except removal of ring planes and clip renames. The owner's ruling resolves the prior shared-display scaling dependency for these assets. The plugin hook must play two displays.

The brief overrides `C:/Users/omarz/.codex/skills/legendcraft-blockbench/SKILL.md`: “the commit and the handoff are all forbidden” before a later preview ruling; and `PROP-PREVIEW.md`: “Then the turn ends: the ruling is the next message”. These are explicit skill gates; this brief directs completion without pausing. It also overrides the separate models-repository index/push workflow: only named pack-worktree asset paths are committed, without push or PR. This worktree has no `mobs-src/README.md`; `FLIPBOOKS.md` indexes this deliverable.
