#!/usr/bin/env python3
"""Gate: the BetterHud files parse, and hold the invariants the generator writes them under.

BetterHud reports a malformed element as one untagged INFO line and then renders the hud
without it -- or drops the hud entirely. Every failure this checks for is therefore silent in
the only place it matters, and the cost is paid by whoever joins the server next.

    python tools/check_hud_yaml.py [--hud-root <dir>]

Checked, per file kind:
  registry (images/)  every entry declares a type; every file it names exists under hud/
  layout   (layouts/) every element declares a name and a layer; every image element's name is
                      a registered image; every layer is inside the generator's band
  hud      (huds/)    every layout it composes exists
  conditions          every numbered block declares first, second and operation

And over EVERY `.yml` in the tree, at any depth: every `pattern:` obeys the text parser's
slash rule (see SLASH_RUN_LENGTH below).
"""

from __future__ import annotations

import argparse
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
DEFAULT_HUD_ROOT = os.path.join(REPO_ROOT, "hud", "betterhud")
ART_ROOT = os.path.join(REPO_ROOT, "hud")

# BetterHud resolves an image `file:` under its own assets root, where the deploy copies this
# repo's hud/ trees as one namespace directory. Stripping that segment is what maps a
# registered path back onto a file in this tree.
ASSET_NAMESPACE = "legendcraft/"
# A sequence frame is `<path>:<hold-ticks>`; the hold is not part of the path.
FRAME_HOLD_SEPARATOR = ":"

# The generator draws in a single band: 1 is the bar/frame ground and 18 is the topmost
# affliction overlay. A layer outside it is an element the compositor never placed, which means
# it was hand-edited into a file whose header forbids exactly that.
MIN_LAYER = 1
MAX_LAYER = 18

# The two element sections a layout may carry, and the sections that are settings rather than
# elements.
ELEMENT_SECTIONS = ("images", "texts")
CONDITION_FIELDS = ("first", "second", "operation")
# `conditions` carries numbered blocks plus an optional combinator; only the blocks have shape.
CONDITION_GATE_KEY = "gate"

# BetterHud 2.1.0-447's text parser EATS one "/" out of every run of them, and the literal in
# front of the run fuses onto the next placeholder token: "HP/[papi:x]" comes back as
# `this placeholder not found: HP[papi` and the hud does not load -- every other element in it
# with it. A "//" run survives that as a single rendered "/", and only with a colour tag on
# each side; dropping the tag after it broke parsing outright at the box.
#
# generate_hud.py writes exactly that as SEP and has since the stat block existed. The party
# rows are hand-authored, so they inherited nothing and shipped the bare form, which is what
# refused lc_stat_hud for three days. This rule is over every pattern in the tree rather than
# the generated ones, because the generated ones were never the problem.
PATTERN_KEY = "pattern"
SLASH_RUN_LENGTH = 2
SLASH_RUN_RX = re.compile(r"/+")
# A MiniMessage tag closing immediately before the run, and one opening immediately after it.
TAG_BEFORE_RX = re.compile(r"<[^<>]+>\s*$")
TAG_AFTER_RX = re.compile(r"^\s*<[^<>]+>")


def numbered(mapping):
    """The numbered entries of a BetterHud block, in file order, skipping named settings."""
    for key, value in mapping.items():
        if str(key).isdigit():
            yield key, value


def art_path(reference: str) -> str:
    path = reference.split(FRAME_HOLD_SEPARATOR)[0]
    if path.startswith(ASSET_NAMESPACE):
        path = path[len(ASSET_NAMESPACE):]
    return os.path.join(ART_ROOT, *path.split("/"))


def check_conditions(where, element, failures):
    conditions = element.get("conditions")
    if conditions is None:
        return
    if not isinstance(conditions, dict):
        failures.append("%s: conditions is not a block" % where)
        return
    for key, block in numbered(conditions):
        if not isinstance(block, dict):
            failures.append("%s: condition %s is not a block" % (where, key))
            continue
        missing = [field for field in CONDITION_FIELDS if field not in block]
        if missing:
            failures.append("%s: condition %s declares no %s"
                            % (where, key, ", ".join(missing)))
    for key in conditions:
        if not str(key).isdigit() and key != CONDITION_GATE_KEY:
            failures.append("%s: conditions carries an unknown key %r" % (where, key))


def check_registry(path, display, failures, registered):
    document = yaml.safe_load(open(path, encoding="utf-8").read()) or {}
    for name, entry in document.items():
        registered.add(name)
        where = "%s: image %s" % (display, name)
        if not isinstance(entry, dict) or "type" not in entry:
            failures.append("%s declares no type" % where)
            continue
        references = []
        if "file" in entry:
            references.append(entry["file"])
        references.extend(entry.get("files", []) or [])
        if not references:
            failures.append("%s names no file" % where)
        for reference in references:
            resolved = art_path(str(reference))
            if not os.path.isfile(resolved):
                failures.append("%s references %s, which is not a file in this tree"
                                % (where, reference))


def check_layout(path, display, failures, layouts):
    document = yaml.safe_load(open(path, encoding="utf-8").read()) or {}
    for layout_name, layout in document.items():
        layouts[layout_name] = display
        if not isinstance(layout, dict):
            failures.append("%s: layout %s is not a block" % (display, layout_name))
            continue
        for section in ELEMENT_SECTIONS:
            for key, element in numbered(layout.get(section, {}) or {}):
                where = "%s: %s.%s element %s" % (display, layout_name, section, key)
                if not isinstance(element, dict):
                    failures.append("%s is not a block" % where)
                    continue
                if "name" not in element:
                    failures.append("%s declares no name" % where)
                if "layer" not in element:
                    failures.append("%s declares no layer" % where)
                else:
                    layer = element["layer"]
                    if not isinstance(layer, int) or not MIN_LAYER <= layer <= MAX_LAYER:
                        failures.append("%s sits at layer %r, outside %d..%d"
                                        % (where, layer, MIN_LAYER, MAX_LAYER))
                check_conditions(where, element, failures)


def check_layout_image_names(path, display, failures, registered):
    document = yaml.safe_load(open(path, encoding="utf-8").read()) or {}
    for layout_name, layout in document.items():
        if not isinstance(layout, dict):
            continue
        for key, element in numbered(layout.get("images", {}) or {}):
            if isinstance(element, dict) and element.get("name") not in registered:
                failures.append("%s: %s.images element %s draws %r, which no registry declares"
                                % (display, layout_name, key, element.get("name")))


def check_hud(path, display, failures, layouts):
    document = yaml.safe_load(open(path, encoding="utf-8").read()) or {}
    for hud_name, hud in document.items():
        if not isinstance(hud, dict):
            failures.append("%s: hud %s is not a block" % (display, hud_name))
            continue
        for key, entry in numbered(hud.get("layouts", {}) or {}):
            name = entry.get("name") if isinstance(entry, dict) else None
            if name not in layouts:
                failures.append("%s: hud %s layout %s composes %r, which no layout file defines"
                                % (display, hud_name, key, name))


def patterns_in(node, trail):
    """Every `pattern:` string in a parsed document, with the key path that reaches it.

    Recursive rather than section-aware: the rule is the text parser's, so it holds wherever a
    pattern is written, including file kinds and nesting depths the shape checks above do not
    know about.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            reached = trail + [str(key)]
            if key == PATTERN_KEY and isinstance(value, str):
                yield ".".join(reached), value
            else:
                yield from patterns_in(value, reached)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from patterns_in(value, trail + [str(index)])


def check_pattern_slashes(path, display, failures):
    document = yaml.safe_load(open(path, encoding="utf-8").read()) or {}
    for trail, pattern in patterns_in(document, []):
        where = "%s: %s" % (display, trail)
        for run in SLASH_RUN_RX.finditer(pattern):
            if len(run.group(0)) != SLASH_RUN_LENGTH:
                failures.append(
                    "%s: %r carries a run of %d slash(es); BetterHud eats one, so a separator "
                    "has to be written \"//\" to render as one"
                    % (where, pattern, len(run.group(0))))
                continue
            if not TAG_BEFORE_RX.search(pattern[:run.start()]):
                failures.append("%s: %r has no colour tag before its \"//\"; the literal in "
                                "front fuses onto the next placeholder token"
                                % (where, pattern))
            if not TAG_AFTER_RX.search(pattern[run.end():]):
                failures.append("%s: %r has no colour tag after its \"//\"" % (where, pattern))


def files_in(hud_root, subdir):
    directory = os.path.join(hud_root, subdir)
    if not os.path.isdir(directory):
        return []
    return [os.path.join(directory, name)
            for name in sorted(os.listdir(directory)) if name.endswith(".yml")]


def every_yml(hud_root):
    for directory, _subdirs, names in os.walk(hud_root):
        for name in sorted(names):
            if name.endswith(".yml"):
                yield os.path.join(directory, name)


def display_path(path):
    """The path as this repo names it, or the absolute one when it is not under this repo.

    The suites point --hud-root at a fixture in temp, which on Windows can be a different
    volume from the repo -- and relpath raises rather than answering across volumes.
    """
    try:
        return os.path.relpath(path, REPO_ROOT)
    except ValueError:
        return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hud-root", default=DEFAULT_HUD_ROOT)
    args = parser.parse_args()

    failures = []
    registered = set()
    layouts = {}
    counted = 0

    for path in files_in(args.hud_root, "images"):
        counted += 1
        check_registry(path, display_path(path), failures, registered)
    layout_paths = files_in(args.hud_root, "layouts")
    for path in layout_paths:
        counted += 1
        check_layout(path, display_path(path), failures, layouts)
    # Registry names are only complete once every registry file has been read, so the
    # cross-file check is a second pass rather than part of the first.
    for path in layout_paths:
        check_layout_image_names(path, display_path(path), failures, registered)
    for path in files_in(args.hud_root, "huds"):
        counted += 1
        check_hud(path, display_path(path), failures, layouts)

    # The pattern rule is the parser's, not a section's, so its walk is the whole tree rather
    # than the three directories above -- a hand-authored file in a fourth one carries the
    # same defect and would otherwise be read by nothing.
    walked = 0
    for path in every_yml(args.hud_root):
        walked += 1
        check_pattern_slashes(path, display_path(path), failures)

    if not counted:
        print("FAIL: no BetterHud files under %s -- this gate checked nothing" % args.hud_root)
        return 1
    if failures:
        print("FAIL: %d shape problem(s) across %d file(s)" % (len(failures), counted))
        for failure in failures:
            print("  " + failure)
        return 1
    print("OK: %d BetterHud file(s), %d registered image(s), %d layout(s), "
          "%d file(s) walked for pattern slashes"
          % (counted, len(registered), len(layouts), walked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
