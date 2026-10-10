"""Acceptance suite for the ghost mark: the gate over shipped tints, and the item shader's reading.

A ghost limb rig's tint colours carry an alpha code (tools/ghost_mark.py) that the item shader
turns into the face's alpha. Any other tint carrying it would draw its item translucent.

Acceptance criteria:
1. The mark is read exactly: both mark nibbles and a level from 1 to LEVELS - 1. Control: level 0,
   a wrong nibble, white and the void marker are not marks.
2. A constant tint carrying the mark fails the gate, naming the file; so does a tint source's
   default, and a constant given as a float triple.
3. Control: a tree whose tints carry no mark passes.
4. Each item shader this lane covers (the 26.1 and 26.2 overlays) declares the mark's exact values
   and draws a marked face at its level's alpha.

    python tools/test_check_ghost_mark.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ghost_mark import LEVELS, MARK_BLUE, MARK_RED, is_ghost_coded  # noqa: E402
from void_marker import void_tint  # noqa: E402

GATE = os.path.join(HERE, "check_ghost_mark.py")
SOURCE = os.path.join(os.path.dirname(HERE), "src")
COVERED_OVERLAYS = ("legendcraft_26_1", "legendcraft_26_2")


def coded(rgb, level):
    return (rgb & 0xF0F0F0) | (MARK_RED << 16) | (level << 8) | MARK_BLUE


def item(tints):
    return {"model": {"type": "minecraft:model", "model": "legendcraft:item/fixture",
                      "tints": tints}}


class GhostMarkTest(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="ghostmark-")
        self.addCleanup(shutil.rmtree, self.workspace, True)
        self.tree = os.path.join(self.workspace, "src")
        os.makedirs(self.tree)

    def write(self, relative, definition):
        path = os.path.join(self.tree, *relative.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(definition, handle)

    def gate(self):
        return subprocess.run([sys.executable, GATE, "--source-tree", self.tree],
                              capture_output=True, text=True)

    def test_the_mark_is_read_exactly(self):
        for level in range(1, LEVELS):
            self.assertTrue(is_ghost_coded(coded(0x8C5A3B, level)), "level %d is a mark" % level)
        self.assertFalse(is_ghost_coded(coded(0x8C5A3B, 0)), "level 0 draws nothing; never a mark")
        self.assertFalse(is_ghost_coded(coded(0x8C5A3B, 6) ^ 0x010000), "red's nibble is the mark")
        self.assertFalse(is_ghost_coded(coded(0x8C5A3B, 6) ^ 0x000001), "blue's nibble is the mark")
        self.assertFalse(is_ghost_coded(0xFFFFFF), "an untinted face is not a mark")
        self.assertFalse(is_ghost_coded(void_tint()), "the void marker is not a mark")

    def test_a_shipped_tint_carrying_the_mark_fails(self):
        self.write("assets/legendcraft/items/constant.json",
                   item([{"type": "minecraft:constant", "value": coded(0x404040, 3)}]))
        result = self.gate()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("assets/legendcraft/items/constant.json", result.stdout)

        os.remove(os.path.join(self.tree, "assets", "legendcraft", "items", "constant.json"))
        self.write("legendcraft_26_2/assets/legendcraft/items/nested/default.json",
                   {"model": {"type": "minecraft:composite", "models": [item(
                       [{"type": "minecraft:custom_model_data", "index": 0,
                         "default": coded(0xFFFFFF, 9)}])["model"]]}})
        result = self.gate()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("legendcraft_26_2/assets/legendcraft/items/nested/default.json",
                      result.stdout)

        os.remove(os.path.join(self.tree, "legendcraft_26_2", "assets", "legendcraft", "items",
                               "nested", "default.json"))
        rgb = coded(0x202020, 6)
        triple = [((rgb >> shift) & 0xFF) / 255.0 for shift in (16, 8, 0)]
        self.write("assets/legendcraft/items/triple.json",
                   item([{"type": "minecraft:constant", "value": triple}]))
        result = self.gate()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("assets/legendcraft/items/triple.json", result.stdout)

    def test_control_unmarked_tints_pass(self):
        self.write("assets/legendcraft/items/plain.json", item([
            {"type": "minecraft:constant", "value": 0xFFFFFF},
            {"type": "minecraft:constant", "value": void_tint()},
            {"type": "minecraft:custom_model_data", "index": 0, "default": 0x8B0000},
            {"type": "minecraft:dye", "default": coded(0x404040, 0)}]))
        result = self.gate()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_the_covered_item_shaders_draw_the_mark(self):
        for overlay in COVERED_OVERLAYS:
            shaders = os.path.join(SOURCE, overlay, "assets", "minecraft", "shaders", "core")
            with open(os.path.join(shaders, "item.vsh"), encoding="utf-8") as handle:
                vertex = handle.read()
            with open(os.path.join(shaders, "item.fsh"), encoding="utf-8") as handle:
                fragment = handle.read()
            for name, value in (("GHOST_MARK_RED", MARK_RED), ("GHOST_MARK_BLUE", MARK_BLUE),
                                ("GHOST_LEVELS", LEVELS)):
                declared = re.search(r"const float %s = ([0-9.]+);" % name, vertex)
                self.assertIsNotNone(declared, "%s item.vsh declares %s" % (overlay, name))
                self.assertEqual(float(value), float(declared.group(1)),
                                 "%s item.vsh: %s" % (overlay, name))
            self.assertIn("out float ghostAlpha;", vertex, overlay)
            self.assertIn("in float ghostAlpha;", fragment, overlay)
            self.assertRegex(fragment, r"color\.a \*= ghostAlpha;",
                             "%s item.fsh draws a marked face at its level's alpha" % overlay)


if __name__ == "__main__":
    unittest.main()
