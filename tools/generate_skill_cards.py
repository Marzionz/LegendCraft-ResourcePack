#!/usr/bin/env python3
"""Writes the codex skill-card assets: tooltip-style sprites and the stat-marks font.

Re-runnable; every run rewrites the same files under src/:

    python tools/generate_skill_cards.py

A style id ``legendcraft:classes/<name>`` on an item makes the client draw
``tooltip/classes/<name>_background`` then ``_frame`` from the GUI atlas over the text block grown
by 12 pixels a side. Sprite pixel (12, 12) is therefore the first text pixel, and every inset
below is measured from the sprite edge in GUI pixels.

The panel is the website card's box: a one-pixel outer ring, the border, one inner ring (two on an
ultimate), a vertical fill gradient and a drop shadow two pixels down and right. Colours are the
website's CSS colour mixes of the class accent. Corner ornaments are the approved 24x24 SVG,
rasterized by pixel centre, mirrored for the right corner, and animated by opacity only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image

ART_DIR = Path(__file__).resolve().parent / "skill_card_art"
SPRITE_DIR = "assets/legendcraft/textures/gui/sprites/tooltip/classes"
FONT_JSON = "assets/legendcraft/font/classes/skill_card.json"
FONT_PNG = "assets/legendcraft/textures/font/classes/skill_card_marks.png"
FONT_FILE_ID = "legendcraft:font/classes/skill_card_marks.png"

OUTER_RING_INSET = 7
BORDER_INSET = 8
OUTER_RING = (0x09, 0x05, 0x0D)
INNER_RING = (0x16, 0x0B, 0x19)
SHADOW_OFFSET = 2
SHADOW_ALPHA = 0x88

BORDER_BASE, BORDER_ACCENT_SHARE = (0x46, 0x34, 0x48), 0.60
FILL_BASE, FILL_ACCENT_SHARE, FILL_END = (0x10, 0x09, 0x11), 0.11, (0x11, 0x0A, 0x16)
ULTIMATE_RING_BASE, ULTIMATE_RING_ACCENT_SHARE = (0x35, 0x22, 0x31), 0.25
ULTIMATE_TOP_BORDER_PX = 2

BACKGROUND_SIZE = 32
BACKGROUND_SLICE = 10
COMMON_FRAME_SIZE = 32
COMMON_FRAME_SLICE = 10

ORNAMENT_SIZE = 24
# The ornament's top-left cell. Its lowest painted row lands one pixel above the third text line,
# which is where an ultimate card's title sits (banner, spacer, title).
ORNAMENT_LEFT = 12
ORNAMENT_TOP = 11
# The mirrored corner keeps the same distance from the right edge as the left one keeps from the left.
ORNAMENT_RIGHT_INSET = 13
ULTIMATE_FRAME_SIZE = 80
ULTIMATE_SLICE = {"left": 36, "right": 36, "top": 35, "bottom": 12}

# The vein pulse: 3.2 s at 20 ticks a second, one frame a tick. Keyframes are the website's
# percentages snapped to whole ticks, and each later group starts 0.16 s (rounded to 3 ticks) after
# the one before, root to branch to tip.
PULSE_PERIOD_TICKS = 64
PULSE_KEYFRAMES = ((0, 0.3), (10, 1.0), (18, 0.5), (26, 0.85), (42, 0.3), (64, 0.3))
PULSE_GROUP_DELAYS_TICKS = {"blood-root": 0, "blood-branch": 3, "blood-tip": 6}

COMMON_ACCENT = (0xAA, 0x55, 0xFF)
BLOODWEAVER_ACCENT = (0xFF, 0x17, 0x44)
BLOODWEAVER_TITLE_END = (0xFF, 0x51, 0x73)

MARK_CELL = 8
MARK_ASCENT = 7
# U+E000 mana, U+E001 health, U+E002 cooldown, U+E003 open bracket, U+E004 close bracket.
MARKS = (
    ("\ue000", ("...#...", "..###..", ".#####.", "#######", ".#####.", "..###..", "...#...")),
    ("\ue001", (".##.##.", "#######", "#######", "#######", ".#####.", "..###..", "...#...")),
    ("\ue002", ("#######", ".#...#.", "..#.#..", "...#...", "..#.#..", ".#.#.#.", "#######")),
    ("\ue003", ("#...", "#...", "#...", "#...", "#...", "#...", "####")),
    ("\ue004", ("####", "...#", "...#", "...#", "...#", "...#", "...#")),
)


def mix(accent, base, share):
    return tuple(int(a * share + b * (1 - share) + 0.5) for a, b in zip(accent, base))


def lerp(start, end, amount):
    return tuple(int(s + (e - s) * amount + 0.5) for s, e in zip(start, end))


def ring(image, inset, colour, top_inset=None):
    width, height = image.size
    top = inset if top_inset is None else top_inset
    for x in range(inset, width - inset):
        image.putpixel((x, top), colour + (255,))
        image.putpixel((x, height - 1 - inset), colour + (255,))
    for y in range(top, height - inset):
        image.putpixel((inset, y), colour + (255,))
        image.putpixel((width - 1 - inset, y), colour + (255,))


def background(accent):
    size = BACKGROUND_SIZE
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    last = size - 1 - BORDER_INSET
    for y in range(BORDER_INSET + SHADOW_OFFSET, last + SHADOW_OFFSET + 1):
        for x in range(BORDER_INSET + SHADOW_OFFSET, last + SHADOW_OFFSET + 1):
            image.putpixel((x, y), (0, 0, 0, SHADOW_ALPHA))
    top = mix(accent, FILL_BASE, FILL_ACCENT_SHARE)
    for y in range(BORDER_INSET, last + 1):
        colour = lerp(top, FILL_END, (y - BORDER_INSET) / (last - BORDER_INSET))
        for x in range(BORDER_INSET, last + 1):
            image.putpixel((x, y), colour + (255,))
    return image


def common_frame(accent):
    image = Image.new("RGBA", (COMMON_FRAME_SIZE, COMMON_FRAME_SIZE), (0, 0, 0, 0))
    ring(image, OUTER_RING_INSET, OUTER_RING)
    ring(image, BORDER_INSET, mix(accent, BORDER_BASE, BORDER_ACCENT_SHARE))
    ring(image, BORDER_INSET + 1, INNER_RING)
    return image


def svg_layers(svg_text):
    """(rgb, css class or None, covered cells) per path; a cell is covered when its centre is inside."""
    layers = []
    pattern = r'<path(?: class="([^"]+)")? fill="#([0-9a-fA-F]{6})" d="([^"]+)"'
    for css_class, fill, d in re.findall(pattern, svg_text):
        edges = []
        x = y = 0
        start = None
        for op, value in re.findall(r"([MHVZ])\s*(-?\d+(?:\s+-?\d+)?)?", d):
            if op == "M":
                x, y = (int(v) for v in value.split())
                start = (x, y)
            elif op == "H":
                edges.append(((x, y), (int(value), y)))
                x = int(value)
            elif op == "V":
                edges.append(((x, y), (x, int(value))))
                y = int(value)
            else:
                edges.append(((x, y), start))
                x, y = start
        cells = set()
        for cy in range(ORNAMENT_SIZE):
            for cx in range(ORNAMENT_SIZE):
                px, py = cx + 0.5, cy + 0.5
                winding = 0
                for (x0, y0), (x1, y1) in edges:
                    if x0 == x1 and px < x0:
                        if y0 <= py < y1:
                            winding += 1
                        elif y1 <= py < y0:
                            winding -= 1
                if winding:
                    cells.add((cx, cy))
        layers.append((tuple(int(fill[i:i + 2], 16) for i in (0, 2, 4)), css_class or None, cells))
    return layers


def over(image, cell, rgb, alpha):
    old = image.getpixel(cell)
    old_alpha = old[3] / 255
    out_alpha = alpha + old_alpha * (1 - alpha)
    if out_alpha == 0:
        return
    colour = tuple(int((n * alpha + o * old_alpha * (1 - alpha)) / out_alpha + 0.5) for n, o in zip(rgb, old[:3]))
    image.putpixel(cell, colour + (int(out_alpha * 255 + 0.5),))


def pulse_opacity(tick):
    tick %= PULSE_PERIOD_TICKS
    for (t0, v0), (t1, v1) in zip(PULSE_KEYFRAMES, PULSE_KEYFRAMES[1:]):
        if t0 <= tick < t1:
            return v0 + (v1 - v0) * (tick - t0) / (t1 - t0)
    return PULSE_KEYFRAMES[-1][1]


def ornament(layers, tick):
    image = Image.new("RGBA", (ORNAMENT_SIZE, ORNAMENT_SIZE), (0, 0, 0, 0))
    for rgb, css_class, cells in layers:
        alpha = 1.0 if css_class is None else pulse_opacity(tick - PULSE_GROUP_DELAYS_TICKS[css_class])
        for cell in cells:
            over(image, cell, rgb, alpha)
    return image


def ultimate_frame(accent, title_end, layers):
    size = ULTIMATE_FRAME_SIZE
    strip = Image.new("RGBA", (size, size * PULSE_PERIOD_TICKS), (0, 0, 0, 0))
    for tick in range(PULSE_PERIOD_TICKS):
        frame = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ring(frame, OUTER_RING_INSET, OUTER_RING)
        ring(frame, BORDER_INSET, title_end)
        for extra in range(1, ULTIMATE_TOP_BORDER_PX):
            for x in range(BORDER_INSET, size - BORDER_INSET):
                frame.putpixel((x, BORDER_INSET + extra), title_end + (255,))
        ring(frame, BORDER_INSET + 1, INNER_RING, BORDER_INSET + ULTIMATE_TOP_BORDER_PX)
        ring(frame, BORDER_INSET + 2, mix(accent, ULTIMATE_RING_BASE, ULTIMATE_RING_ACCENT_SHARE),
             BORDER_INSET + ULTIMATE_TOP_BORDER_PX + 1)
        corner = ornament(layers, tick)
        frame.alpha_composite(corner, (ORNAMENT_LEFT, ORNAMENT_TOP))
        frame.alpha_composite(corner.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
                              (size - ORNAMENT_RIGHT_INSET - (ORNAMENT_SIZE - 1), ORNAMENT_TOP))
        strip.paste(frame, (0, tick * size))
    return strip


def nine_slice(size, border, animated=False):
    meta = {"gui": {"scaling": {"type": "nine_slice", "width": size, "height": size,
                                "border": border, "stretch_inner": True}}}
    if animated:
        meta["animation"] = {"frametime": 1}
    return meta


def marks_font():
    image = Image.new("RGBA", (MARK_CELL * len(MARKS), MARK_CELL), (0, 0, 0, 0))
    for index, (_, rows) in enumerate(MARKS):
        for y, row in enumerate(rows):
            for x, bit in enumerate(row):
                if bit == "#":
                    image.putpixel((index * MARK_CELL + x, y), (255, 255, 255, 255))
    font = {"providers": [{"type": "bitmap", "file": FONT_FILE_ID, "ascent": MARK_ASCENT,
                           "height": MARK_CELL, "chars": ["".join(char for char, _ in MARKS)]}]}
    return font, image


def build(pack_src: Path) -> list[Path]:
    """Writes every skill-card asset under ``pack_src`` and returns the paths written."""
    written = []

    def save_png(relative, image):
        path = pack_src / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        written.append(path)

    def save_json(relative, data):
        path = pack_src / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
        written.append(path)

    layers = svg_layers((ART_DIR / "blood.svg").read_text(encoding="utf-8"))
    styles = (
        ("skill_card", background(COMMON_ACCENT), common_frame(COMMON_ACCENT),
         nine_slice(COMMON_FRAME_SIZE, COMMON_FRAME_SLICE)),
        ("skill_card_ultimate_bloodweaver", background(BLOODWEAVER_ACCENT),
         ultimate_frame(BLOODWEAVER_ACCENT, BLOODWEAVER_TITLE_END, layers),
         nine_slice(ULTIMATE_FRAME_SIZE, ULTIMATE_SLICE, animated=True)),
    )
    for name, back, frame, frame_meta in styles:
        base = SPRITE_DIR + "/" + name
        save_png(base + "_background.png", back)
        save_json(base + "_background.png.mcmeta", nine_slice(BACKGROUND_SIZE, BACKGROUND_SLICE))
        save_png(base + "_frame.png", frame)
        save_json(base + "_frame.png.mcmeta", frame_meta)

    font, marks = marks_font()
    save_png(FONT_PNG, marks)
    save_json(FONT_JSON, font)
    return written


if __name__ == "__main__":
    for path in build(Path(__file__).resolve().parents[1] / "src"):
        print(path)
