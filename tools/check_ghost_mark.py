#!/usr/bin/env python3
"""Gate: no tint the pack ships carries the ghost mark.

The item shader draws any face whose tint carries the ghost mark at the alpha its level names. A
constant tint, or a tint source's default, that happens to carry it would draw that item
translucent for every player. Every item definition under the source tree is read, overlays
included; a root that is not a readable directory, a directory under it that cannot be read, or
a tree with no item definition at all fails, since the gate then checked nothing.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

from ghost_mark import is_ghost_coded

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE_TREE = os.path.join(os.path.dirname(HERE), "src")
TINT_VALUE_KEYS = ("value", "default")


def float32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def as_byte(channel):
    """One float channel as the game stores it: float32 times 255, as float32, floored."""
    return math.floor(float32(float32(float(channel)) * 255.0)) & 0xFF


def as_rgb(value):
    """A tint value as 0xRRGGBB: an int, or a triple of floats from 0 to 1."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value & 0xFFFFFF
    if isinstance(value, list) and len(value) in (3, 4) and all(
            isinstance(channel, (int, float)) and not isinstance(channel, bool)
            for channel in value):
        red, green, blue = (as_byte(channel) for channel in value[:3])
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


def item_definitions(root, errors):
    """Every item definition under root; each directory that could not be read goes to errors."""
    for directory, _subdirs, files in os.walk(root, onerror=errors.append):
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
    root = args.source_tree

    if not os.path.isdir(root) or not os.access(root, os.R_OK | os.X_OK):
        print("FAIL: %s is not a readable directory, so no tint was checked" % root)
        return 2

    failures = []
    unread = []
    walk_errors = []
    checked = 0
    for relative, path in item_definitions(root, walk_errors):
        try:
            with open(path, encoding="utf-8") as handle:
                definition = json.load(handle)
        except (OSError, ValueError) as error:
            unread.append("  %s: %s" % (relative, error))
            continue
        checked += 1
        for tint in marked_tints(definition):
            failures.append("  %s: %s" % (relative, tint))
    unread.extend("  %s" % error for error in walk_errors)

    if unread:
        print("FAIL: %d path(s) under %s could not be read, so their tints went unchecked:"
              % (len(unread), root))
        print("\n".join(unread))
        return 2
    if checked == 0:
        print("FAIL: no item definition under %s, so no tint was checked" % root)
        return 2
    if failures:
        print("FAIL: %d shipped tint(s) carry the ghost mark, which the item shader draws "
              "translucent:" % len(failures))
        print("\n".join(failures))
        return 1
    print("OK: %d item definition(s), no tint carries the ghost mark" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
