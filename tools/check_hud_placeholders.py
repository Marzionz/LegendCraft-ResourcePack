    "feedback_line": "reads blank at rest and is ungated; accepted debt, waiting on HUD-FEEDBACK-EMPTY",
#!/usr/bin/env python3
"""Gate: every papi:legendcraft_* token the HUD reads is one LegendCraft-Classes answers.

The HUD's elements are gated on placeholders served by the `HudPlaceholders` PlaceholderAPI
expansion. An id nothing answers resolves blank, its gating condition fails, and the element
-- often a whole row -- silently does not render. The two repos build separately, so nothing
but this check couples them.

The answerable set is read out of the expansion's OWN SOURCE, never a hand-copied list: a
copy drifts the moment somebody renames a case, and a gate reading a stale copy reports
confidently and falsely.

Placeholders used inside a `pattern:` string carry a second requirement. A text element whose
pattern resolves to nothing at rest is not merely invisible -- BetterHud drops the hud that
contains it at parse time, taking every other element with it. Those ids must appear in
PATTERN_SAFE_PLACEHOLDERS with the reason they are safe.

    python tools/check_hud_placeholders.py [--classes-root <dir>] [--hud-root <dir>]
"""

from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
DEFAULT_HUD_ROOT = os.path.join(REPO_ROOT, "hud", "betterhud")
DEFAULT_CLASSES_ROOT = os.path.join(os.path.dirname(REPO_ROOT), "LegendCraft-Classes")

EXPANSION_SOURCE = os.path.join(
    "src", "main", "java", "com", "legendcraft", "classes", "hud", "HudPlaceholders.java"
)
PROJECTION_SOURCE = os.path.join(
    "src", "main", "java", "com", "legendcraft", "classes", "hud", "HudPartyProjection.java"
)

# The expansion's own identifier: `legendcraft_<id>` is what a HUD file writes.
PLACEHOLDER_PREFIX = "legendcraft_"
# Every placeholder reference in a BetterHud file, in both the bracketed pattern form and the
# bare form conditions and bar values use.
PLACEHOLDER_REF_RX = re.compile(r"papi:" + PLACEHOLDER_PREFIX + r"([a-z0-9_]+)")
# A pattern line's whole value, so a token can be attributed to the element field it sits in.
PATTERN_LINE_RX = re.compile(r"^\s*pattern:\s*(.+)$")

# Ids the expansion answers by an exact name test rather than a switch label.
EQUALS_RX = re.compile(r"params\.equals\(\"([a-z0-9_]+)\"\)")
# `params.startsWith("slot1_")` and friends: a family, not an id.
STARTSWITH_RX = re.compile(r"params\.startsWith\(\"([a-z0-9_]+)\"\)")
# Both switch forms the expansion uses, including multi-label arrow arms.
CASE_RX = re.compile(r"^\s*case\s+(\"[a-z0-9_]+\"(?:\s*,\s*\"[a-z0-9_]+\")*)\s*(?:->|:)", re.M)
CASE_LABEL_RX = re.compile(r"\"([a-z0-9_]+)\"")
# The party-frame family's prefix constant and the slot count that bounds it.
PARTY_PREFIX_RX = re.compile(r"PARTY_MEMBER_PREFIX\s*=\s*\"([a-z0-9_]+)\"")
MEMBER_SLOTS_RX = re.compile(r"MEMBER_SLOTS\s*=\s*PartyService\.PARTY_MAX_SIZE\s*-\s*(\d+)")
# Core's party size, read where the projection's own bound reads it from.
PARTY_MAX_SIZE_RX = re.compile(r"PARTY_MAX_SIZE\s*=\s*(\d+)")

# The party roster the projection publishes is the viewer's party minus the viewer, and Core
# is a third repository this gate does not check out. Without it the bound is unknown, and an
# unknown bound is checked as a bound rather than waved through.
FALLBACK_PARTY_MAX_SIZE = 5

# Placeholders that may appear inside a `pattern:`. Two kinds, and each entry says which:
# an id the expansion guarantees a non-empty answer for, or one that reads blank and is
# recorded here as accepted debt with what it waits on.
PATTERN_SAFE_PLACEHOLDERS = {
    "health": "the vitals snapshot answers a number, or the element's own health listener hides it",
    "max_health": "same snapshot as health; never blank while health is drawn",
    "armor": "vitals snapshot, and the pattern pairs it with a literal denominator",
    "food": "vitals snapshot, and the pattern pairs it with a literal denominator",
    "level": "progression answers an integer for every player, floor included",
    "xp_current": "progression answers a long, floored at zero",
    "xp_needed": "progression answers a long, floored at zero",
    "resource_current": "the resource service answers a rounded integer for every player",
    "resource_max": "the resource service answers a rounded integer for every player",
    "party_member_1": "the row is followed, and cancel-if-follower-not-exists drops it whole",
    "party_member_2": "the row is followed, and cancel-if-follower-not-exists drops it whole",
    "party_member_3": "the row is followed, and cancel-if-follower-not-exists drops it whole",
    "party_member_4": "the row is followed, and cancel-if-follower-not-exists drops it whole",
    "slot1_cd_secs": "blank off cooldown, but the element is gated on the same cooldown it reads",
    "slot2_cd_secs": "blank off cooldown, but the element is gated on the same cooldown it reads",
    "slot3_cd_secs": "blank off cooldown, but the element is gated on the same cooldown it reads",
    "ult_cd_secs": "blank off cooldown, but the element is gated on the same cooldown it reads",
}


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def party_member_slots(classes_root: str) -> int:
    """How many party-frame rows the expansion answers, read from the projection's own bound."""
    projection = _read(os.path.join(classes_root, PROJECTION_SOURCE))
    offset_match = MEMBER_SLOTS_RX.search(projection)
    if not offset_match:
        return FALLBACK_PARTY_MAX_SIZE - 1
    size_match = PARTY_MAX_SIZE_RX.search(projection)
    party_max = int(size_match.group(1)) if size_match else FALLBACK_PARTY_MAX_SIZE
    return party_max - int(offset_match.group(1))


def answerable(classes_root: str):
    """The ids the expansion answers, as (exact ids, slot prefixes, slot fields)."""
    source = _read(os.path.join(classes_root, EXPANSION_SOURCE))
    exact = set(EQUALS_RX.findall(source))
    for labels in CASE_RX.findall(source):
        exact.update(CASE_LABEL_RX.findall(labels))
    prefixes = set(STARTSWITH_RX.findall(source))
    party_prefix_match = PARTY_PREFIX_RX.search(source)
    if party_prefix_match:
        party_prefix = party_prefix_match.group(1)
        prefixes.discard(party_prefix)
        for slot in range(1, party_member_slots(classes_root) + 1):
            exact.add("%s%d" % (party_prefix, slot))
    # A slot family's suffixes are the labels of the switch over `field`, which the same set of
    # case labels already holds -- the two switches share this source and neither name collides.
    return exact, prefixes


def is_answered(placeholder_id: str, exact, prefixes) -> bool:
    if placeholder_id in exact:
        return True
    for prefix in prefixes:
        if placeholder_id.startswith(prefix) and placeholder_id[len(prefix):] in exact:
            return True
    return False


def hud_files(hud_root: str):
    for directory, _subdirs, names in os.walk(hud_root):
        for name in sorted(names):
            if name.endswith(".yml"):
                yield os.path.join(directory, name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classes-root", default=DEFAULT_CLASSES_ROOT)
    parser.add_argument("--hud-root", default=DEFAULT_HUD_ROOT)
    args = parser.parse_args()

    expansion_path = os.path.join(args.classes_root, EXPANSION_SOURCE)
    if not os.path.isfile(expansion_path):
        print("FAIL: no expansion source at %s" % expansion_path)
        print("      the answerable set is read from that file; without it this gate proves nothing")
        return 1

    exact, prefixes = answerable(args.classes_root)
    failures = []
    seen = 0
    for path in hud_files(args.hud_root):
        display = os.path.relpath(path, REPO_ROOT)
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            pattern_match = PATTERN_LINE_RX.match(line)
            for placeholder_id in PLACEHOLDER_REF_RX.findall(line):
                seen += 1
                if not is_answered(placeholder_id, exact, prefixes):
                    failures.append("%s:%d: %s%s names no case in HudPlaceholders"
                                    % (display, lineno, PLACEHOLDER_PREFIX, placeholder_id))
                elif pattern_match and placeholder_id not in PATTERN_SAFE_PLACEHOLDERS:
                    failures.append(
                        "%s:%d: %s%s is read inside a pattern but is not on the pattern allow-list"
                        % (display, lineno, PLACEHOLDER_PREFIX, placeholder_id))

    if failures:
        print("FAIL: %d placeholder problem(s) across %d reference(s)" % (len(failures), seen))
        for failure in failures:
            print("  " + failure)
        return 1
    print("OK: %d placeholder reference(s), every id answered, every pattern id allow-listed" % seen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
