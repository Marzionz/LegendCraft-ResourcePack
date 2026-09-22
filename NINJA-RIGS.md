# Ninja roster props — draft authoring handoff

Four props are built in the private Models repository. This public change contains
links and status only. It adds no model, texture, render, plugin hook or pack asset.

- [Private Models draft PR #13](https://github.com/Marzionz/LegendCraft-Models/pull/13)
- [Review index: previews, renders and comparisons](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_review.md)

| Asset | Draft status | Private contract | Interactive source |
|---|---|---|---|
| Blur substitution log | Rope-bound voxel prop at departure; 18t keyed appear/topple/vanish | [Contract](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_substitution_log.md) | [Preview HTML](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_substitution_log_preview.html) |
| Shuriken Volley star | Four-point voxel projectile; real spin, once-per-rotation glint, keyed flight | [Contract](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_shuriken.md) | [Preview HTML](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_shuriken_preview.html) |
| Smoke Bomb projectile | 22 cubes; measured cap/fuse; texture rivets; keyed draft arc | [Contract](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_smoke_bomb.md) | [Preview HTML](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_smoke_bomb_preview.html) |
| Thousand Cuts per-victim flash | Delivered recolor frames 1–5; two/three instances per struck victim | [Contract](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_thousand_cuts.md) | [Preview HTML](https://github.com/Marzionz/LegendCraft-Models/blob/ninja-rigs/props/nin_thousand_cuts_preview.html) |

Open the HTML locally after obtaining it from the private repo; GitHub source view
does not run interactive pages. Each includes the saved geometry/textures, three.js
from a CDN, orbit, clip picker, play/pause, tick scrub, day/night and a 1.8-block capsule.

Smoke cloud, both blink puffs, shuriken trails/impacts, Thousand Cuts finish/L60 cloud
and ordinary bursts remain particles. The shared Thief blink uses its existing
moonlit birth tint; no shared geometry or texture was forked. Thousand Cuts strike
poses remain CAST-ANIMATION work; no blink drawing was added.

Status blocks govern over the older roster row. The private contracts record the
superseded volume cloud/puff decal, Blur flash consumer discrepancy, five/eight-frame
source discrepancy, and Smoke Bomb's current instantaneous-cloud implementation
versus the kit's collision-stopping projectile. These are explicit review/integration
items, not silently resolved gameplay changes.

Private verification includes all twelve clip GIF/sheet sets, concept comparisons,
the front-speed shuriken, bomb at six/twelve blocks and simultaneous three-victim cuts;
editor/browser transforms and source/lifecycle checks pass. Local pack gates and
isolated rig staging/preflight pass. Owner visual approval, executable-tool review
before merge and actual BetterModel/runtime probes remain outstanding.

Both handoff PRs are drafts. Nothing is merged, deployed or claimed runtime-approved.
