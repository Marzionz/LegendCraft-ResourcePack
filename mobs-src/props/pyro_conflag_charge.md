# Conflagration flame-charge swirl

`pyro_conflag_charge` is a BetterModel motion prop attached at the caster's feet for Conflagration's 70-tick (3.5-second) channel. Play `charge` continuously at authored speed, then remove the prop on detonation. Brightness belongs to the plugin; the texture and geometry contain no added glow. There is no damage, jump burst, projectile or detonation animation in this asset.

## Source and extraction

Bought source: `C:/Repositories/Animation training/samus2002_AWAKENED_PYROMANCER [v1.1]/ModelEngine/blueprints/RPG_Class_Awakened_Pyromancer/Infernal Judgement/infernal_judgement_vfx.bbmodel`, animation `charge_jump` (2.5 seconds). Original file SHA256: `7bf42a96b5e2bb92b4e545f6dfe0b9039880ab083cf5c8cf5c99199aa6267a96`; unchanged after extraction.

The source was copied to scratch, loaded into Blockbench through its MCP, and trimmed with native outliner operations. Geometry was not generated as JSON. All 24 retained cube/plane elements preserve the source UUIDs, coordinates, pivots, rotations, UVs, face directions, inflate and shading. Both authored textured faces of each plane remain. Only texture references are remapped from source index 1 to the retained atlas at index 0.

Mini flames, flame balls, smoke, spear, magic circle, impacts, stones, lava/obsidian, hitbox and the other four animations are absent.

## Bones and orientation

42 bones total: new identity `root`, plus these 41 source bones:

- `allef_flame_charge`.
- `ef_flame_charge1` through `ef_flame_charge8`.
- `group9` through `group36`, and `group65` through `group68`.

Each flame has one carrier child and three articulated ribbon bones. Flame 1 has `group65 -> group68 -> group67 -> group66`; flames 2-8 have the respective four-bone chains `group9 -> group10 -> group11 -> group12` through `group33 -> group34 -> group35 -> group36`. Three elements per flame, 24 total.

The source `allef_flame_charge` is already a top-level bone with origin and rest rotation `[0,0,0]`. It is parented unchanged under the added `root`, also at `[0,0,0]` with zero rotation. No 180-degree mob yaw, geometry rotation, scale correction or pivot relocation is applied. This follows the unyawed prop-root rule in the skill's `SIGNS.md`.

The source and delivered file retain Blockbench format 5.0. Its native animation coordinates must not be relabeled as legacy 4.x: BetterModel has distinct version-dependent rotation/position conversion. Source rotation and position values were retained and checked through native Blockbench poses, rather than reinterpreted from the legacy sign table. The exported file includes native groups and expanded outliner metadata so the existing staging and preview readers can inspect the same hierarchy. The expanded metadata does not construct new geometry.

## Clips

| Clip | Playback | Length | Contract |
| --- | --- | --- | --- |
| `charge` | LOOP | 1.60 s / 32 ticks | Four repetitions of the bought 0.40 s ribbon pulse, with eight flames staggered by 0.05 s. One full carrier revolution. |
| `hidden` | LOOP | 0.05 s / 1 tick | All 41 source charge bones have step scale `[0.001,0.001,0.001]` at both endpoints; identity root stays unchanged. |

The source contains three 0.40-second pulse repetitions staggered across 0-1.50 seconds. `charge` repeats that same pulse pattern to complete four periods in 1.60 seconds. Wrapped pulse tails fill the start, avoiding a fresh empty startup on each repeat. Source linear and Catmull-Rom keys retain their interpolation; sampled boundary keys close channels that cross the loop boundary. Every key is on the 0.05-second tick grid. Static channels are held from 0 through 1.60 seconds. The carrier's full turn is spread over 1.60 seconds rather than the source's 1.50 seconds.

There are 73 animated channels. **72 have exactly equal first/last values.** The sole exception is `allef_flame_charge.rotation`, unwrapped yaw **0 -> -360 degrees**, which is the identical world orientation and preserves continuous rotation. Literal zero at the final key would erase/reverse the source spin. This exception was approved as PYRO-R6, hub `0240761d`, in `C:/Users/omarz/.claude/comms/orchestrator-inbox.md` and is part of the handoff contract.

At normal speed the 70-tick channel spans two full loops plus six ticks of the third. The plugin removes the prop at detonation; no terminal burst or fade is authored.

## Texture

`pyro_conflag_charge.png`, 128 x 128 RGBA, embedded in the model and copied unchanged beside it and to `src/assets/legendcraft/textures/entity/pyro_conflag_charge.png` (`legendcraft:entity/pyro_conflag_charge`). SHA1: `558fda23a5c214145b1f14d3b3851a5f6a329bfe`.

**This is the source-bound `hellfire_overblast_vfx.png` atlas, source texture index 1.** Every one of the 48 retained textured faces uses it. The brief named the model's index-0 `infernal_judgement_vfx.png`, which these elements do not use. The orchestrator inbox answered this discrepancy: preserve the actual bound atlas byte-for-byte, exported under the prop's name. No repaint, palette adjustment, alpha adjustment or emissive companion was added.

## Verification and renders

Verified 24 source elements, 41 retained source bones, unchanged rest transforms and UVs, the exact bound atlas bytes, unchanged source SHA256, identity root, two clips, every tick-aligned channel, hidden scales, endpoint values and staged/source byte equality. Reloaded the delivered file in Blockbench before native rendering. All native vertex positions at 0 and 1.60 seconds match within **2.842170943040401e-14 model units**.

- [Contact sheet](pyro_conflag_charge_render_contact.png): 17 poses over one cycle, including equal start/end; bystander camera `(0,1.6,6)` blocks, looking at `(0,1,0)`, 90-degree vertical FOV. Close ribbons can cross the edge of this eye-level view; source geometry is not scaled to fit it.
- [Three-cycle GIF](pyro_conflag_charge_render_charge.gif): 96 frames, exactly 20 fps / 50 ms per frame, 4.80 seconds. Cycle labels identify both interior loop seams. Same eye camera.
- [Above](pyro_conflag_charge_render_above.png): 0.20-second pose, camera 10 blocks above origin, perspective 65-degree FOV. The source ribbons are thin from directly overhead.
- [Interactive prop preview](pyro_conflag_charge_render_preview.html): generated with the skill's `prop_preview.py`, then adapted to play native Blockbench bone-transform samples from the delivered rig at 20 fps. This preserves the source easing/signs instead of the template's linear-only approximation. Includes playback, scrub and orbit controls. Three.js/fonts load from the template's external CDNs.

Every render includes mid-grey ground, dark sky and a 2-block-tall stand-in at the prop origin. The native Blockbench mesh/material scene rendered the PNG/GIF frames; the stand-in and ground are preview-only scene objects. Source geometry reaches below the ground during its authored motion; it was not lifted or reshaped. The contact sheet and overhead PNG were visually inspected. Browser policy blocked opening the local preview HTML, so its browser playback is unverified; the deliverable still has native Blockbench render verification.

Staging and `-Prop -Preflight` passed. Staged model: `dist/props/models/pyro_conflag_charge.bbmodel`, SHA1 **`29d2f17f3343f806502bd89429feb3c0ac4267ae`**. `build.ps1` and `check_pack_manifest.py --pack dist/LegendCraft-Pack-0.2.4.zip --source-tree src` passed: 439 item models, 12 sounds, 3 sounds.json. Plugin-contributed assets remain unchecked by that manifest command (no plugin source supplied). Pack ZIP SHA1: `cbc80620039dc2e328482f85586d7930656675cb`.

In-game wearer anchoring, BetterModel playback, brightness override, alpha sorting and removal at detonation remain hook-time checks. This session stages only and changes no plugin code.

## History and skill overrides

2026-09-28: extracted the bought charge subtree, retained its actual atlas, looped its phased motion, rendered and staged it. Inbox rulings accepted rotational yaw closure and the source-bound atlas discrepancy.

The brief overrides the skill's preview pause: `legendcraft-blockbench/SKILL.md` says "END THE TURN" and forbids the commit until a later preview ruling; `PROP-PREVIEW.md` says "Then the turn ends". The explicit instruction to continue through commit/report governed this build. The skill also says "commit and push authoring work there"; the brief instead requires one commit on this worktree branch with no push. The scratch render loop used the skill's native Blockbench posing method with scene dressing and fixed 20-fps sampling needed by this brief; it did not use the stock GIF script's endpoint-inclusive frame timing.
