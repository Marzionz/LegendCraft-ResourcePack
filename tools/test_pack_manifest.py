"""Acceptance suite for the pack manifest gate, run in CI.

The gate's subject is the merge that produces the served pack, and the merge reads two plugin
build zips that only exist on the server box. This suite therefore builds its own: a base pack
zipped from a synthetic source tree, plus stand-ins for the two plugin builds. That is enough
to run the real merge_dev_pack code and audit its real output.

Acceptance criteria:
1. A merge over a complete base pack passes the manifest audit.
2. Hiding one namespace directory before the merge fails the audit, naming what was lost.
3. A plugin build zip whose entries do not survive the merge fails the audit.
4. The audit reports the plugin half as unchecked rather than passing when given no source.
5. With more than one built base pack on disk the merge takes the NEWEST. This is the defect
   that shipped: the merge that produced the served pack resolved a stale base, so content
   added since was absent from every pin with no repository change behind it. Arms 1-4 all
   pass against a merge that picks any base at all, because one pack is both the newest and
   the oldest.

The manifest half, added after a second silent loss. From pack_format 80 the client REQUIRES
`min_format` and `max_format` beside `pack_format`; given only `pack_format` it logs one line
-- "Error reading pack metadata, attempting fallback type" -- and then discards every overlay
in the pack. BetterHud ships its shader cores only inside overlays, so the pack loads, the art
loads, and the HUD's shaders are silently not there. Nothing about that reads as a manifest
problem, and this gate was counting entries while the three keys that decide whether they are
applied at all went unread.

6. A merged pack whose manifest carries `pack_format` alone is refused, naming both absent
   keys.
7. A manifest whose `pack_format` sits outside `min_format`..`max_format` is refused -- three
   keys present is not three keys agreeing.
8. A manifest BELOW the floor is not required to carry them: the requirement is the client's,
   and it starts at 80.
9. `--manifest-only` audits a source tree's own `pack.mcmeta` with no merged pack, which is
   what CI can run -- the merge's inputs only exist on the server box. The merge copies our
   `pack.mcmeta` into the output verbatim, so the source tree is where the defect is.
10. This repo's real `src/pack.mcmeta` passes. (The two-sided control: without it, 6-9 pass
    against a gate that refuses every manifest.)

The range half. A client applies an overlay on the range it declares, so a range reaching past
TESTED_MAX_FORMAT hands a newer client shaders nobody ran on it, and one it cannot compile
rejects the whole pack.

11. A manifest whose overlay range, in either form, ends above TESTED_MAX_FORMAT is refused,
    naming the overlay.
12. A manifest whose base range ends above TESTED_MAX_FORMAT is refused.
13. A manifest whose overlay range starts above its own end is refused, naming the overlay.
14. A merge over plugin packs declaring overlays to format 65535 passes: the merge bounds them.
15. A built pack whose manifest still carries such an overlay is refused under --pack.
16. A [major, minor] range is ordered by minor within a major: `TESTED.2..TESTED.1` is refused,
    `TESTED.1..TESTED.2` passes.

    python tools/test_pack_manifest.py
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
REPO_ROOT = os.path.dirname(HERE)
AUDITOR = os.path.join(HERE, "check_pack_manifest.py")
MERGER = os.path.join(HERE, "merge_dev_pack.py")
sys.path.insert(0, HERE)

from pack_formats import TESTED_MAX_FORMAT  # noqa: E402

# The audit's subjects, one file of each kind the gate counts.
ITEM_MODELS = ("assets/legendcraft/items/classes/alpha.json",
               "assets/legendcraft/items/classes/beta.json",
               "assets/legendcraft/items/economy/marks.json")
SOUND_FILES = ("assets/legendcraft_sounds/sounds/one.ogg",)
SOUND_INDEX = "assets/legendcraft_sounds/sounds.json"
# The namespace directory arm 2 hides. It holds an item model, so its loss is countable.
HIDDEN_NAMESPACE = "assets/legendcraft/items/economy"

# From pack_format 80 the client wants the format triple, so the fixture standing in for a
# healthy pack carries one; the others are the shapes that get discarded.
BASE_MCMETA = {"pack": {"pack_format": 84, "min_format": 9, "max_format": 84,
                        "description": "fixture"}}
NO_TRIPLE_MCMETA = {"pack": {"pack_format": 84, "description": "fixture"}}
DISAGREEING_MCMETA = {"pack": {"pack_format": 84, "min_format": 85, "max_format": 99,
                               "description": "fixture"}}
BELOW_FLOOR_MCMETA = {"pack": {"pack_format": 34, "description": "fixture"}}
REAL_SOURCE_TREE = os.path.join(REPO_ROOT, "src")
UNBOUNDED = 65535
BEYOND_TESTED = TESTED_MAX_FORMAT + 1
UNBOUNDED_OVERLAY = {"min_format": 84, "max_format": UNBOUNDED,
                     "formats": {"min_inclusive": 84, "max_inclusive": UNBOUNDED},
                     "directory": "mythicarmors_26_1"}
FORMATS_ONLY_BEYOND_OVERLAY = {"formats": [84, BEYOND_TESTED], "min_format": 84,
                               "max_format": TESTED_MAX_FORMAT, "directory": "betterhud_26_1"}
MINOR_INVERTED_OVERLAY = {"min_format": [TESTED_MAX_FORMAT, 2],
                          "max_format": [TESTED_MAX_FORMAT, 1], "directory": "minor_inverted"}
MINOR_ORDERED_OVERLAY = {"min_format": [TESTED_MAX_FORMAT, 1],
                         "max_format": [TESTED_MAX_FORMAT, 2], "directory": "minor_ordered"}
INVERTED_OVERLAY = {"formats": [TESTED_MAX_FORMAT, 84], "min_format": TESTED_MAX_FORMAT,
                    "max_format": 84, "directory": "inverted"}
UNBOUNDED_BASE_MCMETA = {"pack": {"pack_format": 84, "min_format": 9, "max_format": 84,
                                  "supported_formats": [9, UNBOUNDED], "description": "fixture"}}
UNBOUNDED_PLUGIN_MCMETA = {"pack": {"pack_format": 63, "min_format": 63, "max_format": UNBOUNDED,
                                    "description": "armour"},
                           "overlays": {"entries": [UNBOUNDED_OVERLAY]}}


def with_overlays(*entries):
    return dict(BASE_MCMETA, overlays={"entries": list(entries)})
PLUGIN_MCMETA = {"pack": {"pack_format": 84, "description": "plugin"},
                 "overlays": {"entries": [{"directory": "betterhud_26_1",
                                           "formats": {"min_inclusive": 84,
                                                       "max_inclusive": 99}}]}}
PLUGIN_ENTRIES = {
    "betterhud": ("assets/betterhud/font/default.json",
                  "assets/betterhud/textures/glyph.png"),
    "bettermodel": ("assets/bettermodel/models/rig.json",),
}


def write_tree(root, entries):
    for entry in entries:
        path = os.path.join(root, *entry.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{}")


def zip_tree(root, out_path, mcmeta):
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("pack.mcmeta", json.dumps(mcmeta))
        archive.writestr("pack.png", "")
        for directory, _subdirs, names in os.walk(root):
            for name in names:
                full = os.path.join(directory, name)
                archive.write(full, os.path.relpath(full, root).replace(os.sep, "/"))


def plugin_zip(out_path, entries, mcmeta=PLUGIN_MCMETA):
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("pack.mcmeta", json.dumps(mcmeta))
        archive.writestr("pack.png", "")
        for entry in entries:
            archive.writestr(entry, "{}")


def audit(pack, source_tree, plugin_sources=()):
    argv = [sys.executable, AUDITOR, "--pack", pack, "--source-tree", source_tree]
    for plugin_source in plugin_sources:
        argv += ["--plugin-source", plugin_source]
    return subprocess.run(argv, capture_output=True, text=True)


def audit_manifest(source_tree):
    return subprocess.run(
        [sys.executable, AUDITOR, "--manifest-only", "--source-tree", source_tree],
        capture_output=True, text=True)


class PackManifestTest(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="packmanifest-")
        self.addCleanup(shutil.rmtree, self.workspace, True)
        self.source_tree = os.path.join(self.workspace, "src")
        write_tree(self.source_tree, ITEM_MODELS + SOUND_FILES + (SOUND_INDEX,))
        self.dist = os.path.join(self.workspace, "dist")
        os.makedirs(self.dist)
        self.plugin_paths = []
        for name, entries in PLUGIN_ENTRIES.items():
            path = os.path.join(self.workspace, "%s-build.zip" % name)
            plugin_zip(path, entries)
            self.plugin_paths.append(path)
        self.vendor_overlays = os.path.join(self.workspace, "vendor-overlays")
        os.makedirs(self.vendor_overlays)
        with open(os.path.join(self.vendor_overlays, "pack.mcmeta"), "w") as handle:
            json.dump({"pack": {"description": "vendor overlays"}}, handle)

    def with_mcmeta(self, mcmeta):
        """A source tree holding one pack.mcmeta, for the manifest-only arms."""
        tree = os.path.join(self.workspace, "src-%d" % len(os.listdir(self.workspace)))
        os.makedirs(tree)
        with open(os.path.join(tree, "pack.mcmeta"), "w", encoding="utf-8") as handle:
            json.dump(mcmeta, handle)
        return tree

    def merge(self, source_tree=None, also_older_from=None, mcmeta=BASE_MCMETA):
        """Run the real merger over this fixture, returning the merged pack's path.

        `also_older_from` writes a LOWER-versioned base pack from a second tree, so the merge
        has a real choice to get wrong.
        """
        if also_older_from is not None:
            zip_tree(also_older_from,
                     os.path.join(self.dist, "LegendCraft-Pack-1.0.0.zip"), mcmeta)
        zip_tree(source_tree or self.source_tree,
                 os.path.join(self.dist, "LegendCraft-Pack-9.9.9.zip"), mcmeta)
        env = dict(os.environ)
        env["PYTHONPATH"] = HERE
        driver = (
            "import merge_dev_pack as m;"
            "m.RP = %r;"
            "m.SOURCES = %r;"
            "m.VENDOR_OVERLAYS = %r;"
            "m.main()" % (self.workspace, self.plugin_paths, self.vendor_overlays)
        )
        result = subprocess.run([sys.executable, "-c", driver],
                                capture_output=True, text=True, env=env, cwd=HERE)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return os.path.join(self.dist, "LegendCraft-Pack-dev.zip")

    def test_a_complete_merge_passes_the_audit(self):
        merged = self.merge()
        result = audit(merged, self.source_tree, self.plugin_paths)
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("carries 3 item model(s), 1 sound(s), 1 sounds.json", result.stdout)

    def test_hiding_a_namespace_directory_before_the_merge_fails_the_audit(self):
        staged = os.path.join(self.workspace, "src-staged")
        shutil.copytree(self.source_tree, staged)
        shutil.rmtree(os.path.join(staged, *HIDDEN_NAMESPACE.split("/")))
        merged = self.merge(source_tree=staged)
        result = audit(merged, self.source_tree, self.plugin_paths)
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("1 item model(s) in the source tree are absent", result.stdout)
        self.assertIn("assets/legendcraft/items/economy/marks.json", result.stdout)

    def test_a_plugin_entry_lost_in_the_merge_fails_the_audit(self):
        merged = self.merge()
        phantom = os.path.join(self.workspace, "phantom-build.zip")
        plugin_zip(phantom, ("assets/betterhud/textures/never_merged.png",))
        result = audit(merged, self.source_tree, [phantom])
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("did not survive the merge", result.stdout)

    def test_the_merge_takes_the_newest_built_base_and_not_a_stale_one(self):
        stale = os.path.join(self.workspace, "src-stale")
        shutil.copytree(self.source_tree, stale)
        shutil.rmtree(os.path.join(stale, *HIDDEN_NAMESPACE.split("/")))
        merged = self.merge(also_older_from=stale)
        result = audit(merged, self.source_tree, self.plugin_paths)
        self.assertEqual(0, result.returncode,
                         "the merge resolved the older base and dropped content:\n" + result.stdout)

    def test_the_plugin_half_reports_itself_unchecked_rather_than_passing(self):
        merged = self.merge()
        result = audit(merged, self.source_tree)
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("UNCHECKED", result.stdout)

    def test_a_merged_pack_carrying_pack_format_alone_is_refused(self):
        merged = self.merge(mcmeta=NO_TRIPLE_MCMETA)
        result = audit(merged, self.source_tree, self.plugin_paths)
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("min_format", result.stdout)
        self.assertIn("max_format", result.stdout)

    def test_a_manifest_whose_pack_format_sits_outside_its_own_range_is_refused(self):
        result = audit_manifest(self.with_mcmeta(DISAGREEING_MCMETA))
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("outside", result.stdout)

    def test_a_manifest_below_the_floor_needs_no_triple(self):
        result = audit_manifest(self.with_mcmeta(BELOW_FLOOR_MCMETA))
        self.assertEqual(0, result.returncode, result.stdout)

    def test_manifest_only_refuses_a_source_tree_that_lost_the_triple(self):
        result = audit_manifest(self.with_mcmeta(NO_TRIPLE_MCMETA))
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("pack.mcmeta", result.stdout)

    def test_manifest_only_passes_a_source_tree_that_carries_it(self):
        result = audit_manifest(self.with_mcmeta(BASE_MCMETA))
        self.assertEqual(0, result.returncode, result.stdout)

    def test_an_overlay_range_ending_above_the_tested_format_is_refused(self):
        for overlay in (UNBOUNDED_OVERLAY, FORMATS_ONLY_BEYOND_OVERLAY):
            result = audit_manifest(self.with_mcmeta(with_overlays(overlay)))
            self.assertEqual(1, result.returncode, result.stdout)
            self.assertIn(overlay["directory"], result.stdout)

    def test_a_base_range_ending_above_the_tested_format_is_refused(self):
        result = audit_manifest(self.with_mcmeta(UNBOUNDED_BASE_MCMETA))
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn(str(UNBOUNDED), result.stdout)

    def test_an_overlay_range_starting_above_its_end_is_refused(self):
        result = audit_manifest(self.with_mcmeta(with_overlays(INVERTED_OVERLAY)))
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("inverted", result.stdout)

    def test_a_minor_version_range_starting_above_its_end_is_refused(self):
        result = audit_manifest(self.with_mcmeta(with_overlays(MINOR_INVERTED_OVERLAY)))
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("minor_inverted", result.stdout)

    def test_a_minor_version_range_in_order_passes(self):
        result = audit_manifest(self.with_mcmeta(with_overlays(MINOR_ORDERED_OVERLAY)))
        self.assertEqual(0, result.returncode, result.stdout)

    def test_a_merge_over_unbounded_plugin_overlays_passes(self):
        unbounded = os.path.join(self.workspace, "mythicarmors-pack.zip")
        plugin_zip(unbounded, ("assets/mythicarmors/models/armour.json",), UNBOUNDED_PLUGIN_MCMETA)
        self.plugin_paths.append(unbounded)
        merged = self.merge()
        result = audit(merged, self.source_tree, self.plugin_paths)
        self.assertEqual(0, result.returncode, result.stdout)

    def test_a_built_pack_still_carrying_an_unbounded_overlay_is_refused(self):
        pack = os.path.join(self.dist, "LegendCraft-Pack-dev.zip")
        zip_tree(self.source_tree, pack, with_overlays(UNBOUNDED_OVERLAY))
        result = audit(pack, self.source_tree)
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn(UNBOUNDED_OVERLAY["directory"], result.stdout)


class TheRealSourceTreeStillPassesTest(unittest.TestCase):
    """The manifest rules must not refuse the pack.mcmeta this repo actually ships."""

    def test_the_committed_manifest_passes(self):
        result = audit_manifest(REAL_SOURCE_TREE)
        self.assertEqual(0, result.returncode, result.stdout)


if __name__ == "__main__":
    unittest.main()
