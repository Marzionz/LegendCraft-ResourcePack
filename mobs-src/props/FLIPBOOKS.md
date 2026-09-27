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
  colour of the worn item's `custom_model_data`, and draws as painted without one.

| frames | rig | clip | shrink | native | tint |
| --- | --- | --- | --- | --- | --- |
| `knight_vanguard_burst` | `knight_vanguard_burst` | `burst` | 4 | | |
| `knight_warcry_ring` | `knight_warcry_ring` | `burst` | 1 | | |
| `priest_spirit_ripple` | `priest_spirit_ripple` | `burst` | 1 | | |
| `seraph_smite_mark` | `seraph_smite_mark` | `smite` | 2 | | |
| `seraph_wrath_bolt` | `seraph_wrath_bolt` | `bolt` | 4 | | |
| `seraph_wrath_detonation` | `seraph_wrath_detonation` | `detonate` | 2 | | |
| `seraph_ascension_finale` | `seraph_ascension_finale` | `finale` | 4 | | |
| `thf_blink_flash` | `thf_blink_flash` | `flash` | 2 | `flash` | yes |
| `pyro_shell_detonation` | `pyro_shell_detonation` | `detonate` | 4 | | |
| `pyro_surge_burst_low` | `pyro_surge_burst` | `burst_low` | 4 | | |
| `pyro_surge_burst_mid` | `pyro_surge_burst` | `burst_mid` | 4 | | |
| `pyro_surge_burst_high` | `pyro_surge_burst` | `burst_high` | 4 | | |
| `pyro_conflag_stream` | `pyro_conflag_stream` | `flow` | 1 | | |
| `pyro_conflag_cashout` | `pyro_conflag_cashout` | `snap` | 1 | | |
| `pyro_conflag_explosion` | `pyro_conflag_explosion` | `detonate` | 4 | | |
