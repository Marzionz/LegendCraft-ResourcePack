#!/usr/bin/env python3
"""Flame Surge rune ring ranks: writes the ring's four rank flipbooks and their burn-away frames.

Durable and re-runnable. Reads the three band flipbooks `tools/gen-flipbook-frames.py` generates
from `pyro_surge_ring.bbmodel` (`pyro_surge_ring_{low,mid,high}_<n>`, textures and item models
under `src/assets/legendcraft/`) and writes, beside them:

    pyro_surge_ring_<rank>_<n>         n 1..9, the ring lighting up, one frame a tick
    pyro_surge_ring_<rank>_burn_<k>    k 1..10, the ring burning away from the held frame 9

for the four ranks Flame Surge's flame takes by the target's Burning stacks: red (the low band),
orange (mid), white (high) and blue (the high band recoloured through the blue rank's ramp).

The band frames are each authored a little higher than the last (y 8.12 to 8.32 in the item
model), so a flipbook stepping through them drifts upward. Every frame written here lies on
frame 1's plane, so the ring stands still.

The burn-away dissolves the lettered ring in patches. A smooth noise field, the same for every
rank, decides when each texel goes: past its moment it is gone, just before it it burns at the
rank's hot edge colour, and until then it keeps its colour while cooling toward the rank's ember.
Frame 10 is fully burnt; the hook removes the display when it ends.

    python mobs-src/props/surge_ring_ranks.py
"""

from __future__ import annotations

import json
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(REPO_ROOT, "src", "assets", "legendcraft")
ITEMS_DIR = os.path.join(ASSETS, "items", "classes")
MODELS_DIR = os.path.join(ASSETS, "models", "item", "classes")
TEXTURES_DIR = os.path.join(ASSETS, "textures", "item", "classes")

STEM = "pyro_surge_ring"
LIT_FRAMES = 9
BURN_FRAMES = 10
BURN_EDGE = 0.16
EMBER_COOLING = 0.55
NOISE_SEED = 7
NOISE_CELLS = 6

RANKS = {
    "red": "low",
    "orange": "mid",
    "white": "high",
    "blue": "high",
}

# The blue rank's ramp, dark to hot, from Flame Surge's blue flame. It tops out at pale cyan
# rather than white: the high band's outer ring sits at its brightest, and white there reads as
# the white rank. The luma is pressed down a little so most of the ring lands on the bright blue.
BLUE_RAMP = [(0x1E, 0x59, 0x6E), (0x2E, 0x8F, 0xB8), (0x4C, 0xC7, 0xFF), (0x9F, 0xE8, 0xFF)]
BLUE_GAMMA = 1.6

# The colour a texel burns at just before it goes, per rank.
HOT_EDGE = {
    "red": (0xFF, 0xD2, 0x4A),    # gold
    "orange": (0xFF, 0xF4, 0xE0),  # white-hot
    "white": (0xFF, 0xFF, 0xFF),   # white
    "blue": (0xE8, 0xFF, 0xFF),    # ice white
}

# The colour the ring cools toward while it burns, per rank.
EMBER = {
    "red": (0x4A, 0x10, 0x0A),
    "orange": (0x7A, 0x1F, 0x10),
    "white": (0x7A, 0x1F, 0x10),
    "blue": (0x0E, 0x2C, 0x3A),
}


def luma(rgb: tuple[int, int, int]) -> float:
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255.0


def ramp(t: float, stops: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    t = min(max(t, 0.0), 1.0) * (len(stops) - 1)
    i = min(int(t), len(stops) - 2)
    f = t - i
    a, b = stops[i], stops[i + 1]
    return tuple(round(a[c] + (b[c] - a[c]) * f) for c in range(3))


def blue(source: Image.Image) -> Image.Image:
    texels = [p for p in source.get_flattened_data() if p[3] > 0]
    lo = min(luma(p[:3]) for p in texels)
    hi = max(luma(p[:3]) for p in texels)
    out = Image.new("RGBA", source.size)
    out.putdata([(0, 0, 0, 0) if p[3] == 0
                 else ramp(((luma(p[:3]) - lo) / max(hi - lo, 1e-6)) ** BLUE_GAMMA, BLUE_RAMP) + (p[3],)
                 for p in source.get_flattened_data()])
    return out


def noise(size: tuple[int, int]) -> list[float]:
    rng = random.Random(NOISE_SEED)
    coarse = Image.new("L", (NOISE_CELLS, NOISE_CELLS))
    coarse.putdata([rng.randrange(256) for _ in range(NOISE_CELLS * NOISE_CELLS)])
    smooth = coarse.resize(size, Image.BICUBIC)
    values = [v / 255.0 for v in smooth.get_flattened_data()]
    lo, hi = min(values), max(values)
    return [(v - lo) / (hi - lo) for v in values]


def burn(held: Image.Image, rank: str, step: int, field: list[float]) -> Image.Image:
    edge, ember = HOT_EDGE[rank], EMBER[rank]
    front = step / BURN_FRAMES * (1.0 + BURN_EDGE)
    cooled = EMBER_COOLING * step / BURN_FRAMES
    out = []
    for texel, n in zip(held.get_flattened_data(), field):
        if texel[3] == 0 or n < front - BURN_EDGE:
            out.append((0, 0, 0, 0))
        elif n < front:
            out.append(edge + (255,))
        else:
            out.append(tuple(round(texel[c] + (ember[c] - texel[c]) * cooled) for c in range(3))
                       + (texel[3],))
    image = Image.new("RGBA", held.size)
    image.putdata(out)
    return image


def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, separators=(",", ":"))
        handle.write("\n")


def write_frame(name: str, texture: Image.Image, plane: dict) -> None:
    texture.save(os.path.join(TEXTURES_DIR, name + ".png"))
    ref = "legendcraft:item/classes/" + name
    model = dict(plane)
    model["textures"] = {key: ref for key in plane["textures"]}
    write_json(os.path.join(MODELS_DIR, name + ".json"), model)
    write_json(os.path.join(ITEMS_DIR, name + ".json"), {"model": {
        "type": "minecraft:model", "model": "legendcraft:item/classes/" + name}})


def main() -> int:
    written = 0
    for rank, band in RANKS.items():
        with open(os.path.join(MODELS_DIR, "%s_%s_1.json" % (STEM, band)), encoding="utf-8") as handle:
            plane = json.load(handle)
        frames = []
        for n in range(1, LIT_FRAMES + 1):
            with Image.open(os.path.join(TEXTURES_DIR, "%s_%s_%d.png" % (STEM, band, n))) as source:
                lit = source.convert("RGBA")
            frames.append(blue(lit) if rank == "blue" else lit)
        for n, texture in enumerate(frames, start=1):
            write_frame("%s_%s_%d" % (STEM, rank, n), texture, plane)
            written += 1
        field = noise(frames[-1].size)
        for k in range(1, BURN_FRAMES + 1):
            write_frame("%s_%s_burn_%d" % (STEM, rank, k), burn(frames[-1], rank, k, field), plane)
            written += 1
    print("wrote %d ring frames" % written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
