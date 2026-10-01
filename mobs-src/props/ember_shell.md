# Ember Shell ribbon egg

Ember Shell stands a ribbon egg around the caster for the shell's life. Its ribbon count and heat tier follow how full the shield pool is between its floor (15) and its level's cap. It forms in over ten ticks, turns while the shell holds, and unravels when the shell lapses. The Level 60 break keeps its own rig, `pyro_shell_detonation`. The egg replaces the earlier `pyro_shell_wrap` rig on the plugin side.

The egg is item models worn on a BetterModel seat rig, `ember_shell_egg_seat`, attached to the caster. The rig's one bone, `egg`, swaps the item model it wears per tick (FLIPBOOK-STEP), then settles on the finished egg while the rig turns. The rig follows the caster as packets, so nothing rides the caster for real.

Source delivery: `C:\Repositories\Assets\pyro-surge-shell\ember-shell\`. Editor sources copied here unchanged: `ember_shell_egg_{1,2,3}.bbmodel` (one per ribbon count), `ember_shell_egg_3_anim.bbmodel` (clips `form_a`, `spin`, `form_b`; `form_b` does not ship), `ember_shell_egg_model.js` (the geometry generator, delivered as `egg-model.js`) and `ember_shell_tip_paths.json` (the form-in tip paths, delivered as `tip_paths.json`).

## Shape

A smooth asymmetric egg of revolution, fullest below the middle, with narrow open ends, wound by one to three glyph-banded ribbons with torn ends and flame tongues. Every element is rotated on all three axes, the item-model format feature from snapshot 25w46a.

| Ribbons | Finished elements | Form states 00..10 elements |
| ---: | ---: | --- |
| 1 | 24 | 0, 1, 2, 3, 5, 8, 12, 17, 20, 24, 24 |
| 2 | 48 | 0, 2, 4, 6, 10, 16, 24, 34, 40, 48, 48 |
| 3 | 72 | 0, 3, 6, 9, 15, 24, 36, 51, 60, 72, 72 |

The form states follow `reveal_segments` in the tip paths: each state reveals the ribbon up to its tip, and state 10 is the whole ribbon.

## Texture

Five atlases, one per heat tier, shared by the finished and form models: `textures/item/classes/ember_shell_egg_tier_<t>.png`. The delivery paints them at 512 × 1024, about 100 texels per block; they ship pixelated to 176 × 352, about 35 texels per block, cut to 20 colours each with no dithering (see Shipping). Inner faces carry at most 26% alpha. Heat ramp by tier: deep red, red-orange, orange, gold, white-hot; the glyphs run one tier hotter, and past white-hot they are the kit's cyan.

## Mapping

`frac = (absorb − 15) / (cap − 15)`, clamped to [0, 1].

- Ribbons: 1 when frac < ⅓, 2 when frac < ⅔, else 3.
- Heat tier: `1 + round(4·frac)`.
- Size: the models are drawn at the Level 45+ size; below Level 45 the display is scaled by 0.773.

## Shipping

`ember_shell_ship.py` writes the shipping files from the delivery's `shipping/` folder:

    python mobs-src/props/ember_shell_ship.py C:/Repositories/Assets/pyro-surge-shell/ember-shell/shipping

It writes 15 finished models `ember_shell_egg_<r>_tier_<t>`, 165 form models `ember_shell_form_<r>_tier_<t>_<nn>` (r 1..3, t 1..5, nn 00..10), their item definitions under `items/classes/`, and the five atlases. Each atlas is drawn at 176 × 352, about a third of its size, with both sides multiples of 16 so it never caps the client's mipmapping: every cell takes the median alpha of the texels it covers and the mean colour of its drawn ones, then the atlas is cut to 20 colours with no dithering, so the delivered gradients fall into hard steps at block scale.

The delivered models are authored with the caster's feet at the origin and reach x −25..+24, y 0.5..39.6 u. The 26.1.2 client refuses an element outside the item model's [−16, 32] box ("specifier exceeds the allowed boundaries"), so the script draws every `from`, `to` and rotation `origin` at half size, moved by +8: `p' = p / 2 + 8`. Rotation angles, UVs and faces are unchanged; a model still outside the box is refused. The largest, `ember_shell_egg_3_tier_5`, lands at [−4.08, 8.47, −2.09]..[19.64, 27.61, 17.40]. The plugin scales the seat rig to twice the egg's size to restore it, with the feet at the bone's origin.

## Seat rig

`ember_shell_egg_seat.bbmodel`: one bone, `egg`, pivot at the origin, holding one 1 × 1 × 1 u cube at the origin with a fully transparent 16 × 16 texture. The cube exists only so the bone has a display; the plugin puts the egg's item models on that display at unit item scale, so the rig's scale is the egg's size. No clips. A rig built from the egg's own cubes would not do: BetterModel gives every cube rotated off a single axis its own display, up to 72 for the finished 3-ribbon egg, where the worn item model is one.

## Hook contract

The seat rig attached to the caster at twice the egg's size (0.773 of that below Level 45), brightness 15/15, visible to everyone including the caster. Its bone wears the models below; the egg turns through the rig's root yaw.

| Tick | Model | Turn | Particles |
| ---: | --- | --- | --- |
| 0 (cast) | form 00 | 0 | none |
| 1..10 | form 01..10, one a tick | one spin step a tick | tips |
| 11 | finished egg | spin | edges |
| 12.. (hold) | finished egg | spin | edges |
| expiry, then 10 ticks | form 10 down to 00, one a tick | spin | tips |
| expiry + 11 | removed | | |

- Spin: one step a tick, interpolated over the tick, at `0.25 + 0.8·frac` revolutions a second.
- Tips: every tick of the form-in and the unravel, at each ribbon tip of the current state from `ember_shell_tip_paths.json` (`counts`, blocks, feet at origin), turned with the egg: 2 END_ROD and 3 FLAME (SOUL_FIRE_FLAME at tier 5), spread (.045, .035, .045), speed .01.
- Edges, about 3 a tick, at points along the ribbons' tip paths, turned with the egg: 2 DUST in the tier colour (`#B72A10` `#E84408` `#FF7808` `#FFB030` `#9FE8FF`) sized 0.65 at tier 1 up to 1.2 at tier 5; SMALL_FLAME 3 ticks in 4; LAVA 1 tick in 4. Tier 5 swaps SOUL_FIRE_FLAME for SMALL_FLAME and END_ROD for LAVA.
- A shell broken at Level 60 drops the egg on the same tick the detonation lays.

## Verification

Generated shipping files were checked against the box bound by the script. Blockbench and preview renders are the artist's (`egg_form_a_tier4.gif`, `egg_form_a_tier5.gif`, `cmp_egg.png` in the delivery). The in-game checks are a human's: the multi-axis element rotation loading on the 26.1.2 client, and the ≤26% alpha inner faces rendering translucent on an item display.
