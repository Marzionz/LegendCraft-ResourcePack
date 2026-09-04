#!/usr/bin/env python3
"""Gate: the committed HUD tree is what the generator writes.

The BetterHud YAML and the shared chrome art are generated, and every generated file says so
in its own first line. A hand edit to one survives review looking like ordinary configuration
and is silently erased by the next regeneration, so the tree has to equal generator output.

Run the generator first, then this. It reads what changed rather than re-deriving it.

    python tools/generate_hud.py
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
GENERATED_ROOT = "hud"
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
    tracked = git("diff", "--name-only", "--", GENERATED_ROOT).decode().split()
    untracked = git("ls-files", "--others", "--exclude-standard", "--", GENERATED_ROOT).decode().split()
    return sorted(tracked), sorted(untracked)


def committed_bytes(path):
    return git("show", "HEAD:%s" % path)


def pixels(data):
    with Image.open(io.BytesIO(data)) as image:
        return image.mode, image.size, image.tobytes()


def main() -> int:
    if not os.path.isdir(os.path.join(REPO_ROOT, GENERATED_ROOT)):
        print("FAIL: no %s/ tree -- this gate checked nothing" % GENERATED_ROOT)
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
        print("  regenerate with `python tools/generate_hud.py` and commit the result;")
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
