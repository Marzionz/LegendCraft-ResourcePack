#!/usr/bin/env python3
"""Flame Surge magma pool ranks: writes the L45 field's pool flipbooks, cooling then burning away.

Durable and re-runnable. Reads the bright magma disc of the samusdev pack's Magma Dash ground pool
(`magma_dash_vfx.png`, the 16 x 16 cell at the atlas origin; the pack's licence permits
modification) and stretches its lumpy blob into a solid round disc that fills a 32 x 32 frame:
each frame texel inside the circle samples the source along the same angle from the blob's
centroid, at the same fraction of the blob's edge on that angle, nearest-neighbour and fully
opaque. It writes under `src/assets/legendcraft/`:

    pyro_surge_pool_<rank>_<n>         n 1..12, the pool cooling from its rank's heat to a crust
    pyro_surge_pool_<rank>_burn_<k>    k 1..10, the crusted pool burning away from frame 12

for the four ranks Flame Surge's flame takes by the target's Burning stacks: red, orange, white
and blue.

Each texel's luma, normalised over the disc and raised to the rank's gamma, is mapped through the
rank's ramp (dark, body, hot, core). Cooling frame n pulls every texel toward the rank's crust by `c = 0.85 * (n - 1) / 11`,
weighted `clamp(c * (1.6 - 1.2 * luma))`, so the dark skin crusts over first and the brightest
seams cool last and glow through. The burn-away is the rune ring's (`surge_ring_ranks.py`): the
same noise field, front, hot edge and ember per rank, so the pool and the ring burn out together.

Every frame is one horizontal 32 x 32 u plane at y 8.1, x/z -8..24, its up face textured with
the whole frame. At scale 1 the disc's edge sits 1 block from the centre; the plugin scales the
display to the rune ring's reach, the blast radius.

    python mobs-src/props/surge_pool_ranks.py "<samusdev pack>/ModelEngine/blueprints/RPG_Class_Awakened_Pyromancer/Magma Dash/magma_dash_vfx.png"
"""

from __future__ import annotations

import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import surge_ring_ranks as ring  # noqa: E402

STEM = "pyro_surge_pool"
DISC = (0, 0, 16, 16)
UPSCALE = 2
EDGE_STEP = 0.05
COOL_FRAMES = 12
COOL_MAX = 0.85
PLANE_Y = 8.1

RAMPS = {
    "red": [(0x3A, 0x08, 0x06), (0x8E, 0x1A, 0x0C), (0xD8, 0x36, 0x1A), (0xFF, 0x7A, 0x3A)],
    "orange": [(0x4A, 0x12, 0x06), (0xC0, 0x40, 0x0A), (0xFF, 0x8A, 0x1A), (0xFF, 0xD2, 0x4A)],
    "white": [(0xC8, 0x6A, 0x2A), (0xFF, 0xC4, 0x70), (0xFF, 0xF2, 0xCC), (0xFF, 0xFF, 0xFF)],
    "blue": [(0x0E, 0x2C, 0x3A), (0x2E, 0x8F, 0xB8), (0x4C, 0xC7, 0xFF), (0xE8, 0xFF, 0xFF)],
}

# The power each rank raises the normalised luma to before its ramp: below 1 lifts the disc's
# darker skin toward the rank's hot stops, so the white rank reads white-hot rather than tan.
GAMMA = {"red": 1.0, "orange": 1.0, "white": 0.5, "blue": 0.8}

CRUST = {
    "red": (0x24, 0x0A, 0x08),
    "orange": (0x24, 0x0A, 0x08),
    "white": (0x2A, 0x10, 0x0A),
    "blue": (0x0A, 0x16, 0x22),
}


def disc(source_path: str) -> Image.Image:
    """The source blob stretched to a solid round disc that fills the frame."""
    with Image.open(source_path) as atlas:
        cell = atlas.convert("RGBA").crop(DISC)
    w, h = cell.size
    opaque = [(x + 0.5, y + 0.5) for y in range(h) for x in range(w) if cell.getpixel((x, y))[3]]
    cx = sum(p[0] for p in opaque) / len(opaque)
    cy = sum(p[1] for p in opaque) / len(opaque)

    def drawn(x: float, y: float) -> bool:
        return 0 <= x < w and 0 <= y < h and cell.getpixel((int(x), int(y)))[3] > 0

    def edge(angle: float) -> float:
        t = 0.0
        while drawn(cx + math.cos(angle) * (t + EDGE_STEP), cy + math.sin(angle) * (t + EDGE_STEP)):
            t += EDGE_STEP
        return t

    size = w * UPSCALE
    radius = size / 2
    out = Image.new("RGBA", (size, size))
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - radius, y + 0.5 - radius
            d = math.hypot(dx, dy)
            if d > radius:
                continue
            angle = math.atan2(dy, dx)
            reach = d / radius * edge(angle)
            sx, sy = cx + math.cos(angle) * reach, cy + math.sin(angle) * reach
            while not drawn(sx, sy):
                reach -= EDGE_STEP
                sx, sy = cx + math.cos(angle) * reach, cy + math.sin(angle) * reach
            texel = cell.getpixel((int(sx), int(sy)))
            out.putpixel((x, y), texel[:3] + (255,))
    return out


def lumas(image: Image.Image) -> list[float | None]:
    values = [ring.luma(p[:3]) if p[3] else None for p in image.get_flattened_data()]
    drawn = [v for v in values if v is not None]
    lo, hi = min(drawn), max(drawn)
    return [None if v is None else (v - lo) / max(hi - lo, 1e-6) for v in values]


def cooled(source: Image.Image, levels: list[float | None], rank: str, n: int) -> Image.Image:
    c = COOL_MAX * (n - 1) / (COOL_FRAMES - 1)
    crust = CRUST[rank]
    out = []
    for texel, level in zip(source.get_flattened_data(), levels):
        if level is None:
            out.append((0, 0, 0, 0))
            continue
        hot = ring.ramp(level ** GAMMA[rank], RAMPS[rank])
        w = min(max(c * (1.6 - 1.2 * level), 0.0), 1.0)
        out.append(tuple(round(hot[i] + (crust[i] - hot[i]) * w) for i in range(3)) + (texel[3],))
    image = Image.new("RGBA", source.size)
    image.putdata(out)
    return image


def plane() -> dict:
    return {
        "textures": {"0": "", "particle": ""},
        "elements": [{
            "from": [-8, PLANE_Y, -8],
            "to": [24, PLANE_Y, 24],
            "faces": {"up": {"uv": [0, 0, 16, 16], "texture": "#0"}},
        }],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    source = disc(argv[1])
    levels = lumas(source)
    field = ring.noise(source.size)
    written = 0
    for rank in RAMPS:
        last = None
        for n in range(1, COOL_FRAMES + 1):
            last = cooled(source, levels, rank, n)
            ring.write_frame("%s_%s_%d" % (STEM, rank, n), last, plane())
            written += 1
        for k in range(1, ring.BURN_FRAMES + 1):
            ring.write_frame("%s_%s_burn_%d" % (STEM, rank, k), ring.burn(last, rank, k, field), plane())
            written += 1
    print("wrote %d pool frames" % written)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
