#!/usr/bin/env python3
"""Ember Shell egg shipping: writes the egg's item models, item definitions and textures into the pack.

Durable and re-runnable. Reads the artist's finished Java models and tier atlases (the
`shipping/` folder of the egg delivery, `models/effect/*.json` and `textures/effect/*.png`) and
writes, under `src/assets/legendcraft/`:

    items/classes/ember_shell_egg_<r>_tier_<t>.json             finished egg, r ribbons, heat tier t
    items/classes/ember_shell_form_<r>_tier_<t>_<nn>.json       form state nn (00..10)
    models/item/classes/<same>.json                             the geometry
    textures/item/classes/ember_shell_egg_tier_<t>.png          the tier atlas, pixelated

The delivered models are authored with the caster's feet at the model origin and reach past the
item model's [-16, 32] element box, which the 26.1.2 client refuses ("specifier exceeds the
allowed boundaries"). Every coordinate (`from`, `to`, rotation `origin`) is drawn at half size and
moved by +8 so the feet sit on the display's own origin; the plugin draws the display at twice the
egg's size to restore it. Rotation angles, UVs and faces are unchanged. A model that still
overruns the box is refused.

The delivered atlases paint about 100 texels per block, smooth gradients included, which reads as
clean against the roster's block-scale art. Each atlas is drawn at a quarter of its size (about
25 texels per block, the glyphs still legible): every 4 x 4 cell takes the median alpha of its
texels, so the faint inner faces keep their alpha and a cell on a face edge stays either drawn or
clear, and the mean colour of its drawn texels. The colours are then cut to 16 per atlas with no
dithering, so the gradients fall into hard steps. UVs are unchanged; the item model scales them
to whatever size the atlas is.

    python mobs-src/props/ember_shell_ship.py <delivery>/shipping
"""

from __future__ import annotations

import json
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(REPO_ROOT, "src", "assets", "legendcraft")
ITEMS_DIR = os.path.join(ASSETS, "items", "classes")
MODELS_DIR = os.path.join(ASSETS, "models", "item", "classes")
TEXTURES_DIR = os.path.join(ASSETS, "textures", "item", "classes")

SHRINK = 2.0
CENTRE = 8.0
BOX_MIN, BOX_MAX = -16.0, 32.0
PRECISION = 6
PIXEL = 4
ATLAS_COLOURS = 16

FINISHED = re.compile(r"^ember_shell_egg_(\d)_tier_(\d)\.json$")
FORM = re.compile(r"^form_a_egg_(\d)_tier_(\d)_(\d\d)\.json$")
ATLAS = re.compile(r"^egg_tier_(\d)\.png$")


def placed(value: float) -> float:
    return round(value / SHRINK + CENTRE, PRECISION)


def ship_model(source: dict, name: str) -> dict:
    elements = []
    for element in source["elements"]:
        moved = dict(element)
        moved["from"] = [placed(v) for v in element["from"]]
        moved["to"] = [placed(v) for v in element["to"]]
        if "rotation" in element:
            rotation = dict(element["rotation"])
            rotation["origin"] = [placed(v) for v in rotation["origin"]]
            moved["rotation"] = rotation
        for corner in (moved["from"], moved["to"]):
            if any(v < BOX_MIN or v > BOX_MAX for v in corner):
                raise SystemExit("%s: element %s still overruns the item model box: %s"
                                 % (name, element.get("name"), corner))
        elements.append(moved)
    textures = {}
    for key, ref in source["textures"].items():
        tier = re.search(r"egg_tier_(\d)$", ref)
        if not tier:
            raise SystemExit("%s: unexpected texture %s" % (name, ref))
        textures[key] = "legendcraft:item/classes/ember_shell_egg_tier_%s" % tier.group(1)
    return {
        "ambientocclusion": source.get("ambientocclusion", False),
        "texture_size": source["texture_size"],
        "textures": textures,
        "elements": elements,
    }


def pixelate(source: Image.Image) -> Image.Image:
    rgba = source.convert("RGBA")
    width, height = rgba.size
    cells = Image.new("RGBA", (width // PIXEL, height // PIXEL))
    texels, drawn = rgba.load(), cells.load()
    for y in range(height // PIXEL):
        for x in range(width // PIXEL):
            block = [texels[x * PIXEL + i, y * PIXEL + j] for i in range(PIXEL) for j in range(PIXEL)]
            alpha = sorted(texel[3] for texel in block)[len(block) // 2]
            if alpha == 0:
                drawn[x, y] = (0, 0, 0, 0)
                continue
            lit = [texel for texel in block if texel[3] > 0]
            drawn[x, y] = tuple(sum(texel[c] for texel in lit) // len(lit) for c in range(3)) + (alpha,)
    stepped = cells.convert("RGB").quantize(colors=ATLAS_COLOURS, method=Image.Quantize.MEDIANCUT,
                                           dither=Image.Dither.NONE).convert("RGB")
    return Image.merge("RGBA", (*stepped.split(), cells.split()[3]))


def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, separators=(",", ":"))
        handle.write("\n")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    shipping = argv[1]
    models_in = os.path.join(shipping, "models", "effect")
    textures_in = os.path.join(shipping, "textures", "effect")
    for folder in (ITEMS_DIR, MODELS_DIR, TEXTURES_DIR):
        os.makedirs(folder, exist_ok=True)
    written = 0
    for file in sorted(os.listdir(models_in)):
        finished, form = FINISHED.match(file), FORM.match(file)
        if finished:
            name = "ember_shell_egg_%s_tier_%s" % finished.groups()
        elif form:
            name = "ember_shell_form_%s_tier_%s_%s" % form.groups()
        else:
            continue
        with open(os.path.join(models_in, file), encoding="utf-8") as handle:
            source = json.load(handle)
        write_json(os.path.join(MODELS_DIR, name + ".json"), ship_model(source, name))
        write_json(os.path.join(ITEMS_DIR, name + ".json"), {"model": {
            "type": "minecraft:model", "model": "legendcraft:item/classes/" + name}})
        written += 1
    for file in sorted(os.listdir(textures_in)):
        atlas = ATLAS.match(file)
        if atlas:
            with Image.open(os.path.join(textures_in, file)) as source:
                pixelate(source).save(
                    os.path.join(TEXTURES_DIR, "ember_shell_egg_tier_%s.png" % atlas.group(1)))
    print("wrote %d egg models" % written)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
