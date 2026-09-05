#!/usr/bin/env python3
"""Gate: every papi:legendcraft_* token the HUD reads is one LegendCraft-Classes answers.

The HUD's elements are gated on placeholders served by the `HudPlaceholders` PlaceholderAPI
expansion. An id nothing answers resolves blank, its gating condition fails, and the element
-- often a whole row -- silently does not render. The two repos build separately, so nothing
but this check couples them.

The answerable set is read out of the expansion's OWN SOURCE, never a hand-copied list: a
copy drifts the moment somebody renames a case, and a gate reading a stale copy reports
confidently and falsely.

An id that answers "" is not a failure here: a pattern whose only placeholder resolves to
nothing still loads, and so does the hud around it. What a pattern's TEXT has to obey is the
text parser's slash rule, gated by `tools/check_hud_yaml.py`.

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

# Ids the expansion answers by an exact name test rather than a switch label.
EQUALS_RX = re.compile(r"params\.equals\(\"([a-z0-9_]+)\"\)")
# `params.startsWith("slot1_")` and friends: a family, not an id.
STARTSWITH_RX = re.compile(r"params\.startsWith\(\"([a-z0-9_]+)\"\)")
# Both switch forms the expansion uses, including multi-label arrow arms.
CASE_RX = re.compile(r"^\s*case\s+(\"[a-z0-9_]+\"(?:\s*,\s*\"[a-z0-9_]+\")*)\s*(?:->|:)", re.M)
CASE_LABEL_RX = re.compile(r"\"([a-z0-9_]+)\"")
# The method that projects ONE slot's field. Its switches are over `field`, not over the whole
# id, so their labels are suffixes and never ids in their own right. The two label sets have to
# stay apart: unioned, every stat id passes as a slot field and every field label passes as a
# bare id, and the expansion answers null to both.
SLOT_FIELD_METHOD_RX = re.compile(r"\n    private String slotField\(.*?\n    \}\n", re.S)
# The party-frame family's prefix constant and the slot count that bounds it.
PARTY_PREFIX_RX = re.compile(r"PARTY_MEMBER_PREFIX\s*=\s*\"([a-z0-9_]+)\"")
MEMBER_SLOTS_RX = re.compile(r"MEMBER_SLOTS\s*=\s*PartyService\.PARTY_MAX_SIZE\s*-\s*(\d+)")
# Core's party size, read where the projection's own bound reads it from.
PARTY_MAX_SIZE_RX = re.compile(r"PARTY_MAX_SIZE\s*=\s*(\d+)")

# The party roster the projection publishes is the viewer's party minus the viewer, and Core
# is a third repository this gate does not check out. Without it the bound is unknown, and an
# unknown bound is checked as a bound rather than waved through.
FALLBACK_PARTY_MAX_SIZE = 5

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


def case_labels(source: str):
    labels = set()
    for group in CASE_RX.findall(source):
        labels.update(CASE_LABEL_RX.findall(group))
    return labels


def answerable(classes_root: str):
    """What the expansion answers, as (bare ids, slot prefixes, slot field labels).

    Three sets, kept apart on purpose. A bare id is answered only by the switches over the whole
    parameter; a slot field label only after one of the slot prefixes. Merging them accepts
    `slot1_armor` and a bare `cd_secs`, and the expansion answers null to both -- which leaves
    the raw token in the string and the element's condition never matching.
    """
    source = _read(os.path.join(classes_root, EXPANSION_SOURCE))

    slot_field_body = SLOT_FIELD_METHOD_RX.search(source)
    if not slot_field_body:
        raise SystemExit("could not find slotField in %s: the field labels cannot be read, and "
                         "guessing them is what this gate exists to avoid" % EXPANSION_SOURCE)
    fields = case_labels(slot_field_body.group(0))

    # Everything outside slotField answers a whole parameter name.
    outside = source.replace(slot_field_body.group(0), "\n")
    bare = set(EQUALS_RX.findall(outside)) | case_labels(outside)

    prefixes = set(STARTSWITH_RX.findall(source))
    party_prefix_match = PARTY_PREFIX_RX.search(source)
    if party_prefix_match:
        party_prefix = party_prefix_match.group(1)
        prefixes.discard(party_prefix)
        for slot in range(1, party_member_slots(classes_root) + 1):
            bare.add("%s%d" % (party_prefix, slot))
    return bare, prefixes, fields


def is_answered(placeholder_id: str, bare, prefixes, fields) -> bool:
    for prefix in prefixes:
        if placeholder_id.startswith(prefix):
            return placeholder_id[len(prefix):] in fields
    return placeholder_id in bare


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

    bare, prefixes, fields = answerable(args.classes_root)
    failures = []
    seen = 0
    for path in hud_files(args.hud_root):
        display = os.path.relpath(path, REPO_ROOT)
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            for placeholder_id in PLACEHOLDER_REF_RX.findall(line):
                seen += 1
                if not is_answered(placeholder_id, bare, prefixes, fields):
                    failures.append("%s:%d: %s%s names no case in HudPlaceholders"
                                    % (display, lineno, PLACEHOLDER_PREFIX, placeholder_id))

    if failures:
        print("FAIL: %d placeholder problem(s) across %d reference(s)" % (len(failures), seen))
        for failure in failures:
            print("  " + failure)
        return 1
    print("OK: %d placeholder reference(s), every id answered" % seen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
