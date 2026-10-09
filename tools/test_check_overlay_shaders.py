"""Acceptance suite for the overlay shader gate, run in CI.

A client at MOJ_IMPORT_REJECTED_FORMAT or above cannot compile a core shader that still uses
`#moj_import`, and one shader it cannot compile makes it reject the whole pack. Overlays whose
range ends below that format are read only by older clients, which need the import.

Acceptance criteria:
1. A core shader carrying `#moj_import` in an overlay whose range reaches the format fails the
   gate, naming the file.
2. The same overlay with an import-free core shader passes.
3. A core shader carrying `#moj_import` in an overlay ending below the format passes.
4. A range declared only in the `formats` object form is read.
5. With no overlay reaching the format the gate passes and says it checked nothing.
6. Given a built pack zip, the gate reads the pack's own pack.mcmeta and entries.

    python tools/test_check_overlay_shaders.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pack_formats import MOJ_IMPORT_REJECTED_FORMAT  # noqa: E402

GATE = os.path.join(HERE, "check_overlay_shaders.py")
REJECTING = MOJ_IMPORT_REJECTED_FORMAT
SHADER = "assets/minecraft/shaders/core/item.vsh"
IMPORTING = "#version 330\n#moj_import <minecraft:fog.glsl>\nvoid main() {}\n"
IMPORT_FREE = "#version 330\nvoid main() {}\n"


def overlay(directory, low, high):
    return {"formats": [low, high], "min_format": low, "max_format": high,
            "directory": directory}


def mcmeta(*entries):
    return {"pack": {"pack_format": 84, "description": "fixture"},
            "overlays": {"entries": list(entries)}}


class OverlayShaderGateTest(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="overlayshaders-")
        self.addCleanup(shutil.rmtree, self.workspace, True)
        self.tree = os.path.join(self.workspace, "src")
        os.makedirs(self.tree)

    def write(self, meta, files):
        with open(os.path.join(self.tree, "pack.mcmeta"), "w", encoding="utf-8") as handle:
            json.dump(meta, handle)
        for name, text in files.items():
            path = os.path.join(self.tree, *name.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)

    def gate(self, *argv):
        return subprocess.run([sys.executable, GATE, *argv], capture_output=True, text=True)

    def gate_tree(self):
        return self.gate("--source-tree", self.tree)

    def test_an_importing_core_shader_in_an_overlay_reaching_the_format_fails(self):
        self.write(mcmeta(overlay("next", 84, REJECTING)), {"next/" + SHADER: IMPORTING})
        result = self.gate_tree()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("next/" + SHADER, result.stdout)

    def test_an_import_free_core_shader_in_that_overlay_passes(self):
        self.write(mcmeta(overlay("next", 84, REJECTING)), {"next/" + SHADER: IMPORT_FREE})
        result = self.gate_tree()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("1 core shader(s)", result.stdout)

    def test_an_importing_core_shader_in_an_overlay_ending_below_the_format_passes(self):
        self.write(mcmeta(overlay("older", 84, REJECTING - 1)), {"older/" + SHADER: IMPORTING})
        result = self.gate_tree()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_a_range_declared_only_as_a_formats_object_is_read(self):
        entry = {"formats": {"min_inclusive": 84, "max_inclusive": REJECTING + 2},
                 "directory": "objectform"}
        self.write(mcmeta(entry), {"objectform/" + SHADER: IMPORTING})
        result = self.gate_tree()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("objectform/" + SHADER, result.stdout)

    def test_no_overlay_reaching_the_format_reports_nothing_checked(self):
        self.write(mcmeta(overlay("older", 84, REJECTING - 1)), {"older/" + SHADER: IMPORT_FREE})
        result = self.gate_tree()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("no overlay reaches format %d" % REJECTING, result.stdout)

    def test_a_built_pack_is_read_from_the_zip(self):
        pack = os.path.join(self.workspace, "pack.zip")
        with zipfile.ZipFile(pack, "w") as archive:
            archive.writestr("pack.mcmeta", json.dumps(mcmeta(overlay("next", 84, REJECTING))))
            archive.writestr("next/" + SHADER, IMPORTING)
        result = self.gate("--pack", pack)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("next/" + SHADER, result.stdout)


if __name__ == "__main__":
    unittest.main()
