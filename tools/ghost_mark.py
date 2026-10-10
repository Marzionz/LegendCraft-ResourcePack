"""The alpha code a ghost limb rig's tint colours carry, as the item shader reads it.

LegendCraft-Core's `GhostAlpha` writes it: a coded colour keeps the top four bits of each channel,
red's low nibble is MARK_RED and blue's is MARK_BLUE, and green's low nibble is a level from 1 to
LEVELS - 1. The item shader draws a face whose tint carries the mark at level / LEVELS alpha.
These values are the contract between Core and the shader; neither side may change one alone.
"""

MARK_RED = 0xA
MARK_BLUE = 0x5
LEVELS = 16


def is_ghost_coded(rgb):
    """Whether the tint rgb (0xRRGGBB) carries the ghost mark the item shader acts on."""
    return False
