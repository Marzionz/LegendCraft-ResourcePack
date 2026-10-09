# Cryomancer second pass — draft handoff

2026-09-22. Two private draft assets: **status_frozen_shell v5** and new
**az_cold_front**. [Models draft PR #7](https://github.com/Marzionz/LegendCraft-Models/pull/7),
branch cryomancer-rigs, commit `a5a2567c6585e80e3cece16a06842e9522f11da5`. This public PR contains links and status only.

## Review

- [V3 / v4 / v5 interactive comparison](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell_preview.html),
  [tomb contract](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell.md),
  [same-scale comparison](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell_comparison_s1.png).
- [Absolute Zero interactive preview](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/az_cold_front_preview.html),
  [ring contract and exact per-tick table](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/az_cold_front.md),
  [day/night acceptance board](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/az_cold_front_acceptance.png),
  [approved concept comparison](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/az_cold_front_concept_comparison.png).
- [Tomb / comparison-only cage idle](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/tools/status_frozen_shell_tomb_cage_idle.gif),
  [cage still](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/tools/status_frozen_shell_cage_comparison_s1.png),
  [Ice Lance hue board](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell_ice_lance_continuity.png).

Private access required. Download the HTML and open locally; each embeds real
model data and textures, loads three.js from CDN, and needs no build step.

## Ruling applied

V5 is one 18×36×18u beveled monolith, four-tone cutout ice. Form is full size at
tick 0, idle is a three-tick facet shimmer with no mass motion, crack only brightens
facet lines, and shatter cuts immediately while ten shards pop and drift for 34t.
Fit-scale, mandatory re-anchor, identity root and EntityModels.spawnAt survive.
The explicit new dimensions supersede v4's oversized envelope. Exact/no-blend
playback and the new fit envelope still require a runtime check.

The approved Ice Lance frame 1 is now the **burst over the empty shell space**,
not a silhouette swap frame. The sheet remains unchanged. Its deeper blue versus
the pale tomb still needs the owner's hue-continuity judgment.

Absolute Zero uses eight registered strip frames at two ticks each. Separate
sweep_l20 and sweep_l60 clips arrive at authored radii 8 / 12 at tick 12 and finish
frames 7–8 there. Matching exits cut the wall and release sixteen chips for 20t.
Entity scale stays 1; all travel and frame stepping are authored keyframes.

The 16–24-face limit conflicts with a face under ~1.6 blocks at radius 12: the
chosen 24 faces are 3.133 blocks wide; 48 would be required for 1.6. A flat polygon
also cannot match a circle at every point. This draft is inscribed: corners match
radius exactly, face centers sit up to 0.103 blocks inside at L60, never outside.
These are explicit review departures, not claims that the incompatible conditions
were all met.

## Verification / status

Both remain **DRAFT, not owner approved**. Static structure/material/timing/radius
checks pass. Blockbench captured 144 frames across 17 delivered clips plus the
comparison cage's idle. Preview/editor agreement: 240,894 scalar components,
maximum difference .00001 (editor zero-scale clamp), zero significant mismatch or
JavaScript error. Nine pack commands / 49 test arms pass; local prop staging and
preflight pass. Human BetterModel export, frame stepping, cutout/emissive lighting,
terrain, tier/tick alignment, renderer cost and crowded-combat review remain owed.

No runtime pack contents, plugins, balance, hub, sounds or shipped az/frost props
changed. Frost Nova patch, Ice Lance sheet, Permafrost and Chill body prop remain
out of scope. No merge or deployment. Stale FROST_ENCASE wording is recorded in
the private contract; the hub was not edited.
