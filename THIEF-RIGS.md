# Thief base — draft visual handoff

**2026-09-22: DRAFT / owner review pending.** One asset: Ambush's full-health
bonus-proc flash. Art, editable models, textures, renders and executable preview
remain in the private Models repository. This public change contains links and
status only; it changes no served resource-pack files.

| Review surface | Private link |
|---|---|
| Models draft PR | [LegendCraft-Models #11](https://github.com/Marzionz/LegendCraft-Models/pull/11) |
| Review index | [thf_ambush_review.md](https://github.com/Marzionz/LegendCraft-Models/blob/thief-rigs/props/thf_ambush_review.md) |
| Interactive preview | [thf_ambush_flash_preview.html](https://github.com/Marzionz/LegendCraft-Models/blob/thief-rigs/props/thf_ambush_flash_preview.html) — download and open; three.js CDN, no build step |
| Contract | [thf_ambush_flash.md](https://github.com/Marzionz/LegendCraft-Models/blob/thief-rigs/props/thf_ambush_flash.md) |
| Concept comparison | [approved sheet and production strip](https://github.com/Marzionz/LegendCraft-Models/blob/thief-rigs/props/thf_ambush_flash_comparison.png) |
| Gameplay / family | [day/night, 16/24 blocks, beside shipped blink](https://github.com/Marzionz/LegendCraft-Models/blob/thief-rigs/props/thf_ambush_flash_gameplay_sheet.png) |
| Clip render | [Blockbench GIF](https://github.com/Marzionz/LegendCraft-Models/blob/thief-rigs/props/thf_ambush_flash_preview.gif) |

`thf_ambush_flash`: one visible 1-block billboard, four painted frames at 1 tick
each; hairline, glint with crimson cross, breakup, dusk smear. Born on the damage
tick only when the full-health bonus lands; gone by tick 4. An ordinary Ambush
shows its cast animation and normal hit feedback and **NO flash**: the flash's
absence is itself information.

Palette is ruled dusk-violet and steel with kill-crimson as the only saturated
accent. Only frame 2's glint and cross are emissive; the shadow follows world light.
The private contract carries the sound stack and all hook/export checks.

The explicit STATUS-block flipbook instruction owns this conditional crit read.
Ordinary Ambush feedback, every ordinary impact, splash and small burst remain
particles. Never double-layer a full particle burst with the proc flipbook.
The lunge-and-stab stays in the melee CAST-ANIMATION workstream. Flurry is unchanged;
Roll earns no new asset and its dodge roll is already shipped. No existing
`thf_blink_flash*` asset is modified.

Evidence: saved Blockbench render pass; 102 preview lifecycle samples; 42 matching
editor/browser bone scales; structural/art validation; local prop staging and
preflight; all nine local pack commands (49 test arms) passed. Private evidence
JSONs are linked from the review index. Owner visual review and actual BetterModel
billboard, emissive, frame timing, cleanup, event-selection and sound probes remain
owed. No merge, live staging or deployment occurred.
