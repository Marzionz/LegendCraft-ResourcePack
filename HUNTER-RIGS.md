# Hunter props — draft authoring handoff

2026-09-22. Private Models branch `hunter-rigs`, based on freshly fetched
`origin/main`. Public branch is links/status only; no runtime assets, generated
pack changes, merge or deployment.

Private review index:
[Hunter prop review](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_review.md).
Owner approval and runtime verification remain outstanding.

| Prop | Private contract / renders / preview |
|---|---|
| `hnt_ensnaring_trap` | [Contract](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_ensnaring_trap.md), [comparison](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_ensnaring_trap_comparison.png), [HTML](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_ensnaring_trap_preview.html), [enemy view](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_ensnaring_trap_enemy_browser.png) |
| `hnt_venom_stacks` | [Contract](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_venom_stacks.md), [comparison](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_venom_stacks_comparison.png), [HTML](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_venom_stacks_preview.html) |
| `hnt_prey_mark` | [Contract](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_prey_mark.md), [comparison](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_prey_mark_comparison.png), [HTML](https://github.com/Marzionz/LegendCraft-Models/blob/hunter-rigs/props/hnt_prey_mark_preview.html) |

Download the private HTML and open locally; three.js loads from a CDN with no
build step. All model/texture/render bytes stay private. All 18 clips have
editor GIFs and numbered sheets. Three pages/all clips pass browser checks;
797 sampled bone transforms match Blockbench within 1e-14. Structural checks
and all public-pack gate commands pass, including 49 acceptance test arms.

Trap geometry is Hunter/allies only. The enemy screenshot suppresses the
whole preview model; it illustrates `hideFrom`/`showTo`, without enforcing
server visibility. The mandatory periodic purple particle and click remain
hook work; no enemy model tell is built. Both marks use the everyone-visible
chest carousel, at most three quiet slots; above-head remains CC-exclusive.

The approved purple three-stack art conflates capped poison with Weakened;
the current kit permits capped-only states. Resolve the truthful runtime
mapping before adopting it. Owner must also judge silhouette/paint, actual
brightness/billboarding, viewer tracking, armor and crowded-combat reads.

Companion/direwolf, generators, server/plugin code and hub are unchanged.
The stale Models README wolf retexture claim is recorded in the private
handover, not acted on. All ordinary impacts, splashes, summon poofs and
small bursts remain particles; Hunter has no STATUS-block burst exception.
