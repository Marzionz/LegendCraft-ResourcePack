#!/usr/bin/env python3
"""Gate: no tint the pack ships carries the ghost mark.

The item shader draws any face whose tint carries the mark (tools/ghost_mark.py) at the alpha its
level names. A constant tint, or a tint source's default, that happens to carry it would draw that
item translucent for every player.

    python tools/check_ghost_mark.py [--source-tree <dir>]

Reads every item definition under the source tree (default `src/`), overlays included.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from ghost_mark import is_ghost_coded

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE_TREE = os.path.join(os.path.dirname(HERE), "src")
TINT_VALUE_KEYS = ("value", "default")


def as_rgb(value):
    """A tint value as 0xRRGGBB: an int, or a triple of floats from 0 to 1."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value & 0xFFFFFF
    if isinstance(value, list) and len(value) in (3, 4) and all(
            isinstance(channel, (int, float)) for channel in value):
        red, green, blue = (round(float(channel) * 255) & 0xFF for channel in value[:3])
        return (red << 16) | (green << 8) | blue
    return None


def marked_tints(node):
    """Every tint value under an item definition node that carries the mark."""
    found = []
    if isinstance(node, dict):
        for tint in node.get("tints", []) if isinstance(node.get("tints"), list) else []:
            if isinstance(tint, dict):
                for key in TINT_VALUE_KEYS:
                    rgb = as_rgb(tint.get(key))
                    if rgb is not None and is_ghost_coded(rgb):
                        found.append("%s %06X" % (key, rgb))
        for child in node.values():
            found.extend(marked_tints(child))
    elif isinstance(node, list):
        for child in node:
            found.extend(marked_tints(child))
    return found


def item_definitions(root):
    for directory, _subdirs, files in os.walk(root):
        parts = os.path.relpath(directory, root).replace(os.sep, "/").split("/")
        if "items" not in parts:
            continue
        for name in sorted(files):
            if name.endswith(".json"):
                path = os.path.join(directory, name)
                yield os.path.relpath(path, root).replace(os.sep, "/"), path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-tree", default=DEFAULT_SOURCE_TREE)
    args = parser.parse_args()

    failures = []
    checked = 0
    for relative, path in item_definitions(args.source_tree):
        with open(path, encoding="utf-8") as handle:
            definition = json.load(handle)
        checked += 1
        for tint in marked_tints(definition):
            failures.append("  %s: %s" % (relative, tint))
    if failures:
        print("FAIL: %d shipped tint(s) carry the ghost mark, which the item shader draws "
              "translucent:" % len(failures))
        print("\n".join(failures))
        return 1
    print("OK: %d item definition(s), no tint carries the ghost mark" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
