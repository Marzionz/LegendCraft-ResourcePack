# Model authoring entries in this worktree

| Model | Lane | Elements | Clips | Contract |
| --- | --- | ---: | --- | --- |
| `pyro_conflag_charge` | BetterModel motion prop | 24 | `charge` (1.60 s loop), `hidden` | [Conflagration flame-charge swirl](props/pyro_conflag_charge.md) |
| `pyro_conflag_sigil` | BetterModel motion prop | 1 | `windup` (3.00 s hold), `expand` (0.30 s hold), `hidden` | [Conflagration caster sigil](props/pyro_conflag_sigil.md) |
| `pyro_conflag_debris` | BetterModel motion prop | 66 | `erupt` (1.00 s hold), `sink` (0.60 s hold), `hidden` | [Conflagration eruption debris](props/pyro_conflag_debris.md) |
| `pyro_conflag_explosion` | Item-model flipbook prop | 555 (max 48/frame) | `detonate` (0.80 s, ends hidden), `hidden` | [Conflagration rolling block detonation](props/pyro_conflag_explosion.md) |
| `pyro_conflag_rim` | Item-model flipbook prop | 24 (1/frame) | `fuse` (1.20 s, ends hidden), `hidden` | [Conflagration channel rim using the owner's concept frames](props/pyro_conflag_rim.md) |
| `pyro_conflag_runes` | BetterModel motion prop | 144 | `spin` (4.00 s loop), `hidden` | [Conflagration rings with crossed rune glyphs](props/pyro_conflag_runes.md) |
| `pyro_conflag_field` | Item-model flipbook prop | 16 (1/frame) | `blast` (0.80 s, ends hidden), `hidden` | [Conflagration scorched field using the owner's concept frames](props/pyro_conflag_field.md) |
| `pyro_surge_ring_{red,orange,white,blue}` | Item-model flipbook prop, written by `props/surge_ring_ranks.py` (durable) | 1/frame | 9 lit frames, 10 burn-away frames | [Flame Surge ground rune ring](props/pyro_surge_ring.md#ranks-stand-and-burn-away) |
| `pyro_surge_pool_{red,orange,white,blue}` | Item-model flipbook prop, written by `props/surge_pool_ranks.py` (durable) | 1/frame | 12 cooling frames, 10 burn-away frames | [Flame Surge L45 magma pool](props/pyro_surge_pool.md) |
| `surge_flame_{red,orange,white,blue}` | BetterModel motion prop | 41 each | `erupt` (3.05 s hold) | [Flame Surge ranked flame out of the volcano's throat](props/surge_flame.md) |
| `ember_shell_egg_{1,2,3}` | Item-model prop, form flipbook then turned | 24 / 48 / 72 | form-in 11 states (10 ticks), unravel in reverse | [Ember Shell ribbon egg](props/ember_shell.md) |
