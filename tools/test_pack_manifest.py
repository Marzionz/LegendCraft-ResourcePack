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

# The audit's subjects, one file of each kind the gate counts.
ITEM_MODELS = ("assets/legendcraft/items/classes/alpha.json",
               "assets/legendcraft/items/classes/beta.json",
               "assets/legendcraft/items/economy/marks.json")
SOUND_FILES = ("assets/legendcraft_sounds/sounds/one.ogg",)
SOUND_INDEX = "assets/legendcraft_sounds/sounds.json"
# The namespace directory arm 2 hides. It holds an item model, so its loss is countable.
HIDDEN_NAMESPACE = "assets/legendcraft/items/economy"

BASE_MCMETA = {"pack": {"pack_format": 84, "description": "fixture"}}
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


def plugin_zip(out_path, entries):
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("pack.mcmeta", json.dumps(PLUGIN_MCMETA))
        archive.writestr("pack.png", "")
        for entry in entries:
            archive.writestr(entry, "{}")


def audit(pack, source_tree, plugin_sources=()):
    argv = [sys.executable, AUDITOR, "--pack", pack, "--source-tree", source_tree]
    for plugin_source in plugin_sources:
        argv += ["--plugin-source", plugin_source]
    return subprocess.run(argv, capture_output=True, text=True)


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

    def merge(self, source_tree=None, also_older_from=None):
        """Run the real merger over this fixture, returning the merged pack's path.

        `also_older_from` writes a LOWER-versioned base pack from a second tree, so the merge
        has a real choice to get wrong.
        """
        if also_older_from is not None:
            zip_tree(also_older_from,
                     os.path.join(self.dist, "LegendCraft-Pack-1.0.0.zip"), BASE_MCMETA)
        zip_tree(source_tree or self.source_tree,
                 os.path.join(self.dist, "LegendCraft-Pack-9.9.9.zip"), BASE_MCMETA)
        env = dict(os.environ)
        env["PYTHONPATH"] = HERE
        driver = (
            "import merge_dev_pack as m;"
            "m.RP = %r;"
            "m.SOURCES = %r;"
            "m.main()" % (self.workspace, self.plugin_paths)
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


if __name__ == "__main__":
    unittest.main()
