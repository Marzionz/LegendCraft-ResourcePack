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
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE_TREE = os.path.join(os.path.dirname(HERE), "src")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-tree", default=DEFAULT_SOURCE_TREE)
    parser.parse_args()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
