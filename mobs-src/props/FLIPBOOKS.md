# Flat flipbooks

The frame-stack props the plugin plays as item-model flipbooks: one item display that changes the
item model it wears on each frame's tick. `tools/gen-flipbook-frames.py` reads this table and each
rig's `.bbmodel` beside it, and writes one item model per frame under
`src/assets/legendcraft/{items,models/item,textures/item}/classes/<frames>_<n>`.

A rig named here is a preview and authoring source only. It is not deployed to BetterModel: its
frames reach the client as item models in this pack, never as a BetterModel model. These `.bbmodel`
files are the generator's inputs and are the only files tracked under `mobs-src/`.

Columns:

- **frames** — the item-model stem; frame `n` (from 1, in the order the clip shows them) is
  `<frames>_<n>`.
- **rig** — the `.bbmodel` in this folder.
- **clip** — the clip whose scale steps choose the frames.
- **shrink** — the rig is drawn at 1/shrink of its authored size so every frame fits the item
  model's three-block box; the plugin scales the display up by the same factor.
- **native** — bones whose own animation the display plays as its transform rather than the
  frames drawing it.
- **tint** — `yes` when the plugin colours the frames at spawn: every face multiplies the first
  colour of the worn item's `custom_model_data`, and draws as painted without one. `void` when the
  frames carry a void window: the item is tinted with the void mark (`tools/void_marker.py`), the
  one tint under which the item shader draws the void on the texels painted at a void-band alpha.

| frames | rig | clip | shrink | native | tint |
| --- | --- | --- | --- | --- | --- |
| `knight_vanguard_flash` | `knight_vanguard_flash` | `flash` | 4 | | |
| `seraph_ascension_column` | `seraph_ascension_column` | `flash` | 4 | | |
| `knight_vanguard_burst` | `knight_vanguard_burst` | `burst` | 4 | | |
| `knight_warcry_ring` | `knight_warcry_ring` | `burst` | 1 | | |
| `priest_spirit_ripple` | `priest_spirit_ripple` | `burst` | 1 | | |
| `thf_blink_flash` | `thf_blink_flash` | `flash` | 2 | `flash` | yes |
| `pyro_shell_detonation` | `pyro_shell_detonation` | `detonate` | 4 | | |
| `pyro_surge_pillar_low` | `pyro_surge_burst` | `pillar_low` | 4 | | |
| `pyro_surge_pillar_mid` | `pyro_surge_burst` | `pillar_mid` | 4 | | |
| `pyro_surge_pillar_full` | `pyro_surge_burst` | `pillar_high` | 4 | | |
| `pyro_surge_ring_low` | `pyro_surge_ring` | `ring_low` | 2 | | |
| `pyro_surge_ring_mid` | `pyro_surge_ring` | `ring_mid` | 2 | | |
| `pyro_surge_ring_high` | `pyro_surge_ring` | `ring_high` | 2 | | |
| `pyro_conflag_stream` | `pyro_conflag_stream` | `flow` | 1 | | |
| `pyro_conflag_cashout` | `pyro_conflag_cashout` | `snap` | 1 | | |
| `pyro_conflag_explosion` | `pyro_conflag_explosion` | `detonate` | 4 | | |
| `pyro_conflag_field` | `pyro_conflag_field` | `blast` | 2 | | |
| `pyro_conflag_rim` | `pyro_conflag_rim` | `fuse` | 2 | | |
| `pyro_scorch_explosion` | `pyro_scorch_explosion` | `burst` | 2 | | |
| `knight_ghost_shield` | `knight_ghost_shield` | `flare` | 1 | | |
| `knight_horn_blast` | `knight_horn_blast` | `war_cry` | 1 | | |
| `smc_shadowstep_portal_open` | `smc_shadowstep_portal` | `open` | 2 | | `void` |
| `smc_shadowstep_portal_hold` | `smc_shadowstep_portal` | `hold` | 2 | | `void` |
| `smc_shadowstep_portal_swallow` | `smc_shadowstep_portal` | `swallow` | 2 | | `void` |
| `smc_shadowstep_portal_close` | `smc_shadowstep_portal` | `close` | 2 | | `void` |
| `smc_nightfall_circle` | `smc_nightfall_break` | `appear` | 1 | | |
| `smc_void_bolt_cloud_implode` | `smc_void_bolt_cloud` | `implode` | 1 | `cloud` | |
| `smc_void_bolt_cloud_burst` | `smc_void_bolt_cloud` | `burst` | 1 | `cloud` | |
| `smc_void_bolt_implode` | `smc_void_bolt_implode` | `implode` | 1 | | |
| `nin_thousand_cuts` | `nin_thousand_cuts` | `cut` | 1 | | |

The three `pyro_surge_ring` band rows are the source for the ranked ring flipbooks `surge_ring_ranks.py` writes; re-run it after regenerating them ([`pyro_surge_ring.md`](pyro_surge_ring.md#ranks-stand-and-burn-away)).
