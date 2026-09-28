# Ember Shell runic wrap

`pyro_shell_wrap` is a BetterModel motion prop attached at the caster's feet for Ember Shell's full life: five seconds, or eight seconds at Level 45. Strength is chosen at cast from the caster's active Burning stacks. Play the matching form, then wrap loop; expiry plays the matching gutter. A Level 60 broken shell uses the separate item flipbook `pyro_shell_detonation` instead. No plugin code is included.

The approved Ember Shell panel 1 becomes solid, thin cube ribbons, with the shaded ember materials of the approved Scorch explosion. A ribbon makes 1.4 turns, with forty overlapping short segments. Segment centres run from y=2 to 33.2 u; their edges reach approximately y=0 to 35.2 u (2.2 blocks). Radius to the ribbon centreline is 14.4 u (0.9 blocks); each segment is 3.65 u long, 4 u wide and 1 u thick. Units are 16 per block.

## Bones

| Bone | Children / geometry | Elements |
| --- | --- | ---: |
| `root` | Identity origin and rotation; three strength groups | 0 |
| `band_low` | One ribbon; 40 segment pivot bones | 40 |
| `band_mid` | Two ribbons 180 degrees apart; 80 segment pivot bones | 80 |
| `band_high` | Three ribbons 120 degrees apart; 120 segment pivots and nine ember pivots | 129 |

Total: 249 cubes, 253 bones. Segment pivots let guttering shrink each piece at its own position as the whole band expands. Their descriptive names are `<strength>_r<ribbon>_seg_<number>`; the high embers are `high_shed_0` through `_8`. Only one strength group is shown in any visible clip.

## Clips

| Clip | Ticks | Mode | Motion |
| --- | ---: | --- | --- |
| `wrap_low` | 40 | Loop | One clockwise revolution |
| `wrap_mid` | 30 | Loop | One clockwise revolution |
| `wrap_high` | 20 | Loop | One clockwise revolution, nine orbiting embers |
| `form_low` | 8 | Hold | Low ribbon winds in and grows |
| `form_mid` | 8 | Hold | Mid ribbons wind in and grow |
| `form_high` | 8 | Hold | High ribbons and embers wind in and grow |
| `gutter_low` | 10 | Hold | Low ribbon unwinds, expands and shrinks to hidden |
| `gutter_mid` | 10 | Hold | Mid ribbons unwind, expand and shrink to hidden |
| `gutter_high` | 10 | Hold | High ribbons and embers unwind, expand and shrink to hidden |
| `hidden` | 20 | Loop | All bands held at 0.001 |

Every channel is keyed every tick and interpolates linearly. The inactive bands stay at scale 0.001 at every key, throughout every clip. Formation eases from 1.5 times centreline radius and 0.6 times height to rest, with individual pieces growing from 0.4 to 1; the radial/tangential starting piece size is consequently about 0.6 of rest. Formation unwinds an initial -100-degree yaw into the resting orientation. Guttering turns +120 degrees, expands the radius to 1.36 times rest at tick 9, and shrinks each piece continuously. At tick 10 all three band groups are hidden and held. No scale-step frame sequence is used.

`SIGNS.md`'s unyawed prop-root and prop-bone yaw entries apply: positive animation yaw spins clockwise from above. There are no position keys; segment rest orientation follows the helix tangent. Do not apply the mob root's 180-degree correction.

## Textures

Fourteen embedded 16 x 16 PNGs, also supplied as `pyro_shell_wrap_texture_*.png`: four blocky glyphs for each strength (cross, diamond, boxed square, hooked stroke), plus Scorch's yellow and orange for ember cubes. Bands carry an upper bright rim, shaded body, darker underside and deliberate small clustered marks. Alpha is binary cutout. Palette: `#FFF4E0 #FFD24A #FF8A00 #E8500F #B7331A #7A1F10 #4A423C #3B3430 #241F1B #171310`. Cyan is reserved for the detonation flash and is absent here.

## Verification

Native Blockbench Cube, Group, Texture and Animation APIs through localhost MCP authored the rig. The saved native codec output is normalized to the legacy inline outliner serialization for the pack tooling; no geometry is generated as external JSON.

Prop preview: `C:/Users/omarz/AppData/Local/Temp/bb-ember-shell/wrap_preview.html`, generated from the saved model with feet offset zero and a clip selector for all ten clips. Blockbench renders use a bystander camera at (0,25.6,96) u: 1.6 blocks high and six blocks out, looking at (0,17.6,0). Three loop GIFs contain exactly 40, 30 and 20 frames respectively at 50 ms per frame; matching stills and additional high formation/gutter GIFs are alongside the model under `pyro_shell_wrap_render_*`. All three strengths were visually inspected. Palette, alpha, inactive-band keys and every gutter ending were checked. Blockbench's evaluated terminal gutter scales are 0.001 on all three bands.

Staged with `powershell -NoProfile -ExecutionPolicy Bypass -File deploy-rigs.ps1 -Prop -Rig pyro_shell_wrap`; `deploy-rigs.ps1 -Prop -Preflight` reports DEPLOYABLE. The `-Prop` switch is required by the existing script's identity-root assertion. Stage location: `dist/props/models/pyro_shell_wrap.bbmodel`. Nothing was copied to a server.

The brief overrides the skill's explicit stop: `legendcraft-blockbench/SKILL.md` says "the commit and the handoff are all forbidden" before a later owner ruling, and `PROP-PREVIEW.md` says "Then the turn ends: the ruling is the next message". The brief authorizes the completed build, render and commit sequence in this session. It also limits reads and commits to this pack lane, overriding the skill's index/update/push workflow.

In-game checks still owed: feet attachment while moving, caster visibility, light level, clip transitions and runtime cost of the per-segment pivot bones. No in-game verification is claimed.

## History

2026-09-28: Built the approved runic shell as three strengths of a shaded cube helix with formation, spin and expiry motion.
