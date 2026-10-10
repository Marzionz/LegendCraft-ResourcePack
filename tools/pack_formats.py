"""The client pack formats this pack is tested on, and how a pack.mcmeta declares a range of them.

The merge that builds the served pack and the gates over it read every bound from here, so the
tested ceiling moves in one place.
"""

# The newest client pack format this pack and the plugin packs merged into it have been
# exercised on. A client above it is served the pack without any overlay claiming its format.
TESTED_MAX_FORMAT = 97

# The key holding the range's older form: a pack's section and an overlay entry name it
# differently. Both carry the newer form as `min_format`/`max_format`.
PACK_RANGE_KEY = "supported_formats"
OVERLAY_RANGE_KEY = "formats"


def major(bound):
    """A format bound's major version: an int, or the first of a [major, minor] pair."""
    return bound[0] if isinstance(bound, list) else bound


# A bare major as an upper bound admits every minor of that major; as a lower bound, from its
# first.
ANY_MINOR = float("inf")


def version(bound, bare_minor):
    """A bound as a (major, minor) pair, ordered as the client orders formats; None if the bound
    is not a format."""
    if isinstance(bound, bool):
        return None
    if isinstance(bound, int):
        return (bound, bare_minor)
    if (isinstance(bound, list) and 1 <= len(bound) <= 2
            and all(isinstance(part, int) and not isinstance(part, bool) for part in bound)):
        return (bound[0], bound[1] if len(bound) == 2 else bare_minor)
    return None


def declared_ranges(section, range_key):
    """Every (low, high) range a pack section or overlay entry declares, one per form present,
    each bound a (major, minor) pair from `version`.

    The older form is an int, a [low, high] list or a {min_inclusive, max_inclusive} object of
    majors; a client reads whichever form it understands, so each is a claim of its own.
    """
    ranges = []
    if "min_format" in section or "max_format" in section:
        low = section.get("min_format", section.get("max_format"))
        high = section.get("max_format", low)
        ranges.append((version(low, 0), version(high, ANY_MINOR)))
    value = section.get(range_key)
    if isinstance(value, list) and value:
        value = {"min_inclusive": value[0], "max_inclusive": value[-1]}
    elif not isinstance(value, dict) and value is not None:
        value = {"min_inclusive": value, "max_inclusive": value}
    if isinstance(value, dict):
        ranges.append((version(value.get("min_inclusive"), 0),
                       version(value.get("max_inclusive"), ANY_MINOR)))
    return ranges


def version_text(bound):
    if bound is None:
        return "?"
    if bound[1] in (0, ANY_MINOR):
        return str(bound[0])
    return "%d.%d" % bound


def describe(ranges):
    """The ranges as `low-high`, each written once however many forms declare it."""
    return ", ".join("%s-%s" % (version_text(low), version_text(high))
                     for low, high in dict.fromkeys(ranges))

# The first client pack format whose shader compiler rejects `#moj_import`. A core shader still
# importing that way fails to compile there, and the client rejects the whole pack.
MOJ_IMPORT_REJECTED_FORMAT = 97
