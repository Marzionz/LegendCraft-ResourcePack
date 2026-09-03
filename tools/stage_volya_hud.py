#!/usr/bin/env python3
"""Stage the purchased Volya HUD art into the LegendCraft HUD tree.

The three Volya packs are MythicHUD products; we run BetterHud. Nothing of theirs
is used as-is: this script extracts the *textures* from the purchased zips, recolors
the ones that carry a hue into the locked LegendCraft palette, and writes them under
`hud/party/`. The YAML is a from-scratch rewrite in BetterHud 2.1.0 syntax
(see `betterhud/{images,layouts}/legendcraft-party.yml`).

SCOPE: party-frame chrome and bars ONLY. The health bar's affliction states were
modelled on Volya's MMORPG HUD but are DRAWN BY US, in `generate_hud.py`
(`AFFLICTION` / `affliction_fill` / `affliction_heart`) -- owner call, 2026-08-28.
What survived from that pack is the idea, not the pixels: tint the health bar itself
rather than adding a second indicator. The MMORPG zip is no longer read at all.
The class icons in the party rows are likewise ours, not Volya's 61-icon set.

    python tools/stage_volya_hud.py

Source zips live OUTSIDE every repo (`C:/Repositories/Bought assets/`) and are never
committed. Re-run this after a Volya pack update; it is deterministic.

WHY A SCRIPT AND NOT A COPY. The bars need work before they can sit next to
`generate_hud.py`'s output:

  * The party bars ship pre-colored in Volya's palette (HP `#BE2020`, mana `#146EBE`).
    Dropped in unchanged they would read as a second, slightly-wrong red next to the
    stat block's `BAR_RAMP["health"]`. Each is re-mapped, by luminance, onto the same
    three-stop ramp the generator uses, so party frames and stat block are one palette.
  * The single mana bar becomes three (mana / energy / rage) because a LegendCraft
    party member's resource is class-dependent (`hud-and-icons.md` §2).

The chrome (frame, bar outlines, leader crown) needs nothing and ships verbatim: it is
already flat, translucent and desaturated, which is what `hud-and-icons.md` §1 asks of
chrome.
"""

import os
import shutil
import sys
import tempfile
import zipfile

from PIL import Image

BOUGHT = r"C:\Repositories\Bought assets"
PARTY_ZIP = "Volya's Party HUD 1.1.0.zip"

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud")
PARTY_OUT = os.path.normpath(os.path.join(ROOT, "party"))

# Inside each zip. The four Party presets (MythicRPG / MythicDungeons / MMOCore /
# Parties) differ ONLY in which plugin's placeholders their YAML reads -- every texture
# is byte-identical across all four (verified by md5). We take preset 1 and rewire the
# placeholders ourselves, so the preset choice is moot; what the owner actually picks is
# the LAYOUT VARIANT below.
PARTY_BASE = ("Volya's Party HUD 1.1.0/Preset 1 - MythicRPG/"
              "{variant}/MythicHUD/source-pack/assets/mythichud/textures/assets/partyhud/")

# Locked palette (hud-and-icons.md §2 / generate_hud.py BAR_RAMP) -- kept as literals
# rather than imported so this staging step never drags in the generator's Pillow-heavy
# module graph. If BAR_RAMP moves, this list moves with it.
RAMP = {
    "health": ((0xE0, 0x5A, 0x4E), (0xC4, 0x3B, 0x2E), (0x7A, 0x20, 0x1A)),
    "mana":   ((0x74, 0x9C, 0xF2), (0x3D, 0x6F, 0xE0), (0x20, 0x3C, 0x84)),
    "energy": ((0xF2, 0xDE, 0x7A), (0xE8, 0xC8, 0x4A), (0x86, 0x6E, 0x20)),
    # Rage is EMBER-LED here, not red-led like the stat block's `BAR_RAMP["rage"]`. Both are the
    # locked rage vocabulary (`hud-and-icons.md` §2: top edge #F4924E, ember #EC6C2E, red #BA3426),
    # weighted differently because the constraint differs. The stat block's rage bar is 7px tall
    # and separates itself from health by showing two OBVIOUS bands; a party row's resource bar is
    # 2px and can show exactly one, so a red-led ramp there renders a second red bar directly under
    # the member's red HP bar -- the precise misread §2 says rage must never produce.
    "rage":   ((0xF4, 0x92, 0x4E), (0xEC, 0x6C, 0x2E), (0xBA, 0x34, 0x26)),
    # The class-shield pool (AUD-7). Deliberately NOT antique gold `#D9A94A` -- that hex
    # is the value thread (Marks/prestige) and `hud-and-icons.md` §4 keeps it off every
    # other element. A cold ward-steel reads as "borrowed hit points", not as currency.
    "shield": ((0xD6, 0xE2, 0xEE), (0x8F, 0xA8, 0xC8), (0x46, 0x5A, 0x74)),
}

# Which textures get re-ramped, and onto which ramp.
PARTY_RECOLOR = {
    "party_bar_fill_health.png": ("health", "fill_health.png"),
    "party_bar_fill_mana.png": ("mana", "fill_mana.png"),
    "party_bar_fill_absorption.png": ("shield", "fill_shield.png"),
}
# The mana bar is the shape for all three resources; only the ramp differs.
PARTY_RESOURCE_CLONES = {
    "party_bar_fill_mana.png": [("energy", "fill_energy.png"), ("rage", "fill_rage.png")],
}
# Chrome: flat translucent near-black with a noise grain. Already desaturated and
# non-glowing, which is what `hud-and-icons.md` §1 asks of chrome, so it ships as-is.
PARTY_VERBATIM = {
    "party_background.png": "frame_portrait.png",
    "party_bar_outline_health.png": "outline_health.png",
    "party_bar_outline_mana.png": "outline_resource.png",
    "party_leader.png": "leader.png",
}
PARTY_VARIANT_EXTRA = {
    "3 - COMPACT": {"party_background_noclass.png": "frame_compact.png"},
    "4 - RAID": {"party_background_xl.png": "frame_raid.png"},
}

def _lum(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def reramp(im, ramp):
    """Re-map a pre-colored bar onto a three-stop LegendCraft ramp.

    Volya's fills are 2--3px tall and built as highlight / body / floor rows, so a
    per-pixel luminance split onto (top, main, floor) reproduces the same read in our
    hues without inventing shading the original didn't have. Alpha is preserved exactly,
    which matters: several of these carry partial alpha at the bar caps.
    """
    top, main, floor = ramp
    src = im.convert("RGBA")
    lums = [_lum(*src.getpixel((x, y))[:3])
            for y in range(src.height) for x in range(src.width)
            if src.getpixel((x, y))[3] > 0]
    if not lums:
        return src
    lo, hi = min(lums), max(lums)
    span = max(hi - lo, 1e-6)
    out = src.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            t = (_lum(r, g, b) - lo) / span
            stop = floor if t < 0.34 else (main if t < 0.72 else top)
            px[x, y] = (stop[0], stop[1], stop[2], a)
    return out


def _extract(zip_path, into):
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(into)


def _write(im, out_dir, name):
    im.save(os.path.join(out_dir, name))
    return f"  {name:26s} {im.width}x{im.height}"


def stage():
    os.makedirs(PARTY_OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="volya-stage-")
    written = []
    try:
        _extract(os.path.join(BOUGHT, PARTY_ZIP), tmp)

        portrait = os.path.join(tmp, PARTY_BASE.format(variant="1 - PORTRAIT"))
        for src, dst in PARTY_VERBATIM.items():
            shutil.copyfile(os.path.join(portrait, src), os.path.join(PARTY_OUT, dst))
            written.append(f"  {dst:26s} (verbatim)")
        for src, (ramp, dst) in PARTY_RECOLOR.items():
            written.append(_write(reramp(Image.open(os.path.join(portrait, src)), RAMP[ramp]),
                                  PARTY_OUT, dst))
        for src, clones in PARTY_RESOURCE_CLONES.items():
            for ramp, dst in clones:
                written.append(_write(reramp(Image.open(os.path.join(portrait, src)), RAMP[ramp]),
                                      PARTY_OUT, dst))
        for variant, extra in PARTY_VARIANT_EXTRA.items():
            base = os.path.join(tmp, PARTY_BASE.format(variant=variant))
            for src, dst in extra.items():
                shutil.copyfile(os.path.join(base, src), os.path.join(PARTY_OUT, dst))
                written.append(f"  {dst:26s} (verbatim)")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"staged {len(written)} textures")
    for line in written:
        print(line)
    print(f"\nparty -> {PARTY_OUT}")


if __name__ == "__main__":
    if not os.path.isdir(BOUGHT):
        sys.exit(f"purchased assets not found at {BOUGHT}")
    stage()
