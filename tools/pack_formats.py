"""The client pack formats this pack is tested on, and how a pack.mcmeta declares a range of them.

The merge that builds the served pack and the gates over it read every bound from here, so the
tested ceiling moves in one place.
"""

# The newest client pack format this pack and the plugin packs merged into it have been
# exercised on. A client above it is served the pack without any overlay claiming its format.
TESTED_MAX_FORMAT = 88

# The key holding the range's older form: a pack's section and an overlay entry name it
# differently. Both carry the newer form as `min_format`/`max_format`.
PACK_RANGE_KEY = "supported_formats"
OVERLAY_RANGE_KEY = "formats"


def major(bound):
    """A format bound's major version: an int, or the first of a [major, minor] pair."""
    return bound[0] if isinstance(bound, list) else bound


def declared_ranges(section, range_key):
    """Every (low, high) range a pack section or overlay entry declares, one per form present.

    The older form is an int, a [low, high] list or a {min_inclusive, max_inclusive} object; a
    client reads whichever form it understands, so each is a claim of its own.
    """
    ranges = []
    if "min_format" in section or "max_format" in section:
        low = section.get("min_format", section.get("max_format"))
        high = section.get("max_format", low)
        ranges.append((major(low), major(high)))
    value = section.get(range_key)
    if isinstance(value, int):
        ranges.append((value, value))
    elif isinstance(value, list) and value:
        ranges.append((major(value[0]), major(value[-1])))
    elif isinstance(value, dict):
        ranges.append((value.get("min_inclusive"), value.get("max_inclusive")))
    return ranges


def describe(ranges):
    return ", ".join("%s-%s" % (low, high) for low, high in ranges)

# The first client pack format whose shader compiler rejects `#moj_import`. A core shader still
# importing that way fails to compile there, and the client rejects the whole pack.
MOJ_IMPORT_REJECTED_FORMAT = 97
