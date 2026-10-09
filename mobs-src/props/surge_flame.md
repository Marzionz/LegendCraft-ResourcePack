# Flame Surge ranked flame

Source pack: `C:\Repositories\Animation training\samus2002_AWAKENED_PYROMANCER [v1.1]`; its licence permits modification.
Source model: `ModelEngine\blueprints\RPG_Class_Awakened_Pyromancer\Infernal Judgement\infernal_judgement_vfx.bbmodel` (SHA-256 `7bf42a96b5e2bb92b4e545f6dfe0b9039880ab083cf5c8cf5c99199aa6267a96`).
Source clip: `lava_obsidian_infernal_judgement`, 3.05 s, under `lava_obsidian_pieces_eruption_vfx`.
Retained: the ground-flame tongues (`allef_impactv1`, `allef_impactv2`), the rising streaks (`allef_impact_mini`), the paired flying fragments (`allef_mini_flame2`) and the flying rocks (`allef_stone`), with all their descendants. Excluded: the grounded spike ring `allef_stone_impact` (Conflagration's). No smoke is visible in this state.

`surge_flame_red`, `surge_flame_orange` and `surge_flame_white` are BetterModel rigs that erupt out of the throat of the `surge_volcano` pimple when Flame Surge lands. The rank follows the target's Burning stacks; the top tier, at 5 stacks, wears the white-hot rig taller, so Flame Surge never wears Cryomancer's blues. The volcano itself is the shipped rig, unchanged. Together they replace the painted `pyro_surge_burst` fire pillar on the plugin side. The painted ground rune ring, [`pyro_surge_ring`](pyro_surge_ring.md), plays under them in the flame's rank and stands for the Level 45 patch's life. The Level 45 patch lies on the [magma pool](pyro_surge_pool.md) under its flame motes; `pyro_surge_patch` is no longer laid. The Level 30 bloom and the Level 60 snap are unchanged.

## Shape and ranks

Each rank is one retained effect: 41 elements (29 fire planes, 12 flying-rock cubes), 59 bones, the source scaled uniformly and raised .08 blocks into the throat. Flying rocks share the fire's scale.

| Stacks | Rank | Built height | Source scale | Spawn scale | Standing height |
| --- | --- | --- | ---: | ---: | --- |
| 0–1 | red | 1.50 blocks | 0.0910929713 | 2.5 | 3.75 blocks |
| 2–3 | orange | 2.25 blocks | 0.1392054562 | 2.2222 | 5.00 blocks |
| 4 | white | 3.00 blocks | 0.1873179410 | 2.0833 | 6.25 blocks |
| 5 | white | 3.00 blocks | 0.1873179410 | 2.5 | 7.50 blocks |

Heights are the highest visible fire texel, detached fire included. The plugin spawns each rank at standing height over built height.

## Texture

Two 32 × 32 textures per rank. `flame_<rank>.png` recolours only the fire UV regions of the source atlas `lava_obsidian_infernal_judgement_vfx.png` through a gradient map on weighted luma (.2126 R + .7152 G + .0722 B), with stops on the rank's dark, body, hot and core colours; alpha and pixel shading are the source's. `flying_rocks_original.png` is the source atlas byte for byte (SHA-256 `56daa072942aa33d1c0a4f205e24416fc9a5cf0c0f3a9ed230d4db045804a038`).

## Clip

`erupt`, 3.05 s, hold: the source state at its own pace. The flame flies up, shudders at its peak and falls back like a lava burst; the rocks fly out and scale away at the end. The fire grows and collapses by non-uniform scale with exact-zero and step hides.

BetterModel advances one keyframe segment per tick, so every animated channel carries a linear key on each of the clip's 62 ticks (0 to 3.05 s), constant runs included; a channel with fewer keys plays faster than its authored time. `surge_flame_retime.py` writes the clip from the source: it evaluates each source channel as Blockbench does (step, Blockbench's uniform Catmull-Rom spline, or linear) at every tick, scales position samples by the rank's downscale, and keeps rotation and scale samples as they are. Geometry, textures and bones are the delivery's, whose bones keep their source uuids:

    python mobs-src/props/surge_flame_retime.py C:/Repositories/Assets/pyro-surge-shell/flame-surge "C:/Repositories/Animation training/samus2002_AWAKENED_PYROMANCER [v1.1]/ModelEngine/blueprints/RPG_Class_Awakened_Pyromancer/Infernal Judgement/infernal_judgement_vfx.bbmodel"

The evaluation reproduces the artist's Blockbench samples of the same source (8,412 values across the four ranks, at their compressed times) to within 1e-9 relative. A run is byte-stable.

## Hook contract

All at the target's feet, upright, the volcano, the flame and the ring on the same point:

| Tick | Volcano | Flame | Rune ring |
| ---: | --- | --- | --- |
| 0 | spawned, `erupt_low` (0–2 stacks) or `erupt_high` (3–5) held | | `pyro_surge_ring_<rank>_1`, outer edge at the blast radius |
| 1–8 | | | lit frames 2–9, one a tick, then held |
| 4 | | `surge_flame_<rank>` spawned at its spawn scale, `erupt` held | |
| 13 | `subside` replaces the erupt clip | | |
| 22 | removed | | |
| 65 | | removed, its clip played | |
| life − 20 | | | burns away over ten frames, two ticks each |
| life | | | removed: 80 ticks with the Level 45 patch, else 42 |

The flame spawns 0.20 s into the volcano's erupt, which is where the comparison scene starts it. The eruption is the owner's one-shot: the caster's death, logout or class change takes all three down. At 5 stacks, the blue rank, the eruption's particle ring and the geyser's flame burn soul fire, and soul fire takes the place of the lava the eruption and the geyser throw up.

## Verification

The artist played and isolated the source clip in Blockbench and reviewed all four rank GIFs and the peak sheet (`rank_*.gif`, `ranks_peak_sheet.png` in `C:\Repositories\Assets\pyro-surge-shell\flame-surge\`). The comparison scene `flame_surge_scene.bbmodel` there holds four rank copies with editor-only selector keys and is not a shipping model. The retime is checked byte-stable across runs. The in-game checks are a human's: whether the scale-from-zero keys blink in BetterModel, how the crossed transparent planes sort on the client, and the brightness.
