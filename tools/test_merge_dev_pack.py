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
6. An overlay whose core shaders carry `#moj_import` ends below MOJ_IMPORT_REJECTED_FORMAT in
   both forms, keeping its lower bound; one starting at or above that format is dropped; both are
   reported. An import-free overlay at that format comes through unchanged, and the merged pack
   passes the overlay shader gate.
7. The dev pack main() writes from the plugin packs, the vendor overlays folder and our pack
   carries BetterHud's and MythicArmors' 26.3 overlays, each starting and ending at
   TESTED_MAX_FORMAT, with core shaders and none using `#moj_import`; it passes the overlay shader
   gate, and the vendors' older overlays end below MOJ_IMPORT_REJECTED_FORMAT.
8. A client below MOJ_IMPORT_REJECTED_FORMAT is served the same overlays and the same bytes with
   the vendor overlays folder as without it, and the merge reports the same clamps and drops.
9. main() stops, naming the folder, when the vendor overlays folder is absent, and the merge
   stops when it cannot list a directory inside it.

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
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import merge_dev_pack  # noqa: E402
from check_overlay_shaders import MOJ_IMPORT, core_shaders  # noqa: E402
from pack_formats import (MOJ_IMPORT_REJECTED_FORMAT, OVERLAY_RANGE_KEY,  # noqa: E402
                          TESTED_MAX_FORMAT, declared_ranges)

UNBOUNDED = 65535
FUTURE = TESTED_MAX_FORMAT + 1
BELOW_REJECTING = MOJ_IMPORT_REJECTED_FORMAT - 1
SHADER_GATE = os.path.join(HERE, "check_overlay_shaders.py")
CORE_SHADER = "assets/minecraft/shaders/core/entity.vsh"
IMPORTING_SHADER = "#version 330\n#moj_import <minecraft:fog.glsl>\nvoid main() {}\n"
INCLUDING_SHADER = "#version 330\n#include <minecraft:fog.glsl>\nvoid main() {}\n"

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
IMPORTING_MCMETA = {
    "pack": {"description": "vendor shaders", "pack_format": 84, "min_format": 84,
             "max_format": UNBOUNDED, "supported_formats": [84, UNBOUNDED]},
    "overlays": {"entries": [
        {"min_format": 84, "max_format": UNBOUNDED,
         "formats": {"min_inclusive": 84, "max_inclusive": UNBOUNDED},
         "directory": "vendor_importing"},
        {"min_format": MOJ_IMPORT_REJECTED_FORMAT, "max_format": UNBOUNDED,
         "formats": {"min_inclusive": MOJ_IMPORT_REJECTED_FORMAT, "max_inclusive": UNBOUNDED},
         "directory": "vendor_importing_late"},
        {"formats": [MOJ_IMPORT_REJECTED_FORMAT, MOJ_IMPORT_REJECTED_FORMAT],
         "min_format": MOJ_IMPORT_REJECTED_FORMAT, "max_format": MOJ_IMPORT_REJECTED_FORMAT,
         "directory": "vendor_including"},
    ]},
}
IMPORTING_FILES = {
    "vendor_importing/" + CORE_SHADER: IMPORTING_SHADER,
    "vendor_importing_late/" + CORE_SHADER: IMPORTING_SHADER,
    "vendor_including/" + CORE_SHADER: INCLUDING_SHADER,
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


def write_vendor_overlays(root, mcmeta=None, files=None):
    """A vendor overlays folder: a pack.mcmeta declaring its overlays, and their files."""
    os.makedirs(root)
    with open(os.path.join(root, "pack.mcmeta"), "w") as handle:
        json.dump(mcmeta or {"pack": {"description": "vendor overlays"}}, handle)
    for name, text in (files or {}).items():
        path = os.path.join(root, *name.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as handle:
            handle.write(text)


def run_main(workspace, plugin_paths, vendor_overlays):
    """Run merge_dev_pack.main() over `workspace`/dist and the given sources."""
    driver = ("import merge_dev_pack as m;"
              "m.RP = %r;"
              "m.SOURCES = %r;"
              "m.VENDOR_OVERLAYS = %r;"
              "m.main()" % (workspace, plugin_paths, vendor_overlays))
    return subprocess.run([sys.executable, "-c", driver], capture_output=True, text=True,
                          env=dict(os.environ, PYTHONPATH=HERE), cwd=HERE)


def write_zip(path, mcmeta, *entries, files=None):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("pack.mcmeta", json.dumps(mcmeta))
        for entry in entries:
            archive.writestr(entry, "{}")
        for name, text in (files or {}).items():
            archive.writestr(name, text)


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
        for name, mcmeta, files in (("mythicarmors", MYTHICARMORS_MCMETA, None),
                                    ("betterhud", BETTERHUD_MCMETA, None),
                                    ("future", FUTURE_ONLY_MCMETA, None),
                                    ("importing", IMPORTING_MCMETA, IMPORTING_FILES),
                                    ("base", BASE_MCMETA, None)):
            path = os.path.join(self.workspace, "%s.zip" % name)
            write_zip(path, mcmeta, "assets/%s/marker.json" % name, files=files)
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

    def test_an_importing_overlay_ends_below_the_rejecting_format_in_both_forms(self):
        overlays = self.overlays(self.merged()[0])
        self.assertEqual({"min_format": 84, "max_format": BELOW_REJECTING,
                          "formats": {"min_inclusive": 84, "max_inclusive": BELOW_REJECTING},
                          "directory": "vendor_importing"}, overlays["vendor_importing"])

    def test_an_importing_overlay_starting_at_the_rejecting_format_is_dropped(self):
        self.assertNotIn("vendor_importing_late", self.overlays(self.merged()[0]))

    def test_an_import_free_overlay_at_the_rejecting_format_is_unchanged(self):
        overlays = self.overlays(self.merged()[0])
        self.assertEqual(IMPORTING_MCMETA["overlays"]["entries"][2], overlays["vendor_including"])

    def test_the_merge_reports_the_import_bound(self):
        lines = self.merged()[1]
        for directory in ("vendor_importing", "vendor_importing_late"):
            named = [line for line in lines if (" %s:" % directory) in line]
            self.assertEqual(1, len(named), lines)
            self.assertIn("#moj_import", named[0])
            self.assertIn(str(BELOW_REJECTING), named[0])
        self.assertFalse([line for line in lines if " vendor_including:" in line], lines)

    def test_the_merged_pack_passes_the_overlay_shader_gate(self):
        entries, _ = merge_dev_pack.merge(self.sources)
        merged = os.path.join(self.workspace, "merged.zip")
        with zipfile.ZipFile(merged, "w") as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        result = subprocess.run([sys.executable, SHADER_GATE, "--pack", merged],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

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
        vendor_overlays = os.path.join(self.workspace, "vendor-overlays")
        write_vendor_overlays(vendor_overlays)
        result = run_main(self.workspace, self.sources[:-1], vendor_overlays)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for line in merge_dev_pack.merge(self.sources)[1]:
            self.assertIn(line, result.stdout)
        self.assertIn("future_only", result.stdout.split("overlays:")[0])


BETTERHUD_449 = os.path.join(HERE, "fixtures", "betterhud-449")
# A MythicArmors-generated pack: every overlay claims every format from its first.
MYTHICARMORS_PACK_MCMETA = {
    "pack": {"description": "MythicArmor 3D armor", "pack_format": 63, "min_format": 63,
             "max_format": UNBOUNDED, "supported_formats": [63, UNBOUNDED]},
    "overlays": {"entries": [
        {"min_format": low, "max_format": UNBOUNDED,
         "formats": {"min_inclusive": low, "max_inclusive": UNBOUNDED}, "directory": directory}
        for low, directory in ((63, "mythicarmors_1_21_6"), (84, "mythicarmors_26_1"),
                               (88, "mythicarmors_26_2"))]},
}
MYTHICARMORS_PACK_FILES = {
    "mythicarmors_1_21_6/" + CORE_SHADER: IMPORTING_SHADER,
    "mythicarmors_1_21_6/assets/minecraft/shaders/core/"
    "rendertype_item_entity_translucent_cull.vsh": IMPORTING_SHADER,
    "mythicarmors_1_21_6/assets/minecraft/shaders/include/mythicarmors_main.glsl": "isCustom = 0;\n",
    "mythicarmors_26_1/" + CORE_SHADER: IMPORTING_SHADER,
    "mythicarmors_26_2/" + CORE_SHADER: IMPORTING_SHADER,
}
VENDOR_OVERLAYS_MCMETA = {
    "pack": {"description": "vendor overlays"},
    "overlays": {"entries": [
        {"formats": [TESTED_MAX_FORMAT, TESTED_MAX_FORMAT], "min_format": TESTED_MAX_FORMAT,
         "max_format": TESTED_MAX_FORMAT, "directory": "mythicarmors_26_3"},
    ]},
}
VENDOR_OVERLAYS_FILES = {
    "mythicarmors_26_3/" + CORE_SHADER: INCLUDING_SHADER,
    "mythicarmors_26_3/assets/minecraft/shaders/core/entity.fsh": INCLUDING_SHADER,
    "mythicarmors_26_3/assets/minecraft/shaders/include/mythicarmors_main.glsl": "isCustom = 0;\n",
}
OUR_PACK_MCMETA = {
    "pack": {"pack_format": TESTED_MAX_FORMAT, "description": "ours", "min_format": 9,
             "max_format": TESTED_MAX_FORMAT, "supported_formats": [9, TESTED_MAX_FORMAT]},
    "overlays": {"entries": [
        {"formats": [TESTED_MAX_FORMAT, TESTED_MAX_FORMAT], "min_format": TESTED_MAX_FORMAT,
         "max_format": TESTED_MAX_FORMAT, "directory": "legendcraft_26_3"},
    ]},
}
VENDOR_26_3_OVERLAYS = ("betterhud_26_3", "mythicarmors_26_3")
OLDER_VENDOR_OVERLAYS = ("betterhud_1_21_4", "betterhud_1_21_6", "betterhud_26_1",
                         "betterhud_26_2", "mythicarmors_1_21_6", "mythicarmors_26_1",
                         "mythicarmors_26_2")
# The formats a 26.1 or 26.2 client reports: below the one that rejects `#moj_import`.
OLDER_CLIENT_FORMATS = range(84, MOJ_IMPORT_REJECTED_FORMAT)


def zip_tree(root, path):
    with zipfile.ZipFile(path, "w") as archive:
        for directory, _subdirs, files in os.walk(root):
            for name in files:
                full = os.path.join(directory, name)
                archive.write(full, os.path.relpath(full, root).replace(os.sep, "/"))


def client_view(entries, fmt):
    """What a client at `fmt` reads from a merged pack: the base section, the overlays it applies
    in order, and every file outside the overlays it does not apply."""
    meta = json.loads(entries["pack.mcmeta"])
    overlays = meta.get("overlays", {}).get("entries", [])
    applied = [e for e in overlays
               if any(low is not None and high is not None and low[0] <= fmt <= high[0]
                      for low, high in declared_ranges(e, OVERLAY_RANGE_KEY))]
    skipped = tuple("%s/" % e["directory"] for e in overlays if e not in applied)
    files = {name: data for name, data in entries.items()
             if name != "pack.mcmeta" and not name.startswith(skipped)}
    return meta["pack"], applied, files


class VendorOverlays26_3Test(unittest.TestCase):
    """The dev pack main() builds from a BetterHud pack that ships its own 26.3 overlay, a
    MythicArmors pack that does not, the vendor overlays folder and our pack."""

    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="vendor263-")
        self.addCleanup(shutil.rmtree, self.workspace, True)
        bettermodel = os.path.join(self.workspace, "bettermodel.zip")
        write_zip(bettermodel, {"pack": {"pack_format": 63, "description": "models"}},
                  "assets/bettermodel/marker.json")
        betterhud = os.path.join(self.workspace, "betterhud.zip")
        zip_tree(BETTERHUD_449, betterhud)
        mythicarmors = os.path.join(self.workspace, "mythicarmors.zip")
        write_zip(mythicarmors, MYTHICARMORS_PACK_MCMETA, "assets/mythicarmors/marker.json",
                  files=MYTHICARMORS_PACK_FILES)
        self.plugin_paths = [bettermodel, betterhud, mythicarmors]
        self.vendor_overlays = os.path.join(self.workspace, "vendor-overlays")
        write_vendor_overlays(self.vendor_overlays, VENDOR_OVERLAYS_MCMETA, VENDOR_OVERLAYS_FILES)
        self.dist = os.path.join(self.workspace, "dist")
        os.makedirs(self.dist)
        self.our_pack = os.path.join(self.dist, "LegendCraft-Pack-9.9.9.zip")
        write_zip(self.our_pack, OUR_PACK_MCMETA, "assets/legendcraft/marker.json",
                  files={"legendcraft_26_3/assets/minecraft/shaders/core/item.vsh":
                         INCLUDING_SHADER})
        self.dev_pack = os.path.join(self.dist, "LegendCraft-Pack-dev.zip")

    def build(self):
        result = run_main(self.workspace, self.plugin_paths, self.vendor_overlays)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        with zipfile.ZipFile(self.dev_pack) as archive:
            entries = {n: archive.read(n) for n in archive.namelist() if not n.endswith("/")}
        return entries, result.stdout

    def overlays(self, entries):
        meta = json.loads(entries["pack.mcmeta"])
        return {e["directory"]: e for e in meta.get("overlays", {}).get("entries", [])}

    def test_the_dev_pack_carries_a_26_3_overlay_for_each_vendor(self):
        overlays = self.overlays(self.build()[0])
        for directory in VENDOR_26_3_OVERLAYS:
            self.assertIn(directory, overlays)
            ranges = declared_ranges(overlays[directory], OVERLAY_RANGE_KEY)
            self.assertEqual(2, len(ranges), overlays[directory])
            for low, high in ranges:
                self.assertEqual((TESTED_MAX_FORMAT, TESTED_MAX_FORMAT), (low[0], high[0]),
                                 directory)

    def test_each_26_3_vendor_overlay_carries_core_shaders_without_moj_import(self):
        entries = self.build()[0]
        for directory in VENDOR_26_3_OVERLAYS:
            shaders = core_shaders([directory], entries)
            self.assertTrue(shaders, directory)
            self.assertEqual([], [n for n in shaders if MOJ_IMPORT in entries[n]])

    def test_the_dev_pack_passes_the_overlay_shader_gate(self):
        entries = self.build()[0]
        self.assertIn("mythicarmors_26_3", self.overlays(entries))
        result = subprocess.run([sys.executable, SHADER_GATE, "--pack", self.dev_pack],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_the_vendors_older_overlays_end_below_the_rejecting_format(self):
        overlays = self.overlays(self.build()[0])
        for directory in OLDER_VENDOR_OVERLAYS:
            self.assertIn(directory, overlays)
            for _, high in declared_ranges(overlays[directory], OVERLAY_RANGE_KEY):
                self.assertLess(high[0], MOJ_IMPORT_REJECTED_FORMAT, directory)

    def test_an_older_client_is_served_what_it_is_served_without_the_vendor_overlays(self):
        after, printed = self.build()
        before, report = merge_dev_pack.merge(self.plugin_paths + [self.our_pack])
        for fmt in OLDER_CLIENT_FORMATS:
            self.assertEqual(client_view(before, fmt), client_view(after, fmt), fmt)
        printed_report = [line for line in printed.splitlines()
                          if line.startswith(("clamped", "dropped"))]
        self.assertEqual(report, printed_report)

    def test_main_stops_naming_an_absent_vendor_overlays_folder(self):
        absent = os.path.join(self.workspace, "no-such-folder")
        result = run_main(self.workspace, self.plugin_paths, absent)
        self.assertNotEqual(0, result.returncode, result.stdout)
        self.assertIn("no-such-folder", result.stdout + result.stderr)

    def test_a_vendor_overlays_directory_it_cannot_list_stops_the_merge(self):
        unreadable = os.path.normcase(os.path.join(self.vendor_overlays, "mythicarmors_26_3"))
        listing = os.scandir

        def scandir(path="."):
            if os.path.normcase(os.path.abspath(os.fspath(path))) == unreadable:
                raise PermissionError(13, "Permission denied", path)
            return listing(path)
        with mock.patch("os.scandir", scandir):
            with self.assertRaises(OSError):
                merge_dev_pack.merge(self.plugin_paths + [self.vendor_overlays, self.our_pack])


if __name__ == "__main__":
    unittest.main()
