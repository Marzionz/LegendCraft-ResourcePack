# Conflagration caster sigil

`pyro_conflag_sigil` is a BetterModel motion prop attached at the caster's feet. Play `windup` held, retimed from 3.00 seconds to the actual quiet time (about 3.20 seconds at base tuning). At quiet, switch to `expand` at authored speed; remove the prop six ticks later at detonation. Brightness and attachment belong to the plugin.

## Geometry and texture

One flat element, UUID `59bbd5c1-869f-55c1-7168-6eb5fca7b27b`, edited through the Blockbench MCP at `http://localhost:3000/bb-mcp`:

- `from: [-24, 0.40, -24]`
- `to: [24, 0.40, 24]`
- `origin: [0, 0.40, 0]`; element rotation `[0,0,0]`.
- Size **48 x 0 x 48 u**, or 3 x 3 blocks. Expansion reaches 144 x 0 x 144 u.
- Only **up** is textured: UV `[0,0,47,47]`, face rotation 0. Every other face has `texture: null`.
- Atlas image top maps to north (-Z), and image right to east (+X), in the rest pose. The native up-face UV vertices confirm this orientation.

The circle lies flat in its exported vertices. No bone rest rotation supplies its placement. Native Blockbench gives a zero-height cube preview thickness of 0.001 u above its authored y=0.40 surface; the exported element has exactly zero height.

Bought source: `C:/Repositories/Animation training/samus2002_AWAKENED_PYROMANCER [v1.1]/ModelEngine/blueprints/RPG_Class_Awakened_Pyromancer/Infernal Judgement/infernal_circle.bbmodel`. Source SHA256: `5bad79e0e7d84d7c17ba036a45c1a415a0bf0c9d82c8761f09a8a6bc283e3b79`.

The unchanged 128 x 128 RGBA atlas is embedded and stored as `pyro_conflag_sigil.png` beside this file and under `src/assets/legendcraft/textures/entity/`. Resource location `legendcraft:entity/pyro_conflag_sigil`; atlas SHA1 **`2c6949687283dda1b471f5b8a010e388f989ade4`**. No repaint or emissive companion.

## Bones

Every bone has rest rotation `[0,0,0]`. The identity root follows the unyawed prop-root convention in the Blockbench skill's `SIGNS.md`.

| Bone | Parent | Origin | Rotation |
| --- | --- | --- | --- |
| `root` | scene | `[0,0,0]` | `[0,0,0]` |
| `plane_mount` | `root` | `[0,0.40,0]` | `[0,0,0]` |
| `h_magic_fire_circle` | `plane_mount` | `[0,0.40,0]` | `[0,0,0]` |
| `h_out` | `h_magic_fire_circle` | `[0,0.40,0]` | `[0,0,0]` |

`plane_mount` is an identity organizational bone. Visible motion is keyed on `h_out`, around the vertical Y axis at `[0,0.40,0]`. Native format-5 world transforms confirm negative Y keys move a +X mark toward +Z: clockwise from above. Do not apply the older format-4 keyframe sign inversion to this file.

## Clips

| Clip | Playback | Length | Behavior |
| --- | --- | --- | --- |
| `windup` | HOLD | 3.00 s / 60 ticks | Linear yaw 0 to -120 degrees; scale X/Z from 0 to 1 over ticks 0-2, then hold 1. Y scale stays 1. |
| `expand` | HOLD | 0.30 s / 6 ticks | Linear yaw -120 to -150 degrees; X/Z scale 1 to 3 with cubic ease-out. Last frame holds. |
| `hidden` | LOOP | 0.05 s / 1 tick | Both source bones have step scale `[0.001,0.001,0.001]` at 0 and 0.05 s. |

| Channel | Keys | Interpolation |
| --- | --- | --- |
| `windup.rotation` | `0: [0,0,0]`; `3.00: [0,-120,0]` | Linear |
| `windup.scale` | `0: [0,1,0]`; `0.10: [1,1,1]`; `3.00: [1,1,1]` | Linear |
| `expand.rotation` | `0: [0,-120,0]`; `0.30: [0,-150,0]` | Linear |
| `expand.scale` | X=Z: `0: 1`; `0.05: 1.842592593`; `0.10: 2.407407407`; `0.15: 2.75`; `0.20: 2.925925926`; `0.25: 2.990740741`; `0.30: 3`. Y=1. | Linear between tick samples |

Expansion uses `1 + 2*(1-(1-t/0.30)^3)`. There are no position keys. `windup(3.00)` and `expand(0)` have identical transforms. The nominal windup playback multiplier for a 3.20-second quiet is `3.00/3.20 = 0.9375`; use the actual quiet interval. Do not loop either visible clip.

## Verification and renders

The saved file was reloaded into an isolated Blockbench project. Native geometry, UVs and animated world transforms supply the renders; an unlit texture material makes the art readable against grey ground. No render-only rig transforms are used. The top camera is `(0,190,0.001)` u with north upward and 55-degree vertical FOV. The side orthographic diagnostic includes native geometry edges and a grey y=0 reference line, so a zero-height face remains visible edge-on.

- [Native top-down rest still](pyro_conflag_sigil_render_top.png)
- [Native side rest still](pyro_conflag_sigil_render_side.png)
- [Full windup then expand GIF](pyro_conflag_sigil_render_swap.gif), 50 ms per frame
- [Motion contact sheet](pyro_conflag_sigil_render_contact.png)

Verified the exact exported flat element, all four zero bone rotations, up-face UV orientation, native clockwise Y motion, equal clip-swap transforms, tick grid, playback modes, unchanged atlas bytes and source/stage byte equality. The renders were visually inspected.

`deploy-rigs.ps1 -Prop` and `-Prop -Preflight`: **DEPLOYABLE**. Staged `dist/props/models/pyro_conflag_sigil.bbmodel` SHA1 **`18210ceafb7b6b2e8cfc8a4f771a5296967439ae`**. `build.ps1` and `check_pack_manifest.py --pack dist/LegendCraft-Pack-0.2.4.zip --source-tree src` passed: 490 item models, 17 sounds, 5 sounds.json. Plugin-contributed assets are unchecked because no plugin source was supplied.

In-game BetterModel playback, caster attachment, brightness and alpha sorting remain runtime checks. This contract stages an asset; it does not change plugin code or deploy to a server.
