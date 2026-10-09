# Sniper — draft visual handoff

**Draft, owner review pending. Nothing merged or deployed.**

All authoring assets remain in the private Models repository:

- [Models draft PR #10](https://github.com/Marzionz/LegendCraft-Models/pull/10)
- [Review index](https://github.com/Marzionz/LegendCraft-Models/blob/sniper-rigs/props/snp_review.md)
- [Private CHEST sight-mark](https://github.com/Marzionz/LegendCraft-Models/blob/sniper-rigs/props/snp_heartseeker_mark.md)
- [Public detonation](https://github.com/Marzionz/LegendCraft-Models/blob/sniper-rigs/props/snp_heartseeker_burst.md)
- [Wearer-visible planted anchor](https://github.com/Marzionz/LegendCraft-Models/blob/sniper-rigs/props/snp_blitz_anchor.md)
- [Horizontal hero bow](https://github.com/Marzionz/LegendCraft-Models/blob/sniper-rigs/props/snp_blitz_bow.md)

Four assets include complete contracts, saved models and editable textures,
22 clip GIFs and sheets, concept comparisons, and self-contained interactive
three.js previews. Download/open preview HTML; GitHub does not execute it.

The proposed one-block mark and every derived fit are explicitly **DERIVED AT
RIG TIME, NOT OWNER-APPROVED** in its contract and session handover. Combined
mark/burst gameplay views support that ruling. The mark and lock sounds are
private to its Sniper; the detonation and its sounds are public. Gold texture
exceptions are confined to the full-charge pip and burst payoff frame.

The bow's span is 3.75 blocks, horizontal at chest height in front of its
wearer. Bystander and standing/sneaking wearer comparisons show the intended
self-view seam. Browser hiding is a representation, not runtime enforcement.
The anchor stays wearer-visible. Both state props have paired exits and no
exit on an L60 cooldown reset. The current kit's player-fired shot events take
precedence over older auto-fire VFX wording.

Arrow Blitz arrow lines, light/flare wisps, muzzle cracks, reset glints,
ordinary impacts/explosions, splashes and small bursts remain particles.
Bolt's optional shockwave is not commissioned. Evasive Shot has no rig.
The grapple line remains particles. The explicitly commissioned Heartseeker
STATUS-block detonation is built; never duplicate it with a full particle dome.

Saved-model, palette, lifecycle, chain-module and exact rest-span checks pass;
all 22 browser clips have no JavaScript errors and 1,898 bone samples match
Blockbench. Local public-pack gates pass, including 49 test arms.

Owner visual approval and human BetterModel checks remain outstanding:
billboards, emissive/brightness, culling, actual attachments/armor, crowd read,
per-viewer tracking, both wearer eye heights, timing and sound mix.
This file is links/status only; no private asset or runtime pack change.
