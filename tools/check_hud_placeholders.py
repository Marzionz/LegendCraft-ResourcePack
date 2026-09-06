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

`legendcraft_*` is not the only provider the HUD reads, and an id it does not answer fails
exactly the same way. So the rule is that EVERY operand names a provider and this gate says
which one:

  papi:legendcraft_*   LegendCraft-Classes, read out of the expansion's own source below.
  papi:<anything else> another PlaceholderAPI expansion. Refused unless FOREIGN_PAPI_EXPANSIONS
                       declares it, because an expansion nobody installed answers null and
                       leaves the raw token in the string.
  a bare operand       BetterHud's own built-in, checked against the sets below.
  a literal            `true`, `0`, a quoted `'mana'`. Names no provider and is not graded as
                       one -- without that exemption a gate demanding a provider for every
                       operand would refuse the whole shipped tree.

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
# Every `papi:` token, whatever expansion it names -- not just LegendCraft's.
ANY_PAPI_REF_RX = re.compile(r"papi:([a-z0-9_]+)")
# A condition's two operands, and a listener's class. Three grammar positions, three sets.
OPERAND_LINE_RX = re.compile(r"^\s*(?:first|second):\s*(.+?)\s*$")
LISTENER_CLASS_LINE_RX = re.compile(r"^\s*class:\s*(.+?)\s*$")

# --- BetterHud's own vocabulary ------------------------------------------------------------
# PINNED, not read live: BetterHud ships as a jar, no checkout of it exists in CI, and the
# alternative to a pinned list is no check at all. These names were read out of the installed
# jar's constant pools -- the placeholder categories from BukkitStandardModule's getNumbers /
# getBooleans / getStrings (plus BukkitEntityModule and BukkitItemModule for the last three
# strings), the listener classes from the same module's getListeners plus `placeholder` from
# ListenerManagerImpl. On a version bump, RE-DERIVE from the new jar rather than assuming this
# still holds; the build id is printed on every run so a stale pin is visible in the CI log.
BETTERHUD_BUILD = "2.1.0-SNAPSHOT-447"

# One set per grammar position. A union would accept `class: max_air` and `first: exp`, both of
# which BetterHud answers null to -- the same silent blank element this gate exists to refuse.
BETTERHUD_NUMBERS = frozenset("""
    empty_space health last_damage last_health last_health_percentage vehicle_health food armor
    air max_health health_percentage vehicle_max_health max_health_with_absorption
    vehicle_max_health_with_absorption vehicle_health_percentage max_air level hotbar_slot
    potion_effect_duration total_amount storage absorption vehicle_air vehicle_max_air
""".split())
BETTERHUD_BOOLEANS = frozenset("""
    dead frozen burning has_off_hand has_main_hand has_permission
""".split())
BETTERHUD_STRINGS = frozenset("""
    name world gamemode custom_variable custom_name display_name type
""".split())
BETTERHUD_PLACEHOLDERS = BETTERHUD_NUMBERS | BETTERHUD_BOOLEANS | BETTERHUD_STRINGS
BETTERHUD_LISTENERS = frozenset("""
    health vehicle_health food armor air exp absorption placeholder
""".split())

# PlaceholderAPI expansions OTHER than LegendCraft's that a HUD file may read. Empty on
# purpose: the box's expansions folder is empty, so any foreign id today resolves to nothing.
# An entry is `id prefix -> what installing that expansion takes`, and adding one is a claim
# that the deploy actually installs it -- e.g. "player_": "/papi ecloud download Player".
FOREIGN_PAPI_EXPANSIONS: dict = {}

# Operands that name no provider at all.
LITERAL_WORDS = frozenset(("true", "false"))

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
    "feedback_line": "reads blank at rest and is ungated; accepted debt, waiting on HUD-FEEDBACK-EMPTY",
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


def unquote(raw: str) -> str:
    """One layer of YAML quoting off, so `"papi:x"` and `"'mana'"` reach the classifier as
    `papi:x` and `'mana'` -- the second still quoted, because that inner quoting is what makes
    it a string LITERAL rather than a placeholder name."""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def classify_operand(raw: str):
    """(kind, name) for one condition operand or listener class.

    kind is "literal" (names no provider), "papi" (the name is a full expansion id), or
    "builtin" (the name is BetterHud's own).
    """
    value = unquote(raw.strip())
    if not value:
        return ("literal", None)
    # A quoted inner value is a string literal: `"'mana'"`, `"'3'"`.
    if value[0] in "\"'":
        return ("literal", None)
    # Bar values carry a cast: `(number)papi:legendcraft_xp_percent`.
    if value.startswith("(") and ")" in value:
        value = value[value.index(")") + 1:]
    if value.startswith("papi:"):
        return ("papi", value[len("papi:"):])
    if value in LITERAL_WORDS:
        return ("literal", None)
    try:
        float(value)
        return ("literal", None)
    except ValueError:
        pass
    # An arg-taking built-in is `<name>:<arg>` -- only the head is the registered name.
    return ("builtin", value.split(":", 1)[0])


def foreign_expansion_declared(placeholder_id: str) -> bool:
    return any(placeholder_id.startswith(prefix) for prefix in FOREIGN_PAPI_EXPANSIONS)


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
            pattern_match = PATTERN_LINE_RX.match(line)
            for placeholder_id in PLACEHOLDER_REF_RX.findall(line):
                seen += 1
                if not is_answered(placeholder_id, bare, prefixes, fields):
                    failures.append("%s:%d: %s%s names no case in HudPlaceholders"
                                    % (display, lineno, PLACEHOLDER_PREFIX, placeholder_id))
                elif pattern_match and placeholder_id not in PATTERN_SAFE_PLACEHOLDERS:
                    failures.append(
                        "%s:%d: %s%s is read inside a pattern but is not on the pattern allow-list"
                        % (display, lineno, PLACEHOLDER_PREFIX, placeholder_id))

            # A `papi:` id from any OTHER expansion, wherever it sits. This is the door the
            # gate did not watch: not being `legendcraft_` was the whole reason it passed.
            for placeholder_id in ANY_PAPI_REF_RX.findall(line):
                if placeholder_id.startswith(PLACEHOLDER_PREFIX):
                    continue
                seen += 1
                if not foreign_expansion_declared(placeholder_id):
                    failures.append(
                        "%s:%d: papi:%s belongs to a PlaceholderAPI expansion this repo does not "
                        "declare -- add it to FOREIGN_PAPI_EXPANSIONS with what installing it "
                        "takes, or the id resolves to nothing and the element never draws"
                        % (display, lineno, placeholder_id))

            # Bare operands and listener classes: BetterHud's own vocabulary, two positions.
            for line_rx, vocabulary, position in (
                (OPERAND_LINE_RX, BETTERHUD_PLACEHOLDERS, "placeholder"),
                (LISTENER_CLASS_LINE_RX, BETTERHUD_LISTENERS, "listener class"),
            ):
                match = line_rx.match(line)
                if not match:
                    continue
                kind, name = classify_operand(match.group(1))
                if kind != "builtin":
                    continue
                seen += 1
                if name not in vocabulary:
                    failures.append(
                        "%s:%d: `%s` is no BetterHud %s in build %s -- BetterHud answers nothing "
                        "to it and the element silently does not draw"
                        % (display, lineno, name, position, BETTERHUD_BUILD))

    if failures:
        print("FAIL: %d placeholder problem(s) across %d reference(s)" % (len(failures), seen))
        for failure in failures:
            print("  " + failure)
        return 1
    print("OK: %d operand(s), every one attributed to a provider that answers it; "
          "every pattern id allow-listed. BetterHud vocabulary pinned to build %s."
          % (seen, BETTERHUD_BUILD))
    return 0


if __name__ == "__main__":
    sys.exit(main())
