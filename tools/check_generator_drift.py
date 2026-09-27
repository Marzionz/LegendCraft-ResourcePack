#!/usr/bin/env python3
"""Gate: the committed HUD tree and flipbook frames are what the generators write.

The BetterHud YAML and the shared chrome art are generated, and every generated file says so
in its own first line. The flipbook frames under the pack's `classes/` item, model and texture
folders are generated from the flipbook rigs. A hand edit to either survives review looking like
ordinary content and is silently erased by the next regeneration, so the tree has to equal
generator output.

Run the generators first, then this. It reads what changed rather than re-deriving it, so the
files in the flipbook folders that no generator writes are never reported: regeneration leaves
them untouched.

    python tools/generate_hud.py
    python tools/gen-flipbook-frames.py
    python tools/check_generator_drift.py

A PNG is compared by DECODED PIXELS, not by the bytes of the file. PNG stores its pixels
DEFLATE-compressed, and DEFLATE output is a property of the zlib the interpreter was linked
against, not of the image: CPython on Windows ships zlib-ng while the Linux builds ship stock
zlib, so the same Pillow writing the same pixels produces different files on the two. Comparing
bytes would make this gate report every contributor whose interpreter differs from whoever last
regenerated, which is noise that trains people to ignore it -- and it would still be reporting
that noise on a tree nobody had edited. Everything else is compared byte for byte.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
GENERATED_ROOTS = (
    "hud",
    "src/assets/legendcraft/items/classes",
    "src/assets/legendcraft/models/item/classes",
    "src/assets/legendcraft/textures/item/classes",
)
PIXEL_COMPARED_SUFFIX = ".png"

# The two files under hud/ that generate_hud.py does not write. The party frames are authored by
# hand against the purchased chrome, and their registry and layout have no generator counterpart,
# so regeneration cannot change them and a change to one is an edit somebody meant to make. Left
# in, this gate would report a legitimate party edit as a hand-edited generated file and send
# whoever made it to regenerate, which would do nothing.
HAND_AUTHORED = {
    "hud/betterhud/images/legendcraft-party.yml",
    "hud/betterhud/layouts/legendcraft-party.yml",
}


def git(*args):
    result = subprocess.run(("git",) + args, cwd=REPO_ROOT, capture_output=True)
    if result.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(args), result.stderr.decode("utf-8", "replace")))
    return result.stdout


def changed_paths():
    tracked = git("diff", "--name-only", "--", *GENERATED_ROOTS).decode().split()
    untracked = git("ls-files", "--others", "--exclude-standard", "--",
                    *GENERATED_ROOTS).decode().split()
    return sorted(tracked), sorted(untracked)


def committed_bytes(path):
    return git("show", "HEAD:%s" % path)


def pixels(data):
    with Image.open(io.BytesIO(data)) as image:
        return image.mode, image.size, image.tobytes()


def main() -> int:
    for root in GENERATED_ROOTS:
        if not os.path.isdir(os.path.join(REPO_ROOT, root)):
            print("FAIL: no %s/ tree -- this gate checked nothing there" % root)
            return 1

    tracked, untracked = changed_paths()
    drifted = []
    reencoded = []

    for path in tracked:
        if path in HAND_AUTHORED:
            continue
        if not path.endswith(PIXEL_COMPARED_SUFFIX):
            drifted.append("%s differs from generator output" % path)
            continue
        try:
            before = pixels(committed_bytes(path))
            with open(os.path.join(REPO_ROOT, path), "rb") as handle:
                after = pixels(handle.read())
        except Exception as unreadable:
            drifted.append("%s could not be compared as an image: %s" % (path, unreadable))
            continue
        if before == after:
            reencoded.append(path)
        else:
            drifted.append("%s draws different pixels than the generator writes" % path)

    for path in untracked:
        drifted.append("%s is generated but not committed" % path)

    if drifted:
        print("FAIL: %d generated file(s) do not match the generator" % len(drifted))
        for entry in drifted:
            print("  " + entry)
        print("  regenerate with `python tools/generate_hud.py` and "
              "`python tools/gen-flipbook-frames.py` and commit the result;")
        print("  a generated file is never hand-edited.")
        return 1

    if reencoded:
        print("OK: %d image(s) re-encoded to the same pixels by this interpreter's zlib, 0 drifted"
              % len(reencoded))
    else:
        print("OK: the committed tree is byte-identical to generator output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
