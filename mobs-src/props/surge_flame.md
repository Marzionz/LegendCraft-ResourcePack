# Flame Surge ranked flame

Source pack: `C:\Repositories\Animation training\samus2002_AWAKENED_PYROMANCER [v1.1]`; its licence permits modification.
Source model: `ModelEngine\blueprints\RPG_Class_Awakened_Pyromancer\Infernal Judgement\infernal_judgement_vfx.bbmodel` (SHA-256 `7bf42a96b5e2bb92b4e545f6dfe0b9039880ab083cf5c8cf5c99199aa6267a96`).
Source clip: `lava_obsidian_infernal_judgement`, 3.05 s, under `lava_obsidian_pieces_eruption_vfx`.
Retained: the ground-flame tongues (`allef_impactv1`, `allef_impactv2`), the rising streaks (`allef_impact_mini`), the paired flying fragments (`allef_mini_flame2`) and the flying rocks (`allef_stone`), with all their descendants. Excluded: the grounded spike ring `allef_stone_impact` (Conflagration's). No smoke is visible in this state.

`surge_flame_red`, `surge_flame_orange`, `surge_flame_white` and `surge_flame_blue` are BetterModel rigs that erupt out of the throat of the `surge_volcano` pimple when Flame Surge lands. The rank follows the target's Burning stacks. The volcano itself is the shipped rig, unchanged. Together they replace the painted `pyro_surge_burst` fire pillar on the plugin side. The painted ground rune ring, [`pyro_surge_ring`](pyro_surge_ring.md), still plays under them. The Level 45 patch draws only flame motes; `pyro_surge_patch` is no longer laid. The Level 30 bloom and the Level 60 snap are unchanged.

## Shape and ranks

Each rank is one retained effect: 41 elements (29 fire planes, 12 flying-rock cubes), 59 bones, the source scaled uniformly and raised .08 blocks into the throat. Flying rocks share the fire's scale.

| Stacks | Rank | Flame height | Source scale |
| --- | --- | ---: | ---: |
| 0–1 | red | 1.50 blocks | 0.0910929713 |
| 2–3 | orange | 2.25 blocks | 0.1392054562 |
| 4 | white | 3.00 blocks | 0.1873179410 |
| 5 | blue | 3.75 blocks | 0.2354304259 |

Heights are the highest visible fire texel, detached fire included.

## Texture

Two 32 × 32 textures per rank. `flame_<rank>.png` recolours only the fire UV regions of the source atlas `lava_obsidian_infernal_judgement_vfx.png` through a gradient map on weighted luma (.2126 R + .7152 G + .0722 B), with stops on the rank's dark, body, hot and core colours; alpha and pixel shading are the source's. `flying_rocks_original.png` is the source atlas byte for byte (SHA-256 `56daa072942aa33d1c0a4f205e24416fc9a5cf0c0f3a9ed230d4db045804a038`).

## Clip

`erupt`, 0.90 s, hold. The 3.05 s source state is compressed 3.3888889× and sampled onto linear keys on the 0.05 s grid, with constant and collinear keys removed. The ground flame shows from about 0.04 s to 0.27 s; the rocks fly until 0.90 s. The fire grows and collapses by non-uniform scale with exact-zero and step hides, and the rocks scale out at the end.

The artist's delivery opens the clip with a 0.20 s lead, timed to the volcano inside the comparison scene. `surge_flame_retime.py` cuts it: keys move 0.20 s earlier, the pose each channel holds at 0.20 s becomes its key at 0, and the clip runs 0.90 s:

    python mobs-src/props/surge_flame_retime.py C:/Repositories/Assets/pyro-surge-shell/flame-surge

## Hook contract

All at the target's feet, upright, the volcano, the flame and the ring on the same point:

| Tick | Volcano | Flame | Rune ring |
| ---: | --- | --- | --- |
| 0 | spawned, `erupt_low` (0–2 stacks) or `erupt_high` (3–5) held | | `pyro_surge_ring_<band>` frame 1 (low 0–2, mid 3–4, high 5), outer edge at the blast radius |
| 1–11 | | | frames 2–12, one a tick |
| 4 | | `surge_flame_<rank>` spawned at scale 1, `erupt` held | |
| 12 | | | removed |
| 13 | `subside` replaces the erupt clip | | |
| 22 | removed | removed | |

The flame spawns 0.20 s into the volcano's erupt, which is where the comparison scene starts it. The eruption is the owner's one-shot: the caster's death, logout or class change takes all three down. The eruption's particle ring burns soul fire at 5 stacks, the blue rank.

## Verification

The artist played and isolated the source clip in Blockbench and reviewed all four rank GIFs and the peak sheet (`rank_*.gif`, `ranks_peak_sheet.png` in `C:\Repositories\Assets\pyro-surge-shell\flame-surge\`). The comparison scene `flame_surge_scene.bbmodel` there holds four rank copies with editor-only selector keys and is not a shipping model. The retime is checked byte-stable across runs. The in-game checks are a human's: whether the scale-from-zero keys blink in BetterModel, how the crossed transparent planes sort on the client, and the brightness.
