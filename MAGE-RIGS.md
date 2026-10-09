# Mage base visual draft - 2026-09-22

Status: **DRAFT, owner visual review pending**. Authoring assets, textures, contracts,
renders and interactive previews stay in the private Models repository.

- [Private Models draft PR #5](https://github.com/Marzionz/LegendCraft-Models/pull/5)
- [Review index and per-asset links](https://github.com/Marzionz/LegendCraft-Models/blob/mage-rigs/props/mag_review.md)
- [Arcane Ward contract](https://github.com/Marzionz/LegendCraft-Models/blob/mage-rigs/props/mag_arcane_ward.md)
- [Frost Bolt contract](https://github.com/Marzionz/LegendCraft-Models/blob/mage-rigs/props/mag_frost_bolt.md)
- [Fireball source rescale contract](https://github.com/Marzionz/LegendCraft-Models/blob/mage-rigs/props/mag_fireball_rescale.md)

Ward reuses the low-band shield-family geometry. The lance is the base Mage member
of the ice family. Fireball reuses the original public `pyro_fireball` item model at
a smaller proposed runtime scale; its public source files are unchanged.

The private draft also contains two impact candidates under the task's explicit
STATUS BLOCK precedence exception. Their status blocks still request flipbooks while
the later scope split says particles only. That conflict is recorded for owner review;
neither is approved for runtime adoption. Ignite, slow linger and trails remain vanilla
fire/particles.

Five interactive pages and fourteen clip render sets are available privately. Local
pack checks passed (nine commands, 49 acceptance arms). This public PR changes only
this links/status document: no runtime pack assets, configuration, merge or deployment.
