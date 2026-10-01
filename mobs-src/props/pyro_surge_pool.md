# Flame Surge magma pool

The ground of Flame Surge's Level 45 field: a magma pool in the flame's rank that cools toward a crust over the field's life and burns away as the field ends, together with the [rune ring](pyro_surge_ring.md#ranks-stand-and-burn-away). Item-model flipbook frames, not a BetterModel rig.

Source: the bright magma disc of the samusdev pack's Magma Dash ground pool, `C:\Repositories\Animation training\samus2002_AWAKENED_PYROMANCER [v1.1]\ModelEngine\blueprints\RPG_Class_Awakened_Pyromancer\Magma Dash\magma_dash_vfx.png`, the 16 × 16 cell at the atlas origin. The pack's licence permits modification.

## Frames

`surge_pool_ranks.py` (durable, re-runnable) writes them:

    python mobs-src/props/surge_pool_ranks.py "C:/Repositories/Animation training/samus2002_AWAKENED_PYROMANCER [v1.1]/ModelEngine/blueprints/RPG_Class_Awakened_Pyromancer/Magma Dash/magma_dash_vfx.png"

Per rank, 22 item models: `pyro_surge_pool_<rank>_1..12` cool from the rank's heat to its crust, and `pyro_surge_pool_<rank>_burn_1..10` burn frame 12 away. 88 frames, 264 files.

| Rank | Stacks | Ramp (dark, body, hot, core) | Gamma | Crust |
| --- | --- | --- | ---: | --- |
| `red` | 0–1 | `#3A0806` `#8E1A0C` `#D8361A` `#FF7A3A` | 1.0 | `#240A08` |
| `orange` | 2–3 | `#4A1206` `#C0400A` `#FF8A1A` `#FFD24A` | 1.0 | `#240A08` |
| `white` | 4 | `#C86A2A` `#FFC470` `#FFF2CC` `#FFFFFF` | 0.5 | `#2A100A` |
| `blue` | 5 | `#0E2C3A` `#2E8FB8` `#4CC7FF` `#E8FFFF` | 0.8 | `#0A1622` |

The disc is doubled to 32 × 32 by nearest-neighbour. Each texel's luma, normalised over the disc and raised to the rank's gamma, maps through the ramp. Cooling frame n pulls each texel toward the crust by `clamp(c × (1.6 − 1.2 × luma))` with `c = 0.85 × (n − 1) / 11`: the dark skin crusts first and the bright seams glow through longest. The burn-away is the rune ring's own (noise field, front, hot edge and ember per rank), so both burn out together.

Every frame is one horizontal 32 × 32 u plane at y 8.1, x/z −8..24, its up face showing the whole frame. At scale 1 the disc's edge is 1 block from the centre.

## Hook contract

One item display on the eruption's ground point, unyawed, scaled to the field's radius over 1 block (3 at base tuning), for the field's life L (80 ticks at base tuning):

| Tick | Frame |
| ---: | --- |
| `n × (L − 20) / 12`, n 0..11 | cooling 1–12 |
| L − 20 to L − 1 | burn 1–10, two ticks each, with the ring's |
| L | removed |

Over it until the burn-away, a bubble rises every 2 ticks at its own point within 0.85 of the radius: dust in the stacks' heat colour swelling for 3 ticks, then a pop of the eruption's lava (soul fire at 5 stacks), a dust spray and `block.lava.pop` at volume 0.35, pitch 0.8–1.3. `block.lava.ambient` plays at the centre every 30 ticks.

## Verification

The frames were checked by eye on a contact sheet of every rank at cooling 1, 4, 8, 12 and burn 2, 5. The pool's read on the ground, its sorting under the rune ring and the bubbles are a human's in-game checks.
