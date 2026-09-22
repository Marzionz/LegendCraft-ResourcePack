# Cryomancer frozen-shell rework — draft handoff

2026-09-22. Scope is **only `status_frozen_shell` v4**, the roster-wide Frozen tomb.
Private authoring work: [Models draft PR #7](https://github.com/Marzionz/LegendCraft-Models/pull/7), branch `cryomancer-rigs`, commit `da02898`.

The draft replaces the berg with one closed, beveled ice monolith and a newly
painted, cutout interpretation of the approved `cryo_prison` material. The public
pack receives only this links/status document. No model, texture, private render,
runtime pack change, merge or deployment is included here.

## Review surfaces (private access required)

- [Complete model contract and v3 history](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell.md).
- [Interactive v3/v4 preview](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell_preview.html): download/open in a browser; three.js CDN, no build. Shared orbit camera, all clips, pause/tick scrub, day/night, captive and 1.8-block reference capsules, 0.55/1/1.3 scales and 16/24-block cameras.
- [Player-fit comparison](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell_comparison_s1.png), [swarm comparison](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell_comparison_s0p55.png), [elite comparison](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell_comparison_s1p3.png).
- [Ice Lance frame-1 continuity board](https://github.com/Marzionz/LegendCraft-Models/blob/cryomancer-rigs/props/status_frozen_shell_ice_lance_continuity.png).
- [Verification evidence](https://github.com/Marzionz/LegendCraft-Models/tree/cryomancer-rigs/tools): `status_frozen_shell_validation.json`, `status_frozen_shell_blockbench_evidence.json`, `status_frozen_shell_preview_evidence.json`, `status_frozen_shell_continuity.json`, `status_frozen_shell_pack_gates.json`.

## Status and retained contract

**DRAFT; owner approval outstanding.** Retains one rig auto-fit-scaled to the victim,
player scale 1, real span approximately 0.55–1.3, mandatory re-anchor, unyawed root,
no `hi` bones, and Core `EntityModels.spawnAt` delivery. The four public clips keep
their names/durations/modes: `form` 15t once, `idle` 80t loop, `crack` 12t once,
`shatter` 16t hold. Old tier/ridge motion is remapped to the monolith as a unit.
Attach/shatter transients remain particles; no second cracked texture.

**Ice Lance frame-1 continuity is a MISMATCH.** Its pointed, stepped berg, deeper
blue body and dense white fracture web do not continue the new flat-capped pale
cyan monolith and cutout windows. The approved sheet was checked read-only and
remains unchanged. Owner follow-up is required; no shatter-sheet work is included.

`ice_break` ogg versus the ruled vanilla glass-break/chime stack remains open for
hook time. The VFX header names the prop correctly, while its older FROST_ENCASE
body still says translucent PACKED_ICE BlockDisplay / approximately 3-tick growth.
That contradiction is recorded privately; the hub was not edited.

Validation includes a closed 26-vertex/48-triangle manifold, binary alpha,
embedded/loose PNG equality, tick-aligned keys, 134 Blockbench frames covering old
and new clips, and 871 browser/editor element-bound comparisons within .002u with
zero JavaScript errors. All nine local public-pack gate commands pass, 49 test arms.
BetterModel mesh export, armor/captive cutout visibility, lighting, fit/re-anchor,
terrain seating and hook timing still need human in-game checks.

Nothing else in Cryomancer was built or edited: Absolute Zero wavefront, Ice Lance
sheet, Frost Nova patch, Permafrost, killed Chill body prop and all shipped az/frost
props remain outside this handoff. No other class's authoring files changed.
