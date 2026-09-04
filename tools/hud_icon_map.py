"""HUD icon linking map — data only, edited as per-class icons get finished.

`generate_hud.py` reads this to draw each class's real 32x32 ability art in the skill-casting
HUD (over the neutral placeholder gem). It is deliberately a SEPARATE file so an icon/linking
agent touches only this data, never the HUD-wiring logic in generate_hud.py (which avoids the
edit collisions we hit while both were in one file).

HOW TO LINK A CLASS (for a linking agent):
  1. Confirm the class's finished icon PNGs live in hud/skill-icons/<classid>/<name>.png,
     authored at 32x32 (ICON_ART).
  2. Add ONE entry below: "<classid>": [<slot1>, <slot2>, <slot3>(, <ult>)] — the icon file
     stems in the SAME ORDER as the class's GameClass.skills() (+ the ultimate last for a
     subclass). Use None for any slot whose icon isn't drawn yet (it shows the placeholder gem).
     `classid` is the value the `legendcraft_subclass` placeholder returns (e.g. "archer",
     "hunter"); the folder under skill-icons/ must match it.
  3. Base classes have 3 entries, subclasses 4 (3 core + ult).
  4. Run `python generate_hud.py` and redeploy — that's the whole link.

Do NOT add cooldown/starved variants here — the HUD's radial shroud + out-of-mana wash handle
those states over the single ready icon.
"""

CLASS_SKILL_ICONS = {
    # base classes (3 slots, slot order = GameClass.skills())
    "archer": ["pin_shot", "rapid_fire", "grapple"],
    "warrior": ["power_strike", "charge", "grab"],   # complete base 3
    "mage": ["fireball", "arcane_ward", "frost_bolt"],   # complete base 3
    "warlock": ["raise_thrall", "shadow_bolt", "mark_of_misery"],   # complete base 3
    "priest": ["holy_mend", "concoction", "spirit_burst"],   # complete base 3
    "thief": ["ambush", "flurry", "roll"],   # complete base 3

    # subclasses (4 slots: 3 core skills + ultimate last)
    "hunter": ["ensnaring_trap", "venomous_arrow", "beast_companion", "pack_ambush"],   # complete 3+1
    "sniper": ["heartseeker", "bolt", "evasive_shot", "arrow_blitz"],   # complete 3+1
    "pyromancer": ["scorch", "flame_surge", "ember_shell", "conflagration"],   # complete 3+1
    "knight": ["bulwark", "shield_bash", "war_cry", "vanguard"],   # complete 3+1
    "ranger": ["hamstring", "quickstep", "point_blank_shot", "kiting_dance"],   # complete 3+1
    "cryomancer": ["ice_lance", "permafrost", "frost_nova", "absolute_zero"],   # complete 3+1
    "berserker": ["savage_cleave", "blood_rush", "reavers_throw", "undying_rage"],   # complete 3+1
    "necromancer": ["raise_ghoul", "soul_harvest", "defile", "bone_colossus"],   # complete 3+1
    "shadowmancer": ["shadowstep", "maw_of_shadow", "void_bolt", "nightfall"],   # complete 3+1
    "doomsayer": ["curse_of_ruin", "word_of_dread", "contagion", "foretold_doom"],   # complete 3+1
    "bloodweaver": ["crimson_bolt", "hemorrhage", "sanguine_barrier", "exsanguinate"],   # complete 3+1
    "brawler": ["haymaker", "relentless_pursuit", "iron_grip", "flurry"],   # complete 3+1
    "seraph": ["radiant_touch", "divine_wrath", "luminous_bond", "ascension"],   # complete 3+1
    "assassin": ["cloak", "killing_blow", "stalk", "marked_for_death"],   # complete 3+1
    "alchemist": ["caustic_flask", "stimulant", "volatile_concoction", "grand_elixir"],   # Priest subclass — complete 3+1
    "rogue": ["grit", "sidestep", "riposte", "cornered"],   # complete 3+1
    "shaman": ["earthen_strike", "soul_infusion", "voltaic_lash", "ancestral_wrath"],   # Priest subclass — complete 3+1
    "ninja": ["blur", "smoke_bomb", "shuriken_volley", "thousand_cuts"],   # Thief subclass — complete 3+1
}
