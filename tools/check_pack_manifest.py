#!/usr/bin/env python3
"""Gate: a merged pack still carries everything its inputs put into it.

The merge that produces the served pack reads a base pack off disk and two plugin build zips.
Any of those can be stale, partial, or built from the wrong tree, and the result is a valid
zip that simply lacks things -- so nothing throws, the upload succeeds, and the loss shows up
as art that does not render. A merged pack whose base was months old shipped with 133 item
models where the source tree held 216; the 83 missing ones were an entire ability's art, and
no commit anywhere had changed.

Counting the merged output against the SOURCE TREE, rather than checking that the thing you
just added is present, is what catches a loss: a stale input fails in exactly one direction,
gaining nothing and quietly dropping what it never had.

    python tools/check_pack_manifest.py --pack <zip> [--source-tree <dir>] [--plugin-source <zip>]

`--plugin-source` may be repeated; each one's entries must all have survived the merge. Given
none, the plugin half is reported as unchecked rather than passed.
"""

from __future__ import annotations

import argparse
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
DEFAULT_SOURCE_TREE = os.path.join(REPO_ROOT, "src")

# Where this pack's own assets live inside the zip, and inside src/.
ITEM_MODEL_PREFIX = "assets/legendcraft/items/"
ITEM_MODEL_SUFFIX = ".json"
SOUND_INDEX_NAME = "sounds.json"
SOUND_SUFFIX = ".ogg"

# pack.png is deliberately kept from the base on collision, so a plugin source's copy is
# expected to be absent from the merge. Nothing else is.
MERGE_COLLISION_WINNERS = ("pack.png", "pack.mcmeta")


def tree_entries(source_tree: str):
    """Every file under the source tree, as the zip-relative path the merge would give it."""
    entries = set()
    for directory, _subdirs, names in os.walk(source_tree):
        for name in names:
            full = os.path.join(directory, name)
            entries.add(os.path.relpath(full, source_tree).replace(os.sep, "/"))
    return entries


def item_models(entries):
    return {e for e in entries
            if e.startswith(ITEM_MODEL_PREFIX) and e.endswith(ITEM_MODEL_SUFFIX)}


def sounds(entries):
    return {e for e in entries if e.endswith(SOUND_SUFFIX)}


def sound_indexes(entries):
    return {e for e in entries if e.rsplit("/", 1)[-1] == SOUND_INDEX_NAME}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True)
    parser.add_argument("--source-tree", default=DEFAULT_SOURCE_TREE)
    parser.add_argument("--plugin-source", action="append", default=[])
    args = parser.parse_args()

    with zipfile.ZipFile(args.pack) as archive:
        packed = {n for n in archive.namelist() if not n.endswith("/")}
    source = tree_entries(args.source_tree)

    failures = []

    missing_models = sorted(item_models(source) - packed)
    if missing_models:
        failures.append("%d item model(s) in the source tree are absent from the pack, first: %s"
                        % (len(missing_models), missing_models[0]))

    missing_sounds = sorted(sounds(source) - packed)
    if missing_sounds:
        failures.append("%d sound file(s) in the source tree are absent from the pack, first: %s"
                        % (len(missing_sounds), missing_sounds[0]))

    missing_indexes = sorted(sound_indexes(source) - packed)
    if missing_indexes:
        failures.append("%d sounds.json absent from the pack: %s"
                        % (len(missing_indexes), ", ".join(missing_indexes)))

    plugin_checked = 0
    for plugin_zip in args.plugin_source:
        with zipfile.ZipFile(plugin_zip) as archive:
            contributed = {n for n in archive.namelist()
                           if not n.endswith("/") and n not in MERGE_COLLISION_WINNERS}
        plugin_checked += len(contributed)
        lost = sorted(contributed - packed)
        if lost:
            failures.append("%d entr(ies) from %s did not survive the merge, first: %s"
                            % (len(lost), os.path.basename(plugin_zip), lost[0]))

    if failures:
        print("FAIL: %s" % os.path.basename(args.pack))
        for failure in failures:
            print("  " + failure)
        return 1

    print("OK: %s carries %d item model(s), %d sound(s), %d sounds.json"
          % (os.path.basename(args.pack), len(item_models(source)),
             len(sounds(source)), len(sound_indexes(source))))
    if args.plugin_source:
        print("    and every one of %d plugin-contributed entr(ies) across %d source(s)"
              % (plugin_checked, len(args.plugin_source)))
    else:
        print("    plugin-contributed assets UNCHECKED -- no --plugin-source given")
    return 0


if __name__ == "__main__":
    sys.exit(main())
