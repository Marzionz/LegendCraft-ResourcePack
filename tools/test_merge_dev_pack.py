"""Acceptance suite for the dev pack merge's format bound, run in CI.

The plugin packs merged into the served pack declare overlay ranges far past any client the
pack was tested on: MythicArmors' reach format 65535, BetterHud's 99. Carried into the merged
pack.mcmeta verbatim, they make a newer client apply their core shaders, and a client that
cannot compile one rejects the whole pack. The fixtures here copy those plugins' pack.mcmeta
shapes, both range forms included.

Acceptance criteria:
1. No range in the merged pack.mcmeta, base or overlay, in either form, ends above
   TESTED_MAX_FORMAT; an overlay that started below it keeps its lower bound.
2. An overlay that starts above TESTED_MAX_FORMAT is absent from the merged overlays.
3. An overlay already inside the tested range comes through unchanged.
4. The merge reports every clamp and every drop, naming the overlay directory, and main()
   prints the report.
5. A base pack declaring a pack_format above TESTED_MAX_FORMAT stops the merge, and so does one
   whose range starts above it; a base declaring exactly TESTED_MAX_FORMAT merges unchanged.

    python tools/test_merge_dev_pack.py
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

import merge_dev_pack  # noqa: E402
from pack_formats import TESTED_MAX_FORMAT  # noqa: E402

UNBOUNDED = 65535
FUTURE = TESTED_MAX_FORMAT + 1

MYTHICARMORS_MCMETA = {
    "pack": {"description": "armour", "pack_format": 63, "min_format": 63,
             "max_format": UNBOUNDED, "supported_formats": [63, UNBOUNDED]},
    "overlays": {"entries": [
        {"min_format": 63, "max_format": UNBOUNDED,
         "formats": {"min_inclusive": 63, "max_inclusive": UNBOUNDED},
         "directory": "mythicarmors_1_21_6"},
        {"min_format": 84, "max_format": UNBOUNDED,
         "formats": {"min_inclusive": 84, "max_inclusive": UNBOUNDED},
         "directory": "mythicarmors_26_1"},
    ]},
}
BETTERHUD_MCMETA = {
    "pack": {"pack_format": TESTED_MAX_FORMAT, "description": "hud",
             "supported_formats": [9, TESTED_MAX_FORMAT], "min_format": 9,
             "max_format": TESTED_MAX_FORMAT},
    "overlays": {"entries": [
        {"formats": [56, 83], "directory": "betterhud_1_21_6", "min_format": 56, "max_format": 83},
        {"formats": [84, 99], "directory": "betterhud_26_1", "min_format": 84, "max_format": 99},
    ]},
}
FUTURE_ONLY_MCMETA = {
    "pack": {"pack_format": FUTURE, "description": "future", "min_format": FUTURE,
             "max_format": FUTURE + 2},
    "overlays": {"entries": [
        {"formats": [FUTURE, FUTURE + 2], "directory": "future_only",
         "min_format": FUTURE, "max_format": FUTURE + 2},
    ]},
}
BASE_MCMETA = {
    "pack": {"pack_format": TESTED_MAX_FORMAT, "description": "base",
             "supported_formats": [9, UNBOUNDED], "min_format": 9, "max_format": UNBOUNDED},
}


BASE_FORMAT_BEYOND_MCMETA = {
    "pack": {"pack_format": FUTURE, "description": "base", "min_format": 9,
             "max_format": TESTED_MAX_FORMAT},
}
BASE_RANGE_BEYOND_MCMETA = {
    "pack": {"pack_format": TESTED_MAX_FORMAT, "description": "base", "min_format": FUTURE,
             "max_format": FUTURE + 1},
}
BASE_AT_CEILING_MCMETA = {
    "pack": {"pack_format": TESTED_MAX_FORMAT, "description": "base",
             "supported_formats": [TESTED_MAX_FORMAT, TESTED_MAX_FORMAT],
             "min_format": TESTED_MAX_FORMAT, "max_format": TESTED_MAX_FORMAT},
}


def write_zip(path, mcmeta, *entries):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("pack.mcmeta", json.dumps(mcmeta))
        for entry in entries:
            archive.writestr(entry, "{}")


def upper_bounds(section, range_key):
    """Every upper bound a pack or overlay section declares, by where it declares it."""
    bounds = {"max_format": section.get("max_format")}
    value = section.get(range_key)
    if isinstance(value, dict):
        bounds[range_key] = value.get("max_inclusive")
    elif isinstance(value, list):
        bounds[range_key] = value[-1]
    return bounds


class MergeFormatBoundTest(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="mergebound-")
        self.addCleanup(shutil.rmtree, self.workspace, True)
        self.sources = []
        for name, mcmeta in (("mythicarmors", MYTHICARMORS_MCMETA),
                             ("betterhud", BETTERHUD_MCMETA),
                             ("future", FUTURE_ONLY_MCMETA),
                             ("base", BASE_MCMETA)):
            path = os.path.join(self.workspace, "%s.zip" % name)
            write_zip(path, mcmeta, "assets/%s/marker.json" % name)
            self.sources.append(path)

    def merged(self):
        entries, report = merge_dev_pack.merge(self.sources)
        return json.loads(entries["pack.mcmeta"]), report

    def overlays(self, meta):
        return {e["directory"]: e for e in meta.get("overlays", {}).get("entries", [])}

    def test_no_merged_range_ends_above_the_tested_format(self):
        meta, _ = self.merged()
        sections = [("pack", meta["pack"], "supported_formats")]
        sections += [(d, e, "formats") for d, e in self.overlays(meta).items()]
        for name, section, range_key in sections:
            for where, bound in upper_bounds(section, range_key).items():
                self.assertLessEqual(bound, TESTED_MAX_FORMAT, "%s %s" % (name, where))

    def test_a_clamped_overlay_keeps_its_lower_bound_in_both_forms(self):
        overlays = self.overlays(self.merged()[0])
        self.assertEqual({"min_format": 84, "max_format": TESTED_MAX_FORMAT,
                          "formats": {"min_inclusive": 84, "max_inclusive": TESTED_MAX_FORMAT},
                          "directory": "mythicarmors_26_1"}, overlays["mythicarmors_26_1"])
        self.assertEqual({"formats": [84, TESTED_MAX_FORMAT], "directory": "betterhud_26_1",
                          "min_format": 84, "max_format": TESTED_MAX_FORMAT},
                         overlays["betterhud_26_1"])

    def test_an_overlay_starting_above_the_tested_format_is_dropped(self):
        self.assertNotIn("future_only", self.overlays(self.merged()[0]))

    def test_an_overlay_inside_the_tested_range_is_unchanged(self):
        overlays = self.overlays(self.merged()[0])
        self.assertEqual(BETTERHUD_MCMETA["overlays"]["entries"][0], overlays["betterhud_1_21_6"])

    def test_the_merge_reports_every_clamp_and_drop(self):
        report = "\n".join(self.merged()[1])
        for directory in ("mythicarmors_1_21_6", "mythicarmors_26_1", "betterhud_26_1",
                          "future_only"):
            self.assertIn(directory, report)
        self.assertNotIn("betterhud_1_21_6", report)
        self.assertIn("dropped", report)
        self.assertIn("clamped", report)

    def merge_over_base(self, mcmeta):
        write_zip(self.sources[-1], mcmeta, "assets/base/marker.json")
        return merge_dev_pack.merge(self.sources)

    def test_a_base_declaring_a_format_above_the_ceiling_stops_the_merge(self):
        with self.assertRaises(SystemExit) as stopped:
            self.merge_over_base(BASE_FORMAT_BEYOND_MCMETA)
        self.assertIn("declares format %d" % FUTURE, str(stopped.exception))

    def test_a_base_range_starting_above_the_ceiling_stops_the_merge(self):
        with self.assertRaises(SystemExit) as stopped:
            self.merge_over_base(BASE_RANGE_BEYOND_MCMETA)
        self.assertIn("%d-%d" % (FUTURE, FUTURE + 1), str(stopped.exception))

    def test_a_base_at_the_ceiling_merges_unchanged(self):
        entries, report = self.merge_over_base(BASE_AT_CEILING_MCMETA)
        self.assertEqual(BASE_AT_CEILING_MCMETA["pack"], json.loads(entries["pack.mcmeta"])["pack"])
        self.assertNotIn("the base", "\n".join(report))

    def test_main_prints_the_report(self):
        dist = os.path.join(self.workspace, "dist")
        os.makedirs(dist)
        shutil.copy(self.sources[-1], os.path.join(dist, "LegendCraft-Pack-9.9.9.zip"))
        driver = ("import merge_dev_pack as m;"
                  "m.RP = %r;"
                  "m.SOURCES = %r;"
                  "m.main()" % (self.workspace, self.sources[:-1]))
        result = subprocess.run([sys.executable, "-c", driver], capture_output=True, text=True,
                                env=dict(os.environ, PYTHONPATH=HERE), cwd=HERE)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for line in merge_dev_pack.merge(self.sources)[1]:
            self.assertIn(line, result.stdout)
        self.assertIn("future_only", result.stdout.split("overlays:")[0])


if __name__ == "__main__":
    unittest.main()
