# Knight Horn Blast

Four-horn War Cry animation, authored on `knight-horn-blast` from origin/main
`347f2fa`. Owner approved the compact X formation, rise and announce, then
specified transparency fading in the raised pose with no lowering. Concept:
`knight_horn_blast_concept_v2.png`. Build authorized in chat on 2026-09-25.

## Asset and placement

`knight_horn_blast.bbmodel` is a Generic Model with one `war_cry` clip.
The original `knight_horn.bbmodel` and runtime held-item files are unchanged.
Four exact copies of its 379-cube geometry and painted RGB materials form this
effect. The 256x64 embedded texture and adjacent PNG contain four 64x64 atlas
columns: solid, 65%, 35%, and 12% alpha. Each horn has four mutually exclusive
geometry stages: 6,064 stored cubes total, 1,516 full-size cubes visible at a time.
The final tick hides every stage. This is a staged transparency fade, not a
continuous opacity curve or a downward recovery animation.

Root is unyawed at the player's feet. Sixteen units equal one block. Yaw parents
at 45, 135, 225, 315 degrees form the X in plan view. Their mouthpiece pivots start
at radius 9 units and y=22 (1.375 blocks). Each horn runs radially outward along
its local -Z, with its narrow mouthpiece inward and its existing curved bell
outward. The horns retain their original approximate 0.65-block length.

At the announcing pose the mouthpieces are y=24 (1.5 blocks), with X/Z positions
`(+/-6.363961, +/-6.363961)`. Bells lift by 22 degrees about the mouthpieces.
The preview mannequin is only a scale reference and is not exported in the rig.
No hands, player animation, or armor are included.

## Clip timing

`war_cry`: 30 ticks / 1.50 seconds, hold last frame. Keys are baked on the 20 Hz
grid. Every horn receives the same curve. Rotation/translation use a sampled
smoothstep rise; stage visibility uses step interpolation.

| Ticks | Seconds | Beat |
|---|---|---|
| 0 | 0.00 | All stages hidden |
| 1-8 | 0.05-0.40 | Appear, lift 2 units and tip bells up 22 degrees |
| 8-18 | 0.40-0.90 | Announce, hold the raised transform |
| 19-22 | 0.95-1.10 | 65% texture alpha, same raised transform |
| 23-25 | 1.15-1.25 | 35% texture alpha, same raised transform |
| 26-29 | 1.30-1.45 | 12% texture alpha, same raised transform |
| 30 | 1.50 | All stages hidden; hold hidden until removal |

Only stage visibility changes after tick 8. Hidden layers use scale 0.001;
visible layers use scale 1. No two full-size stages overlap on any tick.
The leather loop remains rigid with the source horn and does not droop or settle
during the freeze-and-fade beat.

## Future hook contract

Spawn this single four-horn rig at the caster's feet, oriented to caster body yaw,
and play `war_cry` once. Translation and bell pitch are authored in the clip;
the hook must not add the rise a second time. If following a moving player, move
the root with the player while preserving the local X formation.

Intended announcement cue is tick 8 / 0.40 seconds. The azure/gold rally pulse,
silver glint and horn sound from the approved concept remain external effects;
they are not geometry or keyframes in this horn-only asset. No gameplay, buff
timing, plugin code, pack registration, or deployment was changed.

## Verification

Blockbench pass completed after the owner's motion approval and final
"keep it as is" ruling. The approved model bytes were not changed during this pass.

The approved rig is loaded in Blockbench as `knight_horn_blast`, with
`war_cry` selected at the raised pose. Paired sign probes were rendered and
inspected before authoring; see `../SIGNS.md` and
`knight_horn_blast_sign_probes.png`. Probe clips are absent from the deliverable.
The independent live Blockbench check inspected all 31 ticks: exactly four
full-size stages on ticks 1-29, none on ticks 0/30, and bit-identical world pivot
positions/quaternions from tick 8 through 30. The 744 saved keyframes are all
tick-aligned. See `knight_horn_blast_verification.json`.

`knight_horn_blast_preview.html` reads the real model geometry and keys. It includes
player scale, orbit/zoom, playback, scrubbing, beat buttons, and alpha-stage
turnaround controls. The preview applies the probed 4.10 import rotation signs and
ZYX order; alpha compositing remains an approximation of Blockbench/client rendering.
The announce and fade views were visually inspected in the browser.

Final Blockbench captures were rendered and inspected: `knight_horn_blast_rise.png`
at 0.10 seconds, `knight_horn_blast_announce.png` at 0.50 seconds, and
`knight_horn_blast_fade.png` at 1.20 seconds. The close camera is `[10,34,38]`,
targeting `[0,24,0]`. `knight_horn_blast_preview.gif` samples all 31 ticks;
GIF compression merges identical frames into 20 encoded frames and preserves
their durations (1,550 ms including the final 50 ms hidden sample).
`knight_horn_blast_sheet.png` lays out those 20 encoded frames; its labels are
frame indices, not tick numbers. The renders confirm the raised pose remains fixed
as the horn becomes translucent; internal cube surfaces show through during fade.

Model SHA-256: `ca61c7c34b3f27b6b1ab0a431556352b5f64bba2512889375c8b86a5b963f129`.

Client checks still owed: translucent cube sorting/self-overlap, visibility at
16-24 blocks, player-relative follow behavior, and timing against the actual horn
audio. This authoring source is ignored by the parent pack repo's `mobs-src/` rule;
this slice is staged by explicit path, including only its authoring assets and docs.

## History

- 2026-09-25: Owner selected four outward-facing horns in an X, with rising bells.
- 2026-09-25: Owner revised the ending to a stationary transparency fade and
  approved concept v2; subsequently authorized Blockbench animation authoring.
- 2026-09-25: Created this first 1.5-second motion candidate, sign ledger,
  live-transform verification and review preview. No commit or deployment.
- 2026-09-25: Owner approved the live motion ("looks good"), then ruled
  "keep it as is" after discussing rhythmic scaling. Kept the rig unchanged;
  completed and inspected the final Blockbench GIF, contact sheet and three
  close beat renders. No scale pulsing or extra glint was added. No deployment.
