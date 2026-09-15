"""Skill-card asset generator acceptance suite.

Run from the repository root:
    python tools/test_generate_skill_cards.py

Acceptance criteria:
1. The Bloodweaver ultimate frame carries blood.svg's pixels, rasterized by pixel centre, with its
   top-left cell at (12, 11) and its horizontal mirror's right column at x = width - 13, in every
   animation frame; the two base layers are identical in every frame.
2. The veins pulse on a 3.2 s (64-tick) loop: root, branch and tip each swing between 0.3 and
   full opacity, peaking root first, then branch and tip 0.16 s (3 ticks) apart.
3. Both frames are nine-slice sprites whose corner cells hold every ornament pixel, whose reading
   area is transparent in every frame, and whose edges stretch rather than tile.
4. The common card frame carries no ornament: nothing drawn outside its three edge rings.
5. Panel colours are the website's colour mixes: border 60% accent into #463448, fill top 11%
   accent into #100911 fading to #110A16; the ultimate border is the class title end and its
   second inner ring is 25% accent into #352231.
6. The marks font maps mana, health, cooldown, open and close bracket to U+E000..U+E004 in one
   bitmap of 8x8 cells, height 8, ascent 7; each glyph is white-only, and advances 8, 8, 8, 5, 5.
7. The committed assets equal what the generator writes.
"""

from pathlib import Path
import io
import json
import re
import tempfile
import unittest

from PIL import Image

import generate_skill_cards as gen


REPO_ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = Path(__file__).resolve().parent / "skill_card_art" / "blood.svg"

SPRITES = "assets/legendcraft/textures/gui/sprites/tooltip/classes"
COMMON = SPRITES + "/skill_card"
ULTIMATE = SPRITES + "/skill_card_ultimate_bloodweaver"
FONT_JSON = "assets/legendcraft/font/classes/skill_card.json"
FONT_PNG = "assets/legendcraft/textures/font/classes/skill_card_marks.png"
FONT_FILE_ID = "legendcraft:font/classes/skill_card_marks.png"

ORNAMENT_LEFT = (12, 11)
ORNAMENT_RIGHT_INSET = 13
ORNAMENT_SIZE = 24

COMMON_ACCENT = "#AA55FF"
BLOODWEAVER_ACCENT = "#FF1744"
BLOODWEAVER_TITLE_END = "#FF5173"
PANEL_BORDER_BASE, PANEL_BORDER_ACCENT = "#463448", 0.60
PANEL_FILL_BASE, PANEL_FILL_ACCENT, PANEL_FILL_END = "#100911", 0.11, "#110A16"
ULTIMATE_RING_BASE, ULTIMATE_RING_ACCENT = "#352231", 0.25
PANEL_BORDER_INSET = 8

PULSE_PERIOD_TICKS = 64
PULSE_LOW, PULSE_HIGH = 0.3, 1.0
PULSE_STEP_TICKS = 3
VEIN_GROUPS = ("blood-root", "blood-branch", "blood-tip")

MARKS = ("\ue000", "\ue001", "\ue002", "\ue003", "\ue004")
MARK_ADVANCES = (8, 8, 8, 5, 5)
MARK_CELL = 8


def hex_rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def mix(accent, base, share):
    return tuple(int(a * share + b * (1 - share) + 0.5) for a, b in zip(hex_rgb(accent), hex_rgb(base)))


def svg_layers():
    """(fill, class or None, covered cells) per path, covered = pixel centre inside, nonzero."""
    layers = []
    for match in re.finditer(r'<path(?: class="([^"]+)")? fill="(#[0-9a-fA-F]{6})" d="([^"]+)"', SVG_PATH.read_text()):
        css_class, fill, d = match.groups()
        tokens = re.findall(r"[MHVZ]|-?\d+", d)
        assert set(t for t in tokens if t.isalpha()) <= set("MHVZ"), d
        polygons, points, i, x, y = [], [], 0, 0, 0
        while i < len(tokens):
            op = tokens[i]
            if op == "M":
                x, y = int(tokens[i + 1]), int(tokens[i + 2])
                points = [(x, y)]
                i += 3
            elif op == "H":
                x = int(tokens[i + 1])
                points.append((x, y))
                i += 2
            elif op == "V":
                y = int(tokens[i + 1])
                points.append((x, y))
                i += 2
            elif op == "Z":
                polygons.append(points)
                i += 1
            elif re.fullmatch(r"-?\d+", op):
                # An implicit repeat of the last H or V is not used by the art; refuse it loudly.
                raise AssertionError("implicit path command in " + d)
        cells = set()
        for cy in range(ORNAMENT_SIZE):
            for cx in range(ORNAMENT_SIZE):
                if winding(polygons, cx + 0.5, cy + 0.5) != 0:
                    cells.add((cx, cy))
        layers.append((hex_rgb(fill), css_class, cells))
    return layers


def winding(polygons, px, py):
    total = 0
    for poly in polygons:
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            if x0 != x1:
                continue
            if y0 <= py < y1 and px < x0:
                total += 1
            elif y1 <= py < y0 and px < x0:
                total -= 1
    return total


def frames_of(png, mcmeta):
    image = Image.open(png).convert("RGBA")
    meta = json.loads(mcmeta.read_text())
    width = image.width
    height = meta["gui"]["scaling"]["height"] if "animation" in meta else image.height
    count = image.height // height
    return [image.crop((0, k * height, width, (k + 1) * height)) for k in range(count)], meta


def opacity(pixel, fill, ground):
    """How much of ``fill`` a pixel shows: its alpha over empty ground, its blend over an opaque base."""
    if ground is None:
        return pixel[3] / 255
    channel = max(range(3), key=lambda i: abs(fill[i] - ground[i]))
    return (pixel[channel] - ground[channel]) / (fill[channel] - ground[channel])


def to_frame(cells, origin, mirrored, width):
    left, top = origin
    placed = set()
    for cx, cy in cells:
        x = (width - ORNAMENT_RIGHT_INSET - cx) if mirrored else (left + cx)
        placed.add((x, top + cy))
    return placed


class GeneratedTree:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        gen.build(self.root)

    def path(self, relative):
        return self.root / relative


class UltimateOrnamentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = GeneratedTree()

    def ultimate_frames(self):
        png = self.tree.path(ULTIMATE + "_frame.png")
        mcmeta = self.tree.path(ULTIMATE + "_frame.png.mcmeta")
        self.assertTrue(png.is_file() and mcmeta.is_file(), "ultimate frame sprite not written")
        return frames_of(png, mcmeta)

    def test_1_ornament_pixels_in_both_top_corners_every_frame(self):
        frames, _ = self.ultimate_frames()
        layers = svg_layers()
        base = [(fill, cells) for fill, css, cells in layers if css is None]
        animated_cells = set().union(*(cells for _, css, cells in layers if css is not None))
        every_cell = set().union(*(cells for _, _, cells in layers))
        width = frames[0].width
        for index, frame in enumerate(frames):
            for mirrored in (False, True):
                region = to_frame({(x, y) for x in range(ORNAMENT_SIZE) for y in range(1, ORNAMENT_SIZE)},
                                  ORNAMENT_LEFT, mirrored, width)
                drawn = {p for p in region if frame.getpixel(p)[3] != 0}
                self.assertEqual(to_frame({c for c in every_cell if c[1] >= 1}, ORNAMENT_LEFT, mirrored, width),
                                 drawn, "frame %d mirrored=%s ornament coverage" % (index, mirrored))
                for fill, cells in base:
                    for cell in cells - animated_cells:
                        (point,) = to_frame({cell}, ORNAMENT_LEFT, mirrored, width)
                        self.assertEqual(fill + (255,), frame.getpixel(point),
                                         "frame %d base layer at %s" % (index, point))

    def test_2_veins_pulse_on_a_staggered_64_tick_loop(self):
        frames, meta = self.ultimate_frames()
        animation = meta.get("animation", {})
        frametime = animation.get("frametime", 1)
        self.assertNotIn("frames", animation, "a custom frame order would decouple ticks from rows")
        self.assertEqual(PULSE_PERIOD_TICKS, frametime * len(frames))
        width = frames[0].width
        layers = svg_layers()
        groups = set().union(*(cells for _, css, cells in layers if css is not None))
        peaks = []
        for group in VEIN_GROUPS:
            fill, cells = next((f, c) for f, css, c in layers if css == group)
            others = set().union(*(c for f, css, c in layers if css not in (None, group)))
            probe = sorted(cells - others)[0]
            ground = next((f for f, css, c in reversed(layers) if css is None and probe in c), None)
            (point,) = to_frame({probe}, ORNAMENT_LEFT, False, width)
            alphas = [opacity(frame.getpixel(point), fill, ground) for frame in frames]
            self.assertAlmostEqual(PULSE_HIGH, max(alphas), delta=0.02, msg=group)
            self.assertAlmostEqual(PULSE_LOW, min(alphas), delta=0.02, msg=group)
            peaks.append(alphas.index(max(alphas)) * frametime)
        self.assertEqual([PULSE_STEP_TICKS, PULSE_STEP_TICKS], [peaks[1] - peaks[0], peaks[2] - peaks[1]])


class NineSliceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = GeneratedTree()

    def check_style(self, style):
        for part in ("background", "frame"):
            mcmeta = self.tree.path(style + "_" + part + ".png.mcmeta")
            self.assertTrue(mcmeta.is_file(), mcmeta.name + " not written")
            scaling = json.loads(mcmeta.read_text())["gui"]["scaling"]
            self.assertEqual("nine_slice", scaling["type"])
            self.assertIs(True, scaling.get("stretch_inner"), part + " edges tile")
        frames, meta = frames_of(self.tree.path(style + "_frame.png"), self.tree.path(style + "_frame.png.mcmeta"))
        scaling = meta["gui"]["scaling"]
        border = scaling["border"]
        if isinstance(border, int):
            border = {"left": border, "right": border, "top": border, "bottom": border}
        width, height = scaling["width"], scaling["height"]
        return frames, border, width, height

    def test_3_ultimate_corners_hold_the_ornament_and_the_centre_is_clear(self):
        frames, border, width, height = self.check_style(ULTIMATE)
        every_cell = set().union(*(cells for _, _, cells in svg_layers()))
        for mirrored in (False, True):
            for x, y in to_frame(every_cell, ORNAMENT_LEFT, mirrored, width):
                in_corner = (x < border["left"] or x >= width - border["right"]) and y < border["top"]
                self.assertTrue(in_corner, "ornament pixel %s outside a fixed corner" % ((x, y),))
        self.assert_centre_clear(frames, border, width, height)

    def test_3_common_centre_is_clear(self):
        frames, border, width, height = self.check_style(COMMON)
        self.assert_centre_clear(frames, border, width, height)

    def assert_centre_clear(self, frames, border, width, height):
        for index, frame in enumerate(frames):
            for y in range(border["top"], height - border["bottom"]):
                for x in range(border["left"], width - border["right"]):
                    self.assertEqual(0, frame.getpixel((x, y))[3], "frame %d centre pixel %s" % (index, (x, y)))

    def test_4_common_frame_is_rings_only(self):
        frames, _, width, height = self.check_style(COMMON)
        rings = {PANEL_BORDER_INSET - 1, PANEL_BORDER_INSET, PANEL_BORDER_INSET + 1}
        frame = frames[0]
        for y in range(height):
            for x in range(width):
                if min(x, width - 1 - x, y, height - 1 - y) not in rings:
                    self.assertEqual(0, frame.getpixel((x, y))[3], "common frame pixel %s" % ((x, y),))


class PanelColourTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = GeneratedTree()

    def image(self, relative):
        path = self.tree.path(relative)
        self.assertTrue(path.is_file(), relative + " not written")
        frames, _ = frames_of(path, self.tree.path(relative + ".mcmeta"))
        return frames[0]

    def test_5_common_colours(self):
        frame = self.image(COMMON + "_frame.png")
        background = self.image(COMMON + "_background.png")
        self.assertEqual(mix(COMMON_ACCENT, PANEL_BORDER_BASE, PANEL_BORDER_ACCENT) + (255,),
                         frame.getpixel((frame.width // 2, PANEL_BORDER_INSET)))
        self.assertEqual(mix(COMMON_ACCENT, PANEL_FILL_BASE, PANEL_FILL_ACCENT) + (255,),
                         background.getpixel((background.width // 2, PANEL_BORDER_INSET)))
        self.assertEqual(hex_rgb(PANEL_FILL_END) + (255,),
                         background.getpixel((background.width // 2, background.height - 1 - PANEL_BORDER_INSET)))

    def test_5_ultimate_colours(self):
        frame = self.image(ULTIMATE + "_frame.png")
        background = self.image(ULTIMATE + "_background.png")
        middle = frame.width // 2
        self.assertEqual(hex_rgb(BLOODWEAVER_TITLE_END) + (255,), frame.getpixel((middle, PANEL_BORDER_INSET)))
        self.assertEqual(hex_rgb(BLOODWEAVER_TITLE_END) + (255,), frame.getpixel((PANEL_BORDER_INSET, frame.height // 2)))
        self.assertEqual(mix(BLOODWEAVER_ACCENT, ULTIMATE_RING_BASE, ULTIMATE_RING_ACCENT) + (255,),
                         frame.getpixel((PANEL_BORDER_INSET + 2, frame.height // 2)))
        self.assertEqual(mix(BLOODWEAVER_ACCENT, PANEL_FILL_BASE, PANEL_FILL_ACCENT) + (255,),
                         background.getpixel((background.width // 2, PANEL_BORDER_INSET)))
        self.assertEqual(hex_rgb(PANEL_FILL_END) + (255,),
                         background.getpixel((background.width // 2, background.height - 1 - PANEL_BORDER_INSET)))


class MarksFontTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = GeneratedTree()

    def test_6_marks_font(self):
        font = self.tree.path(FONT_JSON)
        png = self.tree.path(FONT_PNG)
        self.assertTrue(font.is_file() and png.is_file(), "marks font not written")
        (provider,) = json.loads(font.read_text(encoding="utf-8"))["providers"]
        self.assertEqual(("bitmap", FONT_FILE_ID, 8, 7),
                         (provider["type"], provider["file"], provider.get("height", 8), provider["ascent"]))
        self.assertEqual(["".join(MARKS)], provider["chars"])
        image = Image.open(png).convert("RGBA")
        self.assertEqual((MARK_CELL * len(MARKS), MARK_CELL), image.size)
        advances = []
        for index in range(len(MARKS)):
            cell = image.crop((index * MARK_CELL, 0, (index + 1) * MARK_CELL, MARK_CELL))
            opaque = [(x, y) for y in range(MARK_CELL) for x in range(MARK_CELL) if cell.getpixel((x, y))[3]]
            self.assertTrue(opaque, "mark %d is empty" % index)
            self.assertTrue(all(cell.getpixel(p)[:3] == (255, 255, 255) for p in opaque), "mark %d is not white" % index)
            advances.append(max(x for x, _ in opaque) + 1 + 1)
        self.assertEqual(list(MARK_ADVANCES), advances)


class DriftTest(unittest.TestCase):
    def test_7_committed_assets_equal_generator_output(self):
        tree = GeneratedTree()
        written = sorted(p.relative_to(tree.root).as_posix() for p in tree.root.rglob("*") if p.is_file())
        self.assertTrue(written, "the generator wrote nothing")
        for relative in written:
            committed = REPO_ROOT / "src" / relative
            self.assertTrue(committed.is_file(), relative + " is not committed under src/")
            fresh = tree.path(relative).read_bytes()
            stored = committed.read_bytes()
            if relative.endswith(".png"):
                with Image.open(io.BytesIO(fresh)) as a, Image.open(io.BytesIO(stored)) as b:
                    self.assertEqual((a.mode, a.size, a.tobytes()), (b.mode, b.size, b.tobytes()), relative)
            else:
                # A Windows checkout under core.autocrlf rewrites line endings; the content is what is compared.
                self.assertEqual(fresh.replace(b"\r\n", b"\n"), stored.replace(b"\r\n", b"\n"), relative)


if __name__ == "__main__":
    unittest.main()
