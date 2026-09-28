# Conflagration caster sigil

`pyro_conflag_sigil` is a BetterModel motion prop worn at the caster's feet. Play `windup` held, retimed from its authored 3.00 seconds to the channel's quiet (about 3.20 seconds at base tuning). At the quiet, replace it with `expand`, held at authored speed. Remove the prop at detonation, six ticks later. Brightness and attachment belong to the plugin.

## Source and extraction

Bought source: `C:/Repositories/Animation training/samus2002_AWAKENED_PYROMANCER [v1.1]/ModelEngine/blueprints/RPG_Class_Awakened_Pyromancer/Infernal Judgement/infernal_circle.bbmodel`. Source SHA256: `5bad79e0e7d84d7c17ba036a45c1a415a0bf0c9d82c8761f09a8a6bc283e3b79`; unchanged after extraction.

The source was copied to scratch and loaded through the Blockbench MCP at `http://localhost:3000/bb-mcp`. Native outliner operations removed the hitbox, retained the circle subtree, and added the root and placement bone. No geometry was generated as JSON. The retained plane keeps UUID `59bbd5c1-869f-55c1-7168-6eb5fca7b27b`, coordinates `[-24,-24,-1]` to `[24,24,-1]`, pivot `[0,0,-1]`, and the source north-face UV `[0,0,47,47]`. Both source bones retain their UUIDs, pivots and zero rest rotations. The source's disabled export flags on the circle and its carrier are enabled.

The source north face becomes the upward-facing surface after the rest rotation. It is the only textured face; all other face texture references are null. This preserves the authored UV and avoids two coplanar textured surfaces. The seven source clips are replaced by the three clips below; no bought animation curve is represented as an unchanged extraction here.

## Bones and orientation

One plane, four bones:

| Bone | Parent | Rest origin | Rest rotation |
| --- | --- | --- | --- |
| `root` | scene | `[0,0,0]` | `[0,0,0]` |
| `plane_mount` | `root` | `[0,-0.3,-0.3]` | `[90,0,0]` |
| `h_magic_fire_circle` | `plane_mount` | `[0,0,-1]` | `[0,0,0]` |
| `h_out` | `h_magic_fire_circle` | `[0,0,-1]` | `[0,0,0]` |

The added placement bone lays the plane flat and maps its authored centre to **`[0,0.40,0]`**, including in the rest pose. It does this without moving any source vertex or pivot. The plane is **48 x 48 u**, or 3 x 3 blocks, before expansion; scale 3 produces a 144 x 144 u plane. Its height remains 0.40 u throughout both visible clips because scaling occurs around the source plane centre.

The identity root follows the skill's `SIGNS.md` unyawed prop-root rule. No mob-facing yaw is applied. This is a native Blockbench 5.0 rig; its coordinates are not relabeled as legacy 4.x. Native world-transform probes establish that positive local `h_out.rotation.z`, under the 90-degree placement bone, produces clockwise motion from above: local `+120` corresponds to world vertical-axis yaw `-120` degrees. A source-plane mark at +X moves toward +Z. The retained north-face normal is world `[0,1,0]`.

## Clips

| Clip | Playback | Length | Content |
| --- | --- | --- | --- |
| `windup` | HOLD | 3.00 s / 60 ticks | Linear clockwise world yaw 0 to -120 degrees. Uniform scale 0 to 1 over ticks 0-2, then 1 through tick 60. |
| `expand` | HOLD | 0.30 s / 6 ticks | Linear clockwise world yaw -120 to -150 degrees. Uniform scale 1 to 3, with a cubic ease-out sampled on each tick. Last frame holds. |
| `hidden` | LOOP | 0.05 s / 1 tick | Both source bones have step scale `[0.001,0.001,0.001]` at both endpoints. The added rest bones remain unchanged. |

All keys are on the 0.05-second tick grid. There are no position keys. Visible keys are on `h_out`:

| Clip/channel | Time/value keys | Interpolation |
| --- | --- | --- |
| `windup.rotation` | `0: [0,0,0]`; `3.00: [0,0,120]` | Linear |
| `windup.scale` | `0: 0`; `0.10: 1`; `3.00: 1` | Linear, uniform |
| `expand.rotation` | `0: [0,0,120]`; `0.30: [0,0,150]` | Linear |
| `expand.scale` | `0: 1`; `0.05: 1.8425925926`; `0.10: 2.4074074074`; `0.15: 2.75`; `0.20: 2.9259259259`; `0.25: 2.9907407407`; `0.30: 3` | Linear between tick samples, uniform |

The expansion samples use `1 + 2 * (1 - (1 - t/0.30)^3)`: fast first, then settling. `windup(3.00)` and `expand(0)` have identical transforms and pixel-identical native renders. For a 3.20-second channel-to-quiet interval, the nominal windup playback multiplier is `3.00 / 3.20 = 0.9375`; the hook must use its actual quiet time. Do not loop the windup or crossfade away from its endpoint. Remove the prop at the expansion endpoint rather than adding a disappearance curve.

## Texture

The source-bound 128 x 128 RGBA `infernal_judgement_vfx.png` atlas is retained byte-for-byte, embedded and exported as `pyro_conflag_sigil.png` beside the model and at `src/assets/legendcraft/textures/entity/pyro_conflag_sigil.png`. Resource location: `legendcraft:entity/pyro_conflag_sigil`. Atlas SHA1: **`2c6949687283dda1b471f5b8a010e388f989ade4`**. No repaint, UV resampling, palette change, alpha change or emissive companion.

## Verification and renders

Verified unchanged source SHA256, source element coordinates and pivot, both source bone pivots and rest rotations, retained face UV, exact atlas bytes in all three locations, identity root, clip playback modes and lengths, tick alignment, hidden scales, upward face normal, rest placement and clip placement. Native authored-plane centre is `[0,0.4000000000000001,0]` within floating-point tolerance. Blockbench adds a preview-only 0.001 u thickness below a zero-thickness plane; the upward surface remains at y = 0.40 u.

The saved deliverable was reloaded into an isolated Blockbench project before rendering. Native animated meshes and materials were rendered over mid-grey ground with a 2-block-tall stand-in. The fixed top camera is `(0,190,0.001)` u looking at the origin, 55-degree vertical FOV. Geometry was not rescaled to fit the frame.

- [Top-down contact sheet](pyro_conflag_sigil_render_contact.png): 16 poses spanning the windup, both swap endpoints, and every expansion tick; visually inspected.
- [Windup-to-expand GIF](pyro_conflag_sigil_render_swap.gif): the final 20 windup ticks followed by expansion ticks 0-6, 50 ms per frame. The endpoint frame is shown for one tick; the GIF loop restarts the demonstration. There is no jump at the clip swap.

`deploy-rigs.ps1 -Prop` and `-Prop -Preflight` passed. Staged model: `dist/props/models/pyro_conflag_sigil.bbmodel`, SHA1 **`e3b84925e7dce6d4b9e9a9655e82bc39aac2ed67`**. Staged and source model bytes match. `build.ps1` and the source-tree manifest check passed: 489 item models, 17 sounds, 5 sounds.json. Plugin-contributed assets were not checked because no plugin source was supplied.

The explicit build brief authorizes the final renders, staging and commit without the skill's intermediate preview pause. This is staging only; no plugin code or live server was changed. In-game wearer anchoring, BetterModel's format-5 transform conversion, brightness, alpha sorting, retiming and removal at detonation remain hook-time checks.
