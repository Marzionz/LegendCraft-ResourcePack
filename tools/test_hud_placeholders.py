"""Acceptance suite for the placeholder gate, run in CI.

The gate's whole job is to refuse an id the plugin does not answer. An id it wrongly ACCEPTS
is the failure that costs a HUD row, and it is invisible: the expansion returns null, so
PlaceholderAPI leaves the raw token in the string, the element's condition never matches, and
the row silently does not render.

The expansion answers three shapes, and they are not interchangeable:
  a bare id           the labels of the two switches over `params`
  a slot family id    a `slotN_`/`ult_` prefix plus one of the labels of the switches over
                      `field` inside slotField
  a party family id   `party_member_<n>`, bounded by the projection's own slot count

Acceptance criteria:
1. A real field label on a slot prefix is answered.
2. A field label used as a BARE id is refused - `cd_secs` alone names no case.
3. A real stat id used as a SLOT FIELD is refused - `slot1_armor` names no case.
4. A bare stat id is answered, and a made-up one is refused. (The two-sided control: without
   it, criteria 2 and 3 pass against a checker that refuses everything.)

    python tools/test_hud_placeholders.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
CHECKER = os.path.join(HERE, "check_hud_placeholders.py")
CLASSES_ROOT = os.path.join(os.path.dirname(REPO_ROOT), "LegendCraft-Classes")
REAL_HUD_ROOT = os.path.join(REPO_ROOT, "hud", "betterhud")

# A minimal layout carrying exactly one placeholder, so a run's verdict is about that id and
# nothing else. Shaped like the real layouts the gate reads.
LAYOUT_TEMPLATE = """lc_probe:
  images:
    1:
      name: lc_bar_empty
      x: 0
      y: 0
      layer: 1
      conditions:
        1:
          first: "papi:legendcraft_%s"
          second: "'1'"
          operation: '=='
"""


class PlaceholderGateTest(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="hudplaceholders-")
        self.addCleanup(shutil.rmtree, self.workspace, True)
        self.hud_root = os.path.join(self.workspace, "betterhud")
        os.makedirs(os.path.join(self.hud_root, "layouts"))

    def verdict(self, placeholder_id):
        path = os.path.join(self.hud_root, "layouts", "probe.yml")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(LAYOUT_TEMPLATE % placeholder_id)
        result = subprocess.run(
            [sys.executable, CHECKER, "--classes-root", CLASSES_ROOT, "--hud-root", self.hud_root],
            capture_output=True, text=True)
        return result.returncode, result.stdout

    def assertAnswered(self, placeholder_id):
        code, out = self.verdict(placeholder_id)
        self.assertEqual(0, code, "%s should be answered:\n%s" % (placeholder_id, out))

    def assertRefused(self, placeholder_id):
        code, out = self.verdict(placeholder_id)
        self.assertEqual(1, code, "%s should be refused but was accepted:\n%s"
                         % (placeholder_id, out))
        self.assertIn("names no case in HudPlaceholders", out)

    def test_a_field_label_on_a_slot_prefix_is_answered(self):
        for placeholder_id in ("slot1_state", "slot2_cd_percent", "ult_charges"):
            self.assertAnswered(placeholder_id)

    def test_a_field_label_used_as_a_bare_id_is_refused(self):
        # `cd_secs` and `charges` are labels of slotField's switch over `field`. Nothing answers
        # them on their own, so the union of both label sets is not a legal set of bare ids.
        for placeholder_id in ("cd_secs", "charges", "is_charge", "max_charges"):
            self.assertRefused(placeholder_id)

    def test_a_stat_id_used_as_a_slot_field_is_refused(self):
        # `armor`, `level` and `resource_type` are answered as bare ids by the switches over
        # `params`. On a slot prefix nothing answers them, and this is the typo a person is
        # most likely to make: a real name on the wrong family.
        for placeholder_id in ("slot1_armor", "slot2_level", "ult_resource_type"):
            self.assertRefused(placeholder_id)

    def test_a_real_bare_id_is_answered_and_an_invented_one_is_refused(self):
        self.assertAnswered("armor")
        self.assertAnswered("subclass")
        self.assertRefused("armour")
        self.assertRefused("slot1_bogus")


class TheRealTreeStillPassesTest(unittest.TestCase):
    """The tightened rules must not start refusing ids the shipped HUD actually reads."""

    def test_the_committed_hud_passes(self):
        result = subprocess.run(
            [sys.executable, CHECKER, "--classes-root", CLASSES_ROOT, "--hud-root", REAL_HUD_ROOT],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout)


if __name__ == "__main__":
    unittest.main()
