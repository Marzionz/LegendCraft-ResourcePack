#!/usr/bin/env python3
"""Gate: no overlay a client at MOJ_IMPORT_REJECTED_FORMAT or above applies carries a core
shader still using `#moj_import`.

That client cannot compile such a shader, and one shader it cannot compile makes it reject the
whole pack. Overlays whose range ends below the format are read only by older clients, which
need the import, so they are not this gate's subject.

    python tools/check_overlay_shaders.py [--source-tree <dir>] [--pack <zip>]

Reads the source tree (default `src/`), or a built pack when `--pack` is given.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile

from pack_formats import MOJ_IMPORT_REJECTED_FORMAT, OVERLAY_RANGE_KEY, declared_ranges

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE_TREE = os.path.join(os.path.dirname(HERE), "src")
CORE_SHADER_DIR = "assets/minecraft/shaders/core/"
MOJ_IMPORT = b"#moj_import"


def overlays_reaching(meta, fmt):
    return [entry["directory"] for entry in meta.get("overlays", {}).get("entries", [])
            if any(high >= fmt for _, high in declared_ranges(entry, OVERLAY_RANGE_KEY))]


def core_shaders(directories, names):
    prefixes = tuple("%s/%s" % (directory, CORE_SHADER_DIR) for directory in directories)
    return sorted(name for name in names if name.startswith(prefixes))


def tree_names(root):
    for directory, _subdirs, files in os.walk(root):
        for name in files:
            yield os.path.relpath(os.path.join(directory, name), root).replace(os.sep, "/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-tree", default=DEFAULT_SOURCE_TREE)
    parser.add_argument("--pack")
    args = parser.parse_args()

    if args.pack:
        archive = zipfile.ZipFile(args.pack)
        names = [n for n in archive.namelist() if not n.endswith("/")]
        read = archive.read
        subject = os.path.basename(args.pack)
    else:
        names = list(tree_names(args.source_tree))

        def read(name):
            with open(os.path.join(args.source_tree, *name.split("/")), "rb") as handle:
                return handle.read()
        subject = args.source_tree

    directories = overlays_reaching(json.loads(read("pack.mcmeta")), MOJ_IMPORT_REJECTED_FORMAT)
    if not directories:
        print("OK: %s -- no overlay reaches format %d, nothing to check"
              % (subject, MOJ_IMPORT_REJECTED_FORMAT))
        return 0

    shaders = core_shaders(directories, names)
    importing = [name for name in shaders if MOJ_IMPORT in read(name)]
    if importing:
        print("FAIL: %s -- %d core shader(s) in an overlay reaching format %d still use #moj_import:"
              % (subject, len(importing), MOJ_IMPORT_REJECTED_FORMAT))
        for name in importing:
            print("  " + name)
        return 1

    print("OK: %s -- %d core shader(s) across overlay(s) %s reaching format %d, none uses #moj_import"
          % (subject, len(shaders), ", ".join(directories), MOJ_IMPORT_REJECTED_FORMAT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
