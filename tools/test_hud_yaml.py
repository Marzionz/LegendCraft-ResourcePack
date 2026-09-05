"""Acceptance suite for the BetterHud YAML gate's pattern rules, run in CI.

BetterHud 2.1.0-447's text parser EATS a single `/` in a `pattern:` string, and the literal
in front of it fuses onto the next placeholder token: `"HP/[papi:x]"` comes back as
`this placeholder not found: HP[papi`, and the whole hud -- every other element with it --
does not load. The structure that survives is a `//` run with a colour tag on each side, so
one slash is eaten and the other renders.

`generate_hud.py` has carried that workaround as `SEP` since the stat block was written. The
party layout is hand-authored and had nothing to inherit it from, so it shipped the bare form
and refused `lc_stat_hud` for three days -- found by hand at the box, one reload at a time,
with the log naming a placeholder that was never missing.

The gate therefore walks EVERY `pattern:` in the tree, at any depth and in any file kind, not
the four rows the outage was found in.

Acceptance criteria:
1. The SEP form -- a `//` run with a colour tag on each side -- passes.
2. A bare `/` between two placeholders is refused, naming the file and the element.
3. A `//` run with no colour tag BEFORE it is refused. (The literal that fuses is the one in
   front of the slash, so this is the side the outage was on.)
4. A `//` run with no colour tag AFTER it is refused.
5. A run of three or more slashes is refused: one is eaten, and what is left is not `//`.
6. A pattern in a file kind the shape checks do not read -- `texts/` -- is still refused, so
   the walk is over the tree and not over the three directories the older checks list.
7. The committed tree passes. (The two-sided control: without it, 2-6 pass against a gate
   that refuses every pattern.)

    python tools/test_hud_yaml.py
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
CHECKER = os.path.join(HERE, "check_hud_yaml.py")
REAL_HUD_ROOT = os.path.join(REPO_ROOT, "hud", "betterhud")

# A minimal layout carrying exactly one text element, so a run's verdict is about that one
# pattern and nothing else. Shaped like the real hand-authored party rows: same sections, same
# required keys, so every shape check the gate already runs passes and only the pattern rule
# can produce a refusal.
LAYOUT_TEMPLATE = """lc_probe:
  texts:
    1:
      name: lc_stat_text
      pattern: "%s"
      align: center
      x: 0
      y: 0
      layer: 8
"""

# The same one pattern, in a directory the registry/layout/hud shape checks never open.
TEXTS_TEMPLATE = """lc_probe_text:
  merge-default-bitmap: true
  children:
    1:
      pattern: "%s"
"""

SEP = "<gray> // <white>"
GOOD_PATTERN = "<white>[papi:legendcraft_health]%s[papi:legendcraft_max_health]" % SEP
BARE_SLASH_PATTERN = "<white>[papi:legendcraft_health]/[papi:legendcraft_max_health]"
NO_TAG_BEFORE_PATTERN = "<white>[papi:legendcraft_health] // <white>[papi:legendcraft_max_health]"
NO_TAG_AFTER_PATTERN = "<white>[papi:legendcraft_health]<gray> // [papi:legendcraft_max_health]"
TRIPLE_SLASH_PATTERN = "<white>[papi:legendcraft_health]<gray> /// <white>[papi:legendcraft_max_health]"


class PatternSlashGateTest(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="hudyaml-")
        self.addCleanup(shutil.rmtree, self.workspace, True)
        self.hud_root = os.path.join(self.workspace, "betterhud")
        for subdir in ("layouts", "texts"):
            os.makedirs(os.path.join(self.hud_root, subdir))

    def verdict(self, pattern, subdir="layouts", template=LAYOUT_TEMPLATE):
        """Write one probe file carrying `pattern`, and run the real gate over the fixture.

        The layout probe is always written: it is what makes the fixture a tree the gate
        counts, so a run that reports "checked nothing" cannot be mistaken for a pass.
        """
        layout = os.path.join(self.hud_root, "layouts", "probe.yml")
        with open(layout, "w", encoding="utf-8") as handle:
            handle.write(LAYOUT_TEMPLATE % (GOOD_PATTERN if subdir != "layouts" else pattern))
        if subdir != "layouts":
            path = os.path.join(self.hud_root, subdir, "probe.yml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(template % pattern)
        result = subprocess.run([sys.executable, CHECKER, "--hud-root", self.hud_root],
                                capture_output=True, text=True)
        return result.returncode, result.stdout

    def assertAccepted(self, pattern, **kwargs):
        code, out = self.verdict(pattern, **kwargs)
        self.assertEqual(0, code, "%r should pass:\n%s" % (pattern, out))

    def assertRefused(self, pattern, **kwargs):
        code, out = self.verdict(pattern, **kwargs)
        self.assertEqual(1, code, "%r should be refused but passed:\n%s" % (pattern, out))
        self.assertIn("probe.yml", out)
        return out

    def test_the_separator_the_generator_writes_passes(self):
        self.assertAccepted(GOOD_PATTERN)

    def test_a_bare_slash_between_two_placeholders_is_refused(self):
        out = self.assertRefused(BARE_SLASH_PATTERN)
        self.assertIn("lc_probe.texts.1.pattern", out)

    def test_a_separator_with_no_tag_before_it_is_refused(self):
        self.assertRefused(NO_TAG_BEFORE_PATTERN)

    def test_a_separator_with_no_tag_after_it_is_refused(self):
        self.assertRefused(NO_TAG_AFTER_PATTERN)

    def test_a_run_of_three_slashes_is_refused(self):
        self.assertRefused(TRIPLE_SLASH_PATTERN)

    def test_a_pattern_outside_the_layout_directories_is_refused_too(self):
        self.assertRefused(BARE_SLASH_PATTERN, subdir="texts", template=TEXTS_TEMPLATE)


class TheRealTreeStillPassesTest(unittest.TestCase):
    """The pattern rule must not start refusing rows the shipped HUD actually draws."""

    def test_the_committed_hud_passes(self):
        result = subprocess.run([sys.executable, CHECKER, "--hud-root", REAL_HUD_ROOT],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout)


if __name__ == "__main__":
    unittest.main()
