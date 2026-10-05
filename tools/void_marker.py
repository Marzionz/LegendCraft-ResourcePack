"""The tint that marks an item as a void window for the item shader.

The shader draws the void only on an item tinted with this colour, and only on its texels whose
alpha sits in a void band (250-254 full, 240-244 faint). The alpha alone is not enough: soft glow
art elsewhere in the pack is painted at those alphas, and an untinted item can never carry the mark.

Green and blue are the mark. Red is free: the shader reads it as the window's fade, and tints the
item's ordinary texels grey by it, so a marked item at full red draws exactly as painted.
"""

VOID_MARK_GREEN = 1
VOID_MARK_BLUE = 254


def void_tint(fade=255):
    """The marker tint at red fade (0-255): 255 is the window fully drawn."""
    return (fade << 16) | (VOID_MARK_GREEN << 8) | VOID_MARK_BLUE


def void_item(model_ref, fade=255):
    """An item definition drawing model_ref, marked as a void window."""
    return {"model": {"type": "minecraft:model", "model": model_ref,
                      "tints": [{"type": "minecraft:constant", "value": void_tint(fade)}]}}
