#!/usr/bin/env python3
"""
LegendCraft HUD asset generator.

Procedurally builds the SHARED skill-casting HUD chrome from HUD_AND_ICONS.md:
  - frame ranks (base / subclass / ultimate keystone / locked ult)
  - resource pip, 3-segment charge indicator, L/R/Q/F keybind glyphs
  - the cooldown shroud, out-of-mana wash, outlined-numeral font, charge badge
  - the chunky stat bars (HP / armor / resource / food / XP) + their icons
  - the BetterHud image/layout/hud/text YAML that wires all of the above

It does NOT author ability-icon art. Each icon's PNG is drawn and edited directly on disk
under hud/skill-icons/<class>/ (via the legendcraft-icon skill) and is the source of
truth; this generator only POINTS the HUD wiring at those PNGs and must never overwrite them.
Everything here is authored at true pixel-art resolution (shared chrome on a 16px inner
field, ART; icons ship at 32px, ICON_ART). Re-run after editing shared chrome:

    python tools/generate_hud.py

Outputs land under hud/. Only Pillow is required.
"""

from __future__ import annotations
import math
import os
import re
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "hud"))
DIRS = {
    "frames": os.path.join(ROOT, "frames"),
    "hunter": os.path.join(ROOT, "skill-icons", "hunter"),
    "archer": os.path.join(ROOT, "skill-icons", "archer"),
    "ind": os.path.join(ROOT, "indicators"),
    "prev": os.path.join(ROOT, "previews"),
    "font": os.path.join(ROOT, "font"),
}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

# Per-class HUD icon linking map (data-only, edited by icon/linking agents). Kept in its own
# module so the icon work never collides with the HUD-wiring logic here.
import sys as _sys
_sys.path.insert(0, HERE)
try:
    from hud_icon_map import CLASS_SKILL_ICONS
except Exception:                       # missing/broken map -> HUD falls back to the placeholder gem
    CLASS_SKILL_ICONS = {}

# ---------------------------------------------------------------------------
# Palette (ART_STYLE.md neutrals + Hunter venom/bruise; HUD_AND_ICONS field)
# ---------------------------------------------------------------------------
T = (0, 0, 0, 0)                       # transparent
PAL = {
    ".": T,
    # iron / steel chrome
    "k": (0x14, 0x16, 0x1A, 255),      # near-black outer rim / outline
    "i": (0x3A, 0x3D, 0x42, 255),      # iron dark
    "I": (0x56, 0x5B, 0x63, 255),      # iron  (ART_STYLE weathered iron #565B63)
    "L": (0x7A, 0x82, 0x8C, 255),      # iron light
    "H": (0x9A, 0xA2, 0xAC, 255),      # iron highlight
    # bone parchment (keyline + glyphs)  #D8CDB4
    "b": (0xA8, 0x9C, 0x80, 255),
    "B": (0xD8, 0xCD, 0xB4, 255),
    # venom green  #AEEA00
    "g": (0x56, 0x74, 0x00, 255),      # venom dark
    "G": (0x7C, 0xA8, 0x00, 255),      # venom mid
    "v": (0xAE, 0xEA, 0x00, 255),      # venom main
    "V": (0xD4, 0xFF, 0x3D, 255),      # venom highlight
    # bruise purple  #8E24AA
    "p": (0x5E, 0x16, 0x70, 255),
    "P": (0x8E, 0x24, 0xAA, 255),
    "u": (0xB8, 0x4F, 0xD0, 255),
    # wolf greys
    "d": (0x2E, 0x31, 0x36, 255),
    "e": (0x4A, 0x4F, 0x55, 255),
    "f": (0x6A, 0x71, 0x78, 255),
    "w": (0x8A, 0x92, 0x9A, 255),
    # archer base — hunter green #2E7D32 (archer.vfx.md primary), value-ramped so the
    # LIT face clears the §5.4 contrast floor (>=40% value vs the #1E2126 field) while the
    # canonical #2E7D32 rides the shadow side.
    "n": (0x1C, 0x52, 0x20, 255),      # forest dark
    "N": (0x2E, 0x7D, 0x32, 255),      # hunter green #2E7D32 (canonical -> shadow side)
    "o": (0x4F, 0xB6, 0x5A, 255),      # lit face (L~146, ~44% value vs field)
    "O": (0x86, 0xDC, 0x90, 255),      # highlight
    # archer sharp gold #FFC400 — the "sharp-eye" glint accent (<=25% of lit px, marks
    # the action point: the driven point / the lead arrowhead)
    "z": (0xC7, 0x92, 0x0A, 255),      # gold shadow
    "y": (0xFF, 0xC4, 0x00, 255),      # sharp gold #FFC400
    "Y": (0xFF, 0xE4, 0x7A, 255),      # gold highlight
    # Minecraft-arrow neutrals (Pin Shot): oak-wood shaft + pale feather fletch
    "t": (0x4E, 0x38, 0x1E, 255),      # wood dark
    "T": (0x82, 0x60, 0x38, 255),      # wood light (shaft center)
    "S": (0xB4, 0x8A, 0x54, 255),      # oak highlight (sunlit shaft core; clears §5.4)
    "W": (0xEC, 0xE9, 0xDE, 255),      # bright feather (b = #A89C80 is the feather shadow)
    # dark inner field  #1E2126
    "#": (0x1E, 0x21, 0x26, 255),
    "x": (0x16, 0x18, 0x1C, 255),      # field vignette (darker)
}

FIELD = PAL["#"]
FIELD_DARK = PAL["x"]
ACCENT = PAL["v"]                       # Hunter class accent (ult keyline / pip)
PURE_BLACK = (0, 0, 0, 255)            # true black for stat-bar frames + icon outlines
                                        # (the heart/food source art outlines are pure black;
                                        # PAL["k"] is a softer near-black that read as "no outline")

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def img(w, h):
    return Image.new("RGBA", (w, h), T)

def from_map(rows):
    """Build an RGBA image from a list of equal-length legend strings."""
    h = len(rows)
    w = max(len(r) for r in rows)
    im = img(w, h)
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            px[x, y] = PAL.get(ch, T)
    return im

def paste(dst, src, x, y):
    dst.alpha_composite(src, (x, y))

def scale(im, n):
    return im.resize((im.width * n, im.height * n), Image.NEAREST)

# Icons are authored NATIVELY at 32x32 (ICON_ART, adopted 2026-07-14), never upscaled.
# The one-shot upscale2x() that promoted the pre-adoption 16x16 art was deleted 2026-07-28:
# that migration is finished, nothing referenced it, and scale(im, 2) covers the general case.

def save(im, path):
    im.save(path)
    return path

# ---------------------------------------------------------------------------
# Frames  (24x24 base/subclass; peaked keystone for ults)
# HUD_AND_ICONS §4: outer rim -> weathered-iron channel -> bone keyline -> field
# ---------------------------------------------------------------------------
TILE = 24          # base/subclass tile size
ART = 16           # FRAME inner-field size (shared hunter/stat chrome — unchanged)
ART_OFF = 4        # art offset inside a 24px tile (rim+channel+keyline = 4px)
# Ultimate keystone: ~15% larger than TILE, plus a peaked top edge (§4). ult_frame() is the
# only consumer — these live here, beside the tile geometry they scale against, rather than
# as bare literals inside the drawing code.
ULT_W = 28              # keystone body width
ULT_PEAK = 5            # height of the peak above the body
ULT_H = ULT_W + ULT_PEAK  # full image height (33)
# Ability-icon ART is authored at 32x32 as of 2026-07-14 (was 16x16) — see the
# legendcraft-icon skill + HUD_AND_ICONS.md §5. ART (16) stays the frame field size the
# hunter/stat chrome is built around; the frame/HUD layer bumps its field to ICON_ART when
# the real 32px per-class icons get wired into BetterHud. New icon maps are 32 rows x 32 chars.
ICON_ART = 32      # ability-icon art size

def _rect(dr, x0, y0, x1, y1, color):
    dr.rectangle([x0, y0, x1, y1], outline=color)

def _field(im, x0, y0, size):
    """Dark vignetted inner field."""
    px = im.load()
    for yy in range(size):
        for xx in range(size):
            edge = min(xx, yy, size - 1 - xx, size - 1 - yy)
            px[x0 + xx, y0 + yy] = FIELD_DARK if edge == 0 else FIELD

def base_frame(rivets=False):
    im = img(TILE, TILE)
    dr = ImageDraw.Draw(im)
    # outer near-black rim
    _rect(dr, 0, 0, TILE - 1, TILE - 1, PAL["k"])
    # 2px weathered-iron channel
    _rect(dr, 1, 1, TILE - 2, TILE - 2, PAL["I"])
    _rect(dr, 2, 2, TILE - 3, TILE - 3, PAL["I"])
    # bevel: light top/left, dark bottom/right on the iron channel
    px = im.load()
    for t in (1, 2):
        for a in range(t, TILE - t):
            px[a, t] = PAL["L"]          # top
            px[t, a] = PAL["L"]          # left
            px[a, TILE - 1 - t] = PAL["i"]  # bottom
            px[TILE - 1 - t, a] = PAL["i"]  # right
    # bone-parchment keyline
    _rect(dr, 3, 3, TILE - 4, TILE - 4, PAL["B"])
    # inner field
    _field(im, ART_OFF, ART_OFF, ART)
    if rivets:
        for (cx, cy) in ((2, 2), (TILE - 3, 2), (2, TILE - 3), (TILE - 3, TILE - 3)):
            px[cx, cy] = PAL["H"]
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if 0 <= cx + dx < TILE and 0 <= cy + dy < TILE:
                    px[cx + dx, cy + dy] = PAL["i"]
    return im

def ult_frame():
    """Keystone: ~15% larger (28px) with a peaked top edge + class-accent keyline.

    There is no universal locked frame variant: a locked ultimate keeps the normal
    keystone and swaps its ART to the per-ult `_locked` PNG (state_locked) instead —
    the slot is a promise, not a different frame (HUD_AND_ICONS.md §3)."""
    size, peak = ULT_W, ULT_PEAK
    W, H = size, ULT_H
    im = img(W, H)
    dr = ImageDraw.Draw(im)
    top = peak  # frame body starts below the peak
    # body frame
    _rect(dr, 0, top, W - 1, H - 1, PAL["k"])
    _rect(dr, 1, top + 1, W - 2, H - 2, PAL["I"])
    _rect(dr, 2, top + 2, W - 3, H - 3, PAL["I"])
    px = im.load()
    for t in (1, 2):
        for a in range(t, W - t):
            px[a, top + t] = PAL["L"]
            px[a, H - 1 - t] = PAL["i"]
        for a in range(top + t, H - t):
            px[t, a] = PAL["L"]
            px[W - 1 - t, a] = PAL["i"]
    # bone keyline
    _rect(dr, 3, top + 3, W - 4, H - 4, PAL["B"])
    # class-accent keyline (READY only) just inside the bone line
    _rect(dr, 4, top + 4, W - 5, H - 5, ACCENT)
    # inner field (16x16 centered horizontally, sits in body)
    foff_x = (W - ART) // 2
    foff_y = top + (size - ART) // 2
    _field(im, foff_x, foff_y, ART)
    # rivets
    for (cx, cy) in ((2, top + 2), (W - 3, top + 2), (2, H - 3), (W - 3, H - 3)):
        px[cx, cy] = PAL["H"]
    # peak: a small iron gable rising to a point above center
    cx = W // 2
    for yy in range(peak):
        half = yy  # widens downward
        for xx in range(cx - half, cx + half):
            col = PAL["k"] if (xx in (cx - half, cx + half - 1)) else PAL["I"]
            if yy == 0:
                col = PAL["k"]
            px[xx, yy] = col
    return im, (foff_x, foff_y)

# ---------------------------------------------------------------------------
# Indicators: resource pip, charge pips, keybind glyphs
# ---------------------------------------------------------------------------
def resource_pip(color=ACCENT):
    hi = PAL["V"]
    rows = [
        "..k..",
        ".kck.",
        "kcHck",
        ".kck.",
        "..k..",
    ]
    im = img(5, 5)
    px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "k":
                px[x, y] = PAL["k"]
            elif ch == "c":
                px[x, y] = color
            elif ch == "H":
                px[x, y] = hi
    return im

def charge_pip(state):
    """state: 'full' venom, 'reloading' half, 'empty' dark."""
    if state == "full":
        c, h = PAL["v"], PAL["V"]
    elif state == "reloading":
        c, h = PAL["g"], PAL["G"]
    else:
        c, h = PAL["i"], PAL["I"]
    rows = ["kkk", "khk", "kkk"]
    im = img(3, 3)
    px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            px[x, y] = PAL["k"] if ch == "k" else (h if ch == "h" else c)
    # fill body
    px[1, 1] = h
    for (x, y) in ((1, 0), (0, 1), (2, 1), (1, 2)):
        px[x, y] = c
    return im

def _gold_pip(px, x0, state):
    """Stamp one 2x2 gold pip at (x0,0). 'full' = lit gold, 'empty' = dulled (a spent charge)."""
    if state == "full":
        c, h = (0xE8, 0xB0, 0x2A, 255), (0xFF, 0xDC, 0x5A, 255)   # lit gold + highlight
    else:
        c, h = (0x46, 0x3E, 0x1E, 255), (0x5E, 0x54, 0x2C, 255)   # dulled/spent gold
    px[x0, 0] = h
    px[x0 + 1, 0] = c; px[x0, 1] = c; px[x0 + 1, 1] = c

def charge_row_gold(n_full):
    """One 8x2 gold charge row: SKILL_MAX_PIPS pips (2px each + 1px gaps = 8px, EVEN so the row sits
    EXACTLY centred in the 16px field), the first n_full lit and the rest dulled. One sprite per
    charge count because BetterHud layout `conditions:` only support == / != (not >= / <=), so the
    live pip pattern is selected by gating each row image on `<slot>_charges == n`."""
    w = SKILL_PIP * SKILL_MAX_PIPS + SKILL_PIP_GAP * (SKILL_MAX_PIPS - 1)
    im = img(w, SKILL_PIP)
    px = im.load()
    for i in range(SKILL_MAX_PIPS):
        _gold_pip(px, i * (SKILL_PIP + SKILL_PIP_GAP), "full" if i < n_full else "empty")
    return im

# tiny 3x5 pixel font (bone parchment) for keybind glyphs + numerals
FONT3x5 = {
    "L": ["X..", "X..", "X..", "X..", "XXX"],
    "R": ["XX.", "X.X", "XX.", "X.X", "X.X"],
    "Q": ["XXX", "X.X", "X.X", "XXX", "..X"],
    "F": ["XXX", "X..", "XXX", "X..", "X.."],
    "0": ["XXX", "X.X", "X.X", "X.X", "XXX"],
    "1": [".X.", "XX.", ".X.", ".X.", "XXX"],
    "2": ["XXX", "..X", "XXX", "X..", "XXX"],
    "3": ["XXX", "..X", ".XX", "..X", "XXX"],
    "4": ["X.X", "X.X", "XXX", "..X", "..X"],
    "5": ["XXX", "X..", "XXX", "..X", "XXX"],
    "6": ["XXX", "X..", "XXX", "X.X", "XXX"],
    "7": ["XXX", "..X", "..X", "..X", "..X"],
    "8": ["XXX", "X.X", "XXX", "X.X", "XXX"],
    "9": ["XXX", "X.X", "XXX", "..X", "XXX"],
    "/": ["..X", "..X", ".X.", "X..", "X.."],
    " ": ["...", "...", "...", "...", "..."],
}

def glyph(text, color=PAL["B"], outline=PAL["k"]):
    """Render text in the 3x5 font with a 1px outline."""
    gap = 1
    glyphs = [FONT3x5[c] for c in text]
    inner_w = sum(3 for _ in glyphs) + gap * (len(glyphs) - 1)
    W, H = inner_w + 2, 5 + 2
    core = img(W, H)
    px = core.load()
    x = 1
    for g in glyphs:
        for yy, r in enumerate(g):
            for xx, ch in enumerate(r):
                if ch == "X":
                    px[x + xx, 1 + yy] = color
        x += 3 + gap
    # outline: any transparent px orthogonally adjacent to a lit px -> outline
    out = core.copy()
    opx = out.load()
    for y in range(H):
        for x in range(W):
            if px[x, y] == T:
                lit = False
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and px[nx, ny] not in (T, outline):
                        lit = True
                        break
                if lit:
                    opx[x, y] = outline
    return out

def mouse(side):
    """Pixel mouse with the active button lit venom-green (side='left'|'right')."""
    left_on = side == "left"
    A = ("v" if left_on else "L")   # left button
    B = ("L" if left_on else "v")   # right button
    Ah = ("V" if left_on else "H")  # button top-highlight
    Bh = ("H" if left_on else "V")
    rows = [
        ".kkkkk.",
        f"k{A}{Ah}k{Bh}{B}k",
        f"k{A}{A}k{B}{B}k",
        "kIIIIIk",
        "kILLLIk",
        "kIIIIIk",
        ".kIIIk.",
        "..kkk..",
    ]
    im = img(7, 8)
    px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            px[x, y] = PAL.get(ch, T)
    return im

# ---------------------------------------------------------------------------
# UX-2 — per-slot input-hint glyphs (shared chrome; HUD_AND_ICONS.md §3, Plans/ICON_CHECKLIST
# "Player UX"). Every skill tile shows its cast input just below the frame: Sneak + Left /
# Right / Q / F for slot1 / slot2 / slot3 / ult. The glyph is fixed by the input scheme, NOT
# the class, so these four sprites are shared across all 24 classes (like the frame + charge
# pips), gated only on slot presence (ult keeps its ⇧F even while locked, to teach the button).
#
# Style (user-directed, ref-image matched): white "keycap" glyphs — F/Q are white keycaps with
# the letter in dark NEGATIVE space; the mouse is a HOLLOW white keycap at the SAME footprint
# with a 2px red ACTIVE-button click; shift is a bold filled up-arrow. Each glyph is authored at
# KEY_SS x (crisp hi-res), 1px near-black outlined, corners chamfered — and the sprite is left at
# that hi-res and DOWNSCALED BY BETTERHUD via `setting: {scale: KEY_SCALE}` (the ability-icon
# pipeline), NOT box-downscaled in Python (which muddied the negative-space letters). KEY_SCALE is
# the one knob for on-screen size. White keys read against the STEEL frame keyline (skill_frame
# uses PAL['I']) so they don't clash with the old bone keyline.
# ---------------------------------------------------------------------------
KEY_WHITE = (0xF2, 0xF2, 0xF2, 255)     # keycap face / arrow
KEY_INK = (0x1A, 0x1C, 0x20, 255)       # dark negative-space letters + 1px outline
KEY_RED = (0xC4, 0x3B, 0x2E, 255)       # active mouse-button click #C43B2E
KEY_SS = 2                              # author (and ship) the sprite at this hi-res factor
KEY_SCALE = 0.42                        # BetterHud render scale of the hi-res sprite (on-screen size knob)
KEY_GAP = 4                             # hi-res px between the shift glyph and the button glyph (~2px shown)
KEY_DROP = 2                            # glyph display-bottom this far below the tile bottom (raised again 1px)

_SHIFT_ARROW = ["..M..", ".MMM.", "MMMMM", ".MMM.", ".MMM.", ".MMM."]        # bold filled up-arrow
_F_KEY = ["XXXXX", "X...X", "X.XXX", "X..XX", "X.XXX", "X.XXX", "XXXXX"]      # white cap, neg-space F
_Q_KEY = ["XXXXX", "X...X", "X.X.X", "X.X.X", "X...X", "XXX.X", "XXXXX"]      # white cap, neg-space Q

def _key_up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)

def _key_outline(im):
    """Add a 1px KEY_INK 4-directional outline just OUTSIDE the opaque silhouette."""
    w, h = im.width, im.height
    out = im.copy()
    ip, op = im.load(), out.load()
    for y in range(h):
        for x in range(w):
            if ip[x, y][3] == 0:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and ip[nx, ny][3] != 0:
                        op[x, y] = KEY_INK
                        break
    return out

def _key_cut(im):
    """Knock out each corner's KEY_SS x KEY_SS block (transparent) — a 1px display chamfer."""
    px = im.load()
    w, h = im.width, im.height
    for cx, cy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        sx = 1 if cx == 0 else -1
        sy = 1 if cy == 0 else -1
        for dx in range(KEY_SS):
            for dy in range(KEY_SS):
                px[cx + sx * dx, cy + sy * dy] = T
    return im

def _key_from(grid, mapping):
    h, w = len(grid), len(grid[0])
    im = img(w, h)
    px = im.load()
    for y, r in enumerate(grid):
        for x, ch in enumerate(r):
            c = mapping.get(ch)
            if c is not None:
                px[x, y] = c
    return im

def _key_letter(grid):
    """White keycap + dark negative-space letter, authored KEY_SS x -> outlined -> chamfered (hi-res)."""
    m = {"X": KEY_WHITE, ".": KEY_INK}
    return _key_cut(_key_outline(_key_up(_key_from(grid, m), KEY_SS)))

def _key_shift():
    """Bold filled white up-arrow (transparent field), hi-res."""
    m = {"M": KEY_WHITE}
    return _key_outline(_key_up(_key_from(_SHIFT_ARROW, m), KEY_SS))

def _key_mouse(side):
    """Mouse AS a hollow keycap at the F/Q footprint: white frame, transparent body, a 2px
    red click on the active side (extending into the middle column). Hi-res."""
    left = side == "left"
    lb = "R" if left else "."   # active-side outer column
    rb = "." if left else "R"
    grid = ["XXXXX", f"X{lb}R{rb}X", f"X{lb}R{rb}X", "X...X", "X...X", "X...X", "XXXXX"]
    m = {"X": KEY_WHITE, "R": KEY_RED}   # "." stays transparent (hollow)
    return _key_cut(_key_outline(_key_up(_key_from(grid, m), KEY_SS)))

def _key_button(slot):
    if slot == "slot1":
        return _key_mouse("left")
    if slot == "slot2":
        return _key_mouse("right")
    if slot == "slot3":
        return _key_letter(_Q_KEY)
    if slot == "ult":
        return _key_letter(_F_KEY)
    raise ValueError(f"no input glyph for slot {slot!r}")

def input_glyph(slot):
    """Composed shift + button input-hint sprite at KEY_SS x (hi-res; BetterHud scales it down
    at render via KEY_SCALE). Both bottom-align to a shared baseline. Returns (image, height)."""
    sh = _key_shift()
    btn = _key_button(slot)
    base = max(sh.height, btn.height)
    im = img(sh.width + KEY_GAP + btn.width, base)
    im.alpha_composite(btn, (sh.width + KEY_GAP, base - btn.height))
    im.alpha_composite(sh, (0, base - sh.height))
    return im, base

# ---------------------------------------------------------------------------
# (Ability-icon pixel maps used to live here.) Icon ART is authored on disk now — see the
# "Build & export" note below. During a single legendcraft-icon session an icon's pixel map
# may be pasted in here transiently to emit its PNG, then deleted. No icon maps are kept.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# State transforms  (HUD_AND_ICONS §3 icon state machine)
# ---------------------------------------------------------------------------
def _lum(r, g, b):
    return int(0.299 * r + 0.587 * g + 0.114 * b)

def desaturate(im, amount):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            l = _lum(r, g, b)
            px[x, y] = (
                int(r + (l - r) * amount),
                int(g + (l - g) * amount),
                int(b + (l - b) * amount),
                a,
            )
    return out

def brightness(im, mul, blue_shift=0):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            px[x, y] = (
                min(255, int(r * mul)),
                min(255, int(g * mul)),
                min(255, int(b * mul + blue_shift)),
                a,
            )
    return out

# EXTERNAL API -- do not delete as "unreferenced". state_cooldown / state_starved /
# state_locked have no caller inside this module by design: the legendcraft-icon skill
# imports them directly (`from generate_hud import state_cooldown, state_starved,
# state_locked`, SKILL.md step 6) to bake an icon's state variants at authoring time.
# from_map/PAL are likewise kept as the skill's documented legacy hand-authoring path.
def state_cooldown(art):
    # desaturate ~70% + darken
    return brightness(desaturate(art, 0.7), 0.6)

def state_starved(art):
    # fully desaturate + cool-dim (dark, slight blue)
    return brightness(desaturate(art, 1.0), 0.5, blue_shift=14)

# Locked-state split: pixels brighter than this are motif and black out to the
# silhouette; anything at or below it is the icon's painted ambient background and is
# dimmed instead. Sits between the image2 murk fields (values ≲ 60) and every motif's
# lit midtones (≳ 70). Transparent-background icons are unaffected (their motif is
# their only opaque content).
LOCKED_MOTIF_VALUE = 68
LOCKED_BG_DIM = 0.55

def state_locked(art):
    # silhouette-black promise (HUD_AND_ICONS.md §3): the motif blacks out to a
    # silhouette while an opaque painted background survives, dimmed — so image2-era
    # full-frame icons keep their field instead of collapsing to one black tile.
    out = art.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if max(r, g, b) > LOCKED_MOTIF_VALUE:
                px[x, y] = (0x0E, 0x0F, 0x12, a)
            else:
                px[x, y] = (int(r * LOCKED_BG_DIM), int(g * LOCKED_BG_DIM),
                            int(b * LOCKED_BG_DIM), a)
    return out

# ---------------------------------------------------------------------------
# Live state OVERLAYS (HUD_AND_ICONS.md §3) — transparent PNGs BetterHud composites
# over the ready icon art. The cooldown shroud is ONE full-field dark wash revealed
# radially by a `split-type: circle` listener (driven by the slot's _cd_percent), so
# the League sweep is native BetterHud, not baked frames. The out-of-mana wash is a
# flat soft-red overlay gated by a layout condition.
# ---------------------------------------------------------------------------
CD_SHROUD = (0x08, 0x09, 0x0C, 170)     # dark shroud colour, ~67% alpha
OOM_SOFT = (0xFF, 0x6B, 0x6B, 90)       # soft light-red out-of-mana wash, ~35% alpha
CD_SPLIT = 36                           # circle-split slices (angular resolution of the sweep)

def cd_shroud():
    """The cooldown shroud: a uniform dark wash over the whole 16x16 field. BetterHud
    reveals it radially via a `split-type: circle` listener driven by the slot's
    `_cd_percent` placeholder (100 -> whole icon dark at cast, shrinking to 0 as it
    expires — the League sweep), so the PNG itself is just the full overlay, not frames."""
    im = img(ART, ART)
    px = im.load()
    for yy in range(ART):
        for xx in range(ART):
            px[xx, yy] = CD_SHROUD
    return im

def oom_overlay():
    """Out-of-mana overlay: a flat soft light-red wash over the whole field."""
    im = img(ART, ART)
    px = im.load()
    for yy in range(ART):
        for xx in range(ART):
            px[xx, yy] = OOM_SOFT
    return im

def icon_placeholder():
    """Solid near-black icon background. It backs EVERY skill slot: for undrawn skills it's the
    whole icon, and behind each (transparent-background) real icon it makes the art sit on black
    instead of a gem. Authored at ICON_ART, shown at 16px (scale 0.5)."""
    n = ICON_ART
    im = img(n, n)
    px = im.load()
    for yy in range(n):
        for xx in range(n):
            px[xx, yy] = (0x10, 0x11, 0x15, 255)   # near-black icon backdrop
    return im

# --- outlined-digit bitmap font (BetterHud text has no native outline) ------------------
NUM_CHARS = "0123456789."
def _outlined_digit(ch):
    """One glyph: white digit (3x5) with a 1px PURE_BLACK 8-directional outline."""
    g = ["...", "...", "...", "...", ".X."] if ch == "." else FONT3x5[ch]
    W, H = 3 + 2, 5 + 2
    core = img(W, H)
    px = core.load()
    for yy, row in enumerate(g):
        for xx, c in enumerate(row):
            if c == "X":
                px[1 + xx, 1 + yy] = (255, 255, 255, 255)
    out = core.copy()
    opx = out.load()
    for y in range(H):
        for x in range(W):
            if px[x, y] == T:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and px[nx, ny] != T:
                        opx[x, y] = PURE_BLACK
                        break
    return out

NUM_CELL_W = 7          # uniform grid cell (5px outlined glyph + right pad); trailing pad is trimmed
def num_outline_font():
    """Bitmap-font strip of white outlined digits 0-9 and '.', one per uniform cell — used by the
    HUD cooldown/charge numerals so they read over any art. BetterHud maps NUM_CHARS onto it."""
    im = img(NUM_CELL_W * len(NUM_CHARS), 7)
    for i, ch in enumerate(NUM_CHARS):
        paste(im, _outlined_digit(ch), i * NUM_CELL_W, 0)
    return im

def charge_badge():
    """A small gray rounded badge that the charge count sits on, pushed just outside the icon's
    top-right corner so it never crowds the centered recharge numeral."""
    w, h = 9, 9
    im = img(w, h)
    px = im.load()
    for yy in range(h):
        for xx in range(w):
            edge = min(xx, yy, w - 1 - xx, h - 1 - yy)
            if (xx in (0, w - 1)) and (yy in (0, h - 1)):
                continue                                   # rounded corners
            px[xx, yy] = PURE_BLACK if edge == 0 else (PAL["I"] if edge == 1 else PAL["i"])
    return im

def skill_field():
    """A compact 16x16 dark icon backing (the frame's inner field, minus the tall
    24-33px iron frame). BetterHud renders HUD elements as font glyphs and the tall
    frames appear to exceed a glyph-height limit that corrupts the HUD font, so the
    small-icon row backs each skill with just this short field for contrast."""
    im = img(ART, ART)
    px = im.load()
    for yy in range(ART):
        for xx in range(ART):
            edge = min(xx, yy, ART - 1 - xx, ART - 1 - yy)
            px[xx, yy] = PAL["k"] if edge == 0 else (FIELD_DARK if edge == 1 else FIELD)
    return im

# The HUD skill-icon frame: a compact 22px tile with a clean 3px border — 1px PURE_BLACK
# outline (matching the other HUD elements), 1px beveled iron/gray, 1px bone/tan keyline —
# around the shared 16px art field. Smaller than the old 4px iron frame so icons sit better
# next to the stat bars (user call). Its own constants so it doesn't disturb TILE/ART_OFF.
SKILL_TILE = 22
SKILL_ART_OFF = 3

def skill_frame():
    t = SKILL_TILE
    im = img(t, t)
    dr = ImageDraw.Draw(im)
    _rect(dr, 0, 0, t - 1, t - 1, PURE_BLACK)          # 1px pure-black outline
    px = im.load()
    for a in range(1, t - 1):                           # 1px beveled iron/gray ring
        px[a, 1] = PAL["L"]; px[1, a] = PAL["L"]        # top / left = light
        px[a, t - 2] = PAL["i"]; px[t - 2, a] = PAL["i"]  # bottom / right = dark
    _rect(dr, 2, 2, t - 3, t - 3, PAL["I"])            # 1px steel keyline (UX-2: white keys don't clash)
    _field(im, SKILL_ART_OFF, SKILL_ART_OFF, ART)      # 16px dark art field
    return im

# Cast-deny fade-in (UX-1a, HUD_AND_ICONS.md §3): a translucent-white wash that fades IN over the
# ability, played once per denied cast via a BetterHud `type: sequence` (animation-type: play_once).
# Each frame is icon-sized (32px ICON_ART, shown at scale 0.5 and placed at the icon's own ax/ay) so
# the wash covers the skill icon EXACTLY — not the frame border. Peak ~45% white so the icon still
# reads under it. Alpha ramps 0→DENY_WASH_ALPHA across DENY_FADE_FRAMES.
DENY_FADE_FRAMES = 4
DENY_WASH_ALPHA = 115

def deny_flash_frame(i):
    """Frame i of the deny fade-in: a 32px full-square translucent white whose alpha steps up with i."""
    a = round(DENY_WASH_ALPHA * (i + 1) / DENY_FADE_FRAMES)
    im = img(ICON_ART, ICON_ART)
    px = im.load()
    for y in range(ICON_ART):
        for x in range(ICON_ART):
            px[x, y] = (0xFF, 0xFF, 0xFF, a)
    return im

# ---------------------------------------------------------------------------
# Build & export
# ---------------------------------------------------------------------------
# Ability-icon ART is no longer generated here — each icon's PNG is authored/edited directly
# on disk under hud/skill-icons/<class>/ (via the legendcraft-icon skill) and IS the
# source of truth; this generator must never overwrite it. A per-icon session may add a pixel
# map above just long enough to emit that one PNG, then removes it — nothing icon-specific
# stays behind. Permanent residents are SHARED chrome only: frames, pips, charge/keybind
# glyphs, the cooldown shroud, fonts, badges, stat bars, and the BetterHud wiring that POINTS
# at the on-disk icon PNGs. Real per-class icons flow through hud_icon_map.CLASS_SKILL_ICONS
# (registered as lc_hud_<class>_<icon>); HUNTER below is just the NAME(s) the legacy Hunter
# BetterHud demo (legendcraft-hunter.yml) references by path — it carries no art.
HUNTER = ["ensnaring_trap"]

def export_true_res():
    # frames
    save(base_frame(rivets=False), os.path.join(DIRS["frames"], "frame_base.png"))
    save(base_frame(rivets=True), os.path.join(DIRS["frames"], "frame_subclass.png"))
    uf, _ = ult_frame()
    save(uf, os.path.join(DIRS["frames"], "frame_ult.png"))
    # indicators
    save(resource_pip(), os.path.join(DIRS["ind"], "pip_venom.png"))
    for s in ("full", "reloading", "empty"):
        save(charge_pip(s), os.path.join(DIRS["ind"], f"charge_{s}.png"))
    for k in range(SKILL_MAX_PIPS + 1):   # gold charge-row sprites, one per charge count (0..max)
        save(charge_row_gold(k), os.path.join(DIRS["ind"], f"charge_row_{k}.png"))
    save(mouse("left"), os.path.join(DIRS["ind"], "key_mouse_left.png"))
    save(mouse("right"), os.path.join(DIRS["ind"], "key_mouse_right.png"))
    for key in ("Q", "F"):
        save(glyph(key), os.path.join(DIRS["ind"], f"key_{key}.png"))
    # UX-2 per-slot input hints (Sneak + L/R/Q/F), shared across all classes
    for slot in SLOT_IDS:
        sprite, _ = input_glyph(slot)
        save(sprite, os.path.join(DIRS["ind"], f"input_{slot}.png"))
    # live state overlays (shared across all classes — composited over any icon art)
    save(cd_shroud(), os.path.join(DIRS["ind"], "cd_shroud.png"))
    save(oom_overlay(), os.path.join(DIRS["ind"], "oom_soft.png"))
    for i in range(DENY_FADE_FRAMES):
        save(deny_flash_frame(i), os.path.join(DIRS["ind"], f"deny_fade_{i}.png"))
    save(skill_field(), os.path.join(DIRS["ind"], "field.png"))
    save(icon_placeholder(), os.path.join(DIRS["ind"], "icon_placeholder.png"))
    save(skill_frame(), os.path.join(DIRS["frames"], "skill_frame.png"))
    save(num_outline_font(), os.path.join(DIRS["font"], "num_outline.png"))
    save(charge_badge(), os.path.join(DIRS["ind"], "charge_badge.png"))

# ---------------------------------------------------------------------------
# BetterHud config export (schema verified against BetterHud 2.0.0 on 26.1.2)
#
# Emits images/layouts/huds YAML with pixel offsets computed from the SAME
# geometry the preview compositor uses — the YAML can never drift from the art.
# Layout entries are numbered maps; layouts use top-left anchored x/y; the hud
# places the layout via gui (percent) + pixel offsets.
#
# Spike scope: static READY-state row + a states demo strip. State-driven
# layer switching needs `conditions:` on `papi:` placeholders — blocked on
# PlaceholderAPI + the LegendCraft-Classes placeholder contract (see README).
# ---------------------------------------------------------------------------
BH_DIR = os.path.join(ROOT, "betterhud")

# (This block held ULT_W/ULT_H/ULT_PEAK + ULT_ART/SLOT_PITCH/ULT_GAP for the retired
#  _tile_elems emitter. ULT_ART/SLOT_PITCH/ULT_GAP were deleted with it 2026-07-28; the
#  ULT_* keystone dimensions moved up beside TILE/ART, next to ult_frame(), their only
#  real consumer. framed_row derives its own geometry from SKILL_TILE and reads no ULT_*.)

def _bh_images_yml():
    reg = {
        "lc_field": "legendcraft/indicators/field.png",
        "lc_skill_frame": "legendcraft/frames/skill_frame.png",
        "lc_frame_subclass": "legendcraft/frames/frame_subclass.png",
        "lc_frame_ult": "legendcraft/frames/frame_ult.png",
        "lc_pip_venom": "legendcraft/indicators/pip_venom.png",
        "lc_charge_full": "legendcraft/indicators/charge_full.png",
        "lc_charge_reloading": "legendcraft/indicators/charge_reloading.png",
        "lc_charge_empty": "legendcraft/indicators/charge_empty.png",
        **{f"lc_charge_row_{k}": f"legendcraft/indicators/charge_row_{k}.png"
           for k in range(SKILL_MAX_PIPS + 1)},
        "lc_key_mouse_left": "legendcraft/indicators/key_mouse_left.png",
        "lc_key_mouse_right": "legendcraft/indicators/key_mouse_right.png",
        "lc_key_q": "legendcraft/indicators/key_Q.png",
        "lc_key_f": "legendcraft/indicators/key_F.png",
        "lc_charge_badge": "legendcraft/indicators/charge_badge.png",
    }
    for skill in HUNTER:
        for state in ("", "_cooldown", "_starved"):
            reg[f"lc_hunter_{skill}{state}"] = f"legendcraft/skill-icons/hunter/{skill}{state}.png"
    # out-of-mana wash (single overlay; gated per slot by a layout condition)
    reg["lc_oom_soft"] = "legendcraft/indicators/oom_soft.png"
    lines = ["# GENERATED by assets/tools/generate_hud.py -- do not hand-edit.",
             "# Image registry for the LegendCraft skill-casting HUD (BetterHud 2.0.0 schema)."]
    for name, file in reg.items():
        lines += [f"{name}:", "  type: single", f"  file: {file}", ""]
    # UX-2 input hints (Sneak + L/R/Q/F) — shared chrome, one sprite per slot. Shipped at KEY_SS x
    # (hi-res) and DOWNSCALED BY BETTERHUD via setting.scale=KEY_SCALE (same as the ability icons),
    # so the negative-space keycaps stay crisp instead of muddying under a Python box-downscale.
    for slot in SLOT_IDS:
        lines += [f"lc_input_{slot}:", "  type: single",
                  f"  file: legendcraft/indicators/input_{slot}.png",
                  "  setting:", f"    scale: {KEY_SCALE}", ""]
    # Cooldown shroud: ONE circle-split listener per slot, revealed by the slot's
    # _cd_percent (0-100). BetterHud's SplitType.CIRCLE gives the League radial sweep
    # natively, so each slot is a single layout element instead of 12 stacked frames
    # (which overflowed the single-line HUD glyph encoding and dumped glyphs at the top).
    for slot in SLOT_IDS:
        lines += [
            f"lc_cd_shroud_{slot}:",
            "  type: listener",
            "  file: legendcraft/indicators/cd_shroud.png",
            f"  split: {CD_SPLIT}",
            "  split-type: circle",
            "  setting:",
            "    listener:",
            "      class: placeholder",
            f'      value: "(number)papi:legendcraft_{slot}_cd_percent"',
            "      max: 100",
            "",
        ]
    # Cast-deny fade-in (UX-1a): a `type: sequence` play_once animation — the translucent-white wash
    # fades IN across DENY_FADE_FRAMES, played once each time a slot's `<slot>_flash` flips to `deny`.
    # scale 0.5 (32px art shown at 16px) matches the icon exactly; `path:N` sets each frame's tick hold.
    lines += ["lc_deny_flash:", "  type: sequence", "  files:"]
    lines += [f'    - "legendcraft/indicators/deny_fade_{i}.png:1"' for i in range(DENY_FADE_FRAMES)]
    lines += ["  setting:", "    scale: 0.5", "    animation-type: play_once", ""]
    # Ability art is authored at 32px (ICON_ART) and displayed at 16px in the frame field via
    # BetterHud `setting: {scale: 0.5}` (crisper at the GUI scales players run). The placeholder
    # and every real per-class icon (from hud_icon_map) register the same way. Real icons use a
    # distinct lc_hud_<class>_<icon> name so they never collide with the icon team's lc_hunter_*.
    def scaled(name, file):
        return [f"{name}:", "  type: single", f"  file: {file}", "  setting:", "    scale: 0.5", ""]
    lines += scaled("lc_icon_placeholder", "legendcraft/indicators/icon_placeholder.png")
    for classid, icons in CLASS_SKILL_ICONS.items():
        for icon in icons:
            if icon:
                lines += scaled(f"lc_hud_{classid}_{icon}",
                                f"legendcraft/skill-icons/{classid}/{icon}.png")
        # A subclass ultimate also registers its `_locked` art (state_locked output) — the
        # 4-slot row draws it over the ready art while `legendcraft_ult_state == locked`.
        if len(icons) == 4 and icons[3]:
            lines += scaled(f"lc_hud_{classid}_{icons[3]}_locked",
                            f"legendcraft/skill-icons/{classid}/{icons[3]}_locked.png")
    return "\n".join(lines)

# --- skill-row geometry, shared by the live framed row in the stat layout -----------
SKILL_NUM_SCALE = 0.38     # centered cooldown / recharge numeral (lc_stat_text)
# (SKILL_CHARGE_SCALE, a text scale for a numeric charge COUNT, was deleted 2026-07-28 --
#  unreferenced since the charge display became the lc_charge_row_* pip sprites.)
# RENDERED numeral height (post-scale), used to vertically centre it in the tile. lc_stat_text renders
# ~16.7px per scale unit (STAT_TEXT_H=5@0.30, STAT_LEVEL_H=7@0.42), so 0.38 -> ~6px. Centering on the
# raw 8px font height (the old value) sat the number ~1-2px high.
SKILL_TEXT_H = round(SKILL_NUM_SCALE * 16.7)
SKILL_PIP = 2              # gold charge-pip size (px); 3 pips + 2 gaps = 8px (even) -> exact centre
SKILL_PIP_GAP = 1          # gap between charge pips
SKILL_MAX_PIPS = 3         # charge pips in the top row (matches the trap's max charges)
# Class-agnostic ability-slot ids for the skill-casting HUD. Kept SEPARATE from the
# Hunter icon list (HUNTER, which the per-class icon work churns) so a change to the
# icons can't drop the HUD's cooldown-shroud registrations again.
SLOT_IDS = ["slot1", "slot2", "slot3", "ult"]
SKILL_FRAME_GAP = 2          # gap between framed skill tiles
SKILL_ROW_GAP = 3            # gap between the skill row's bottom and the stat block's top
VANILLA_ITEM_NAME_OFFSET_PX = 59  # previewed client lane centre, up from the screen bottom
SKILL_ROW_HOIST_PX = 20           # keeps the tile bottom 15px above the client item-name lane
SKILL_ROW_Y_PX = -(SKILL_TILE + SKILL_ROW_GAP + SKILL_ROW_HOIST_PX)
FEEDBACK_TEXT_SCALE = 0.50
FEEDBACK_TEXT_HEIGHT_PX = 8  # rendered default-bitmap text height at FEEDBACK_TEXT_SCALE
FEEDBACK_LINE_GAP_PX = 4     # clear air between the painted line and the icon-row top
FEEDBACK_LINE_Y_PX = SKILL_ROW_Y_PX - FEEDBACK_TEXT_HEIGHT_PX - FEEDBACK_LINE_GAP_PX

# --- Draw order inside one skill tile (HUD_AND_ICONS.md §3) ---------------------------
# BetterHud's `layer` is documented as "priority to display when overlapping. higher the
# number, the higher the priority" — but the docs do NOT define what happens when two
# elements share a value. So every overlay that MUST sit above another gets its own number
# rather than tying with it. This was a live bug: the cooldown shroud and the out-of-mana
# wash both sat at 4, leaving "does the resource tint show through the cooldown sweep?" to
# whatever order BetterHud happened to iterate in. §3's "Both" row requires the tint on top.
TILE_L_FRAME  = 1   # weathered-iron frame
TILE_L_FIELD  = 2   # near-black icon backing (and the placeholder art for undrawn skills)
TILE_L_ART    = 3   # the real per-class ability art
TILE_L_SHROUD = 4   # circle-split cooldown sweep — darkens the art beneath it
TILE_L_OOM    = 5   # out-of-mana tint — ABOVE the sweep, so both problems read at once
TILE_L_BADGE  = 6   # locked-ult art + charge pips: information, must survive both washes
TILE_L_DENY   = 7   # cast-deny flash: always the top of the tile
# Every `texts:` entry in this layout — the cooldown numeral, the ult's parchment "20", and
# the stat block's numerals. `layer` is a BetterHud COMMON option (it applies to all layout
# element types, not just images), and its default is 0 — which would nominally put the
# numeral BELOW the frame, field, art, shroud and tint. It renders today only because
# BetterHud happens to draw texts in a pass above images. That is exactly the undefined
# ordering these constants exist to remove, on the one element that has to stay readable
# through BOTH washes, so the numeral states its position instead of inheriting it.
TILE_L_TEXT   = 8   # above everything, including the deny flash — matches the observed order

# --- Health-bar affliction stack (Volya MMORPG HUD art, staged by stage_volya_hud.py) -------
# Layers 1..9 are spoken for by the stat block (1 channels / 2 fills / 3 icons) and the skill
# row (TILE_L_* above, 9 = input glyphs), so the affliction overlays start at 10. Each state
# gets its OWN number because several can be live at once and a tie is undefined: a burning,
# poisoned player must get one deterministic composite, not a random one. Bottom to top, the
# order is severity: a venom film, then flame, then frost, and wither over all of them because
# wither is the one that reads as "you are dying". Regeneration sits above the afflictions —
# it is the counter-signal and must be visible through them.
VIT_L_POISON  = 10
VIT_L_BURNING = 11
VIT_L_FREEZE  = 12
VIT_L_WITHER  = 13
VIT_L_REGEN   = 14
# Heart-icon states repeat that order in the icon column (they are opaque, so the top one wins).
VIT_L_ICON_POISON  = 15
VIT_L_ICON_BURNING = 16
VIT_L_ICON_FREEZE  = 17
VIT_L_ICON_WITHER  = 18
# UX-2 cast-hint keycaps. These straddle the tile's BOTTOM border, outside the 16px art field, so
# the frame is the only thing they overlap: the shroud, tint, locked badge and deny flash all draw
# inside the field, and the charge pips deliberately own the top edge. This carried a bare literal
# 6 when it was authored, which the layer pass has since given to TILE_L_BADGE — and a tie leaves
# BetterHud's draw order undefined, which is the whole failure that pass existed to remove. 9 keeps
# it above the keyline it outlines against without renumbering a single relation that pass fixed.
INPUT_L_GLYPH = 9

def export_betterhud():
    # Emits ONLY the shared image registry (legendcraft-hunter.yml) that the lc_stat skill
    # row references. The old spike HUD (lc_skill_hud) and its layouts (lc_hunter_skill_row /
    # lc_hunter_states_demo / lc_skill_row_live) were RETIRED 2026-07-22 -- the production
    # skill row lives as a second layout of lc_stat_hud, so a separate hud is redundant and
    # stacking both (e.g. via /hud add-all) double-renders the row oversized. Their EMITTERS
    # were deleted 2026-07-28 (they had been unreachable since that retirement, and one still
    # carried the shroud/tint same-layer tie that the live row had to be fixed for).
    for sub in ("images", "layouts", "huds", "texts"):
        os.makedirs(os.path.join(BH_DIR, sub), exist_ok=True)
    with open(os.path.join(BH_DIR, "images", "legendcraft-hunter.yml"), "w", encoding="utf-8") as f:
        f.write(_bh_images_yml() + "\n")

# ===========================================================================
# Phase 2 — chunky MMORPG stat bars (HUD_AND_ICONS.md §2)
#
# Each bar ships as a pair: an EMPTY frame+channel PNG and a full-width FILL PNG
# that BetterHud reveals left-to-right via `split` (the stock health_empty /
# health_bar pattern). Numerals are a BetterHud text element over the bar, never
# baked into the art (§5.5), so the fill stays a pure value ramp.
# ===========================================================================
STAT_DIR = os.path.join(ROOT, "bars")
SICON_DIR = os.path.join(ROOT, "stat-icons")
VITALS_DIR = os.path.join(ROOT, "vitals")      # health-bar affliction states (generated)
ARTSRC_DIR = os.path.join(ROOT, "art-src")   # hand-drawn source PNGs baked into icons

# Square, black-outlined, hotbar-matched bars (per reference). The two bars + the
# mid gap span exactly the vanilla hotbar width (182px) so each bar's OUTER end lands
# on a hotbar edge; the flanking icons then sit just beyond those ends.
HOTBAR_W = 182
STAT_GAP_MID = 2                               # 2px between the two bar columns (exact spec)
BAR_W = (HOTBAR_W - STAT_GAP_MID) // 2         # 90 -> 2*90 + 2 = 182, still hotbar-wide
BAR_H = 9                                      # exact spec: HP/mana/shield/food bars are 9px tall
BAR_PAD = 1                                    # single black-outline pixel, no bevel
BAR_IN_W, BAR_IN_H = BAR_W - 2 * BAR_PAD, BAR_H - 2 * BAR_PAD   # 88 x 7 fill
# Block spacing — shared by the preview compositor AND the BetterHud layout emitter
# so the two can never drift (the generator's art-vs-YAML invariant). All measurements exact-spec.
STAT_IW = 9            # flanking-icon column width (all icons share one 9x9 box)
STAT_ICON_H = 9        # every stat icon is a uniform 9x9 square so they read consistently
STAT_ICON_GAP = 2      # gap between an icon and its bar
STAT_BAR_VGAP = 2      # 2px vertical gap between the two bar rows
STAT_ROW_GAP = 2       # 2px vertical gap before the XP bar row
STAT_TEXT_SCALE = 0.30  # bar numerals ~5px tall, fit inside the 7px bar interior
STAT_TEXT_H = 5         # rendered bar-numeral height for vertical centering (exact spec)
STAT_LEVEL_SCALE = 0.42  # centered level numeral ~7px tall (overhangs the 5px XP bar 1px each side)
STAT_LEVEL_H = 7         # level numeral height
STAT_TEXT_DY = 0        # fine vertical nudge on top of the centered position
STAT_HUD_X = -10        # -19 sat ~9 GUI px left of hotbar center (in-client) -> shift right to -10
STAT_HUD_Y = -51        # -49 put the XP bar flush on the hotbar; raise 2px so the XP-hotbar
                        # gap matches the ~2px gap between the stat rows (STAT_BAR_VGAP)
# The skill-casting icon row rides INSIDE the single lc_stat layout, not as a layout or hud
# of its own. (BetterHud puts each *default-hud* on its own bossbar carrier and only the
# first repositions — a second default-hud dumps its glyphs at the top boss-bar line and
# shoves the first. One hud, one layout avoids that entirely.) Sharing the stat block's
# layout means the row needs no anchor of its own: it auto-centres on the same gui.x:50,
# and framed_row places it with a NEGATIVE y (`fy = -(SKILL_TILE + SKILL_ROW_GAP)`)
# measured up from the stat block -- tune there.
# The old SKILL_HUD_X/SKILL_HUD_Y anchors belonged to the separate lc_skill_hud retired
# 2026-07-22 and were deleted with its emitter 2026-07-28.

# Saturated value ramps (top-highlight, main, floor) — chunky/reference read.
# Resource hues from HUD_AND_ICONS §2; vitals tuned to the reference image.
BAR_RAMP = {
    "health": ((0xE0, 0x5A, 0x4E), (0xC4, 0x3B, 0x2E), (0x7A, 0x20, 0x1A)),
    "armor":  ((0xC6, 0xCB, 0xD2), (0x93, 0x99, 0xA2), (0x54, 0x59, 0x62)),  # vanilla steel gray
    "food":   ((0xB4, 0x8B, 0x54), (0x8B, 0x6A, 0x3E), (0x51, 0x3C, 0x22)),
    "mana":   ((0x74, 0x9C, 0xF2), (0x3D, 0x6F, 0xE0), (0x20, 0x3C, 0x84)),
    "energy": ((0xF2, 0xDE, 0x7A), (0xE8, 0xC8, 0x4A), (0x86, 0x6E, 0x20)),
    "rage":   ((0xE8, 0x54, 0x3F), (0xC4, 0x3B, 0x2E), (0x6C, 0x1C, 0x16)),
}
GEM_COLOR = {   # mana's left-cap sparkle base (original blue); energy/rage keys only drive
                # the export loop -- their icons (bolt/flame) carry their own palettes below.
    "mana": (0x3D, 0x6F, 0xE0), "energy": (0xE8, 0xC8, 0x4A), "rage": (0xC4, 0x3B, 0x2E),
}

# Rage's fill is NOT a 3-stop sand ramp like the other bars: two OBVIOUS bands
# (ember-orange over deep-red) meeting at a SUBTLE flame-shaped seam, with flat 3D
# top/bottom edges so it still reads as a rectangle (not a round/gradient bar).
RAGE_TOP_EDGE = (0xF4, 0x92, 0x4E)   # solid highlight row (3D top edge)
RAGE_ORANGE   = (0xEC, 0x6C, 0x2E)   # obvious upper band
RAGE_RED      = (0xBA, 0x34, 0x26)   # obvious lower band
RAGE_BOT_EDGE = (0x70, 0x1A, 0x12)   # solid deep-red floor (3D bottom edge)
XP_W, XP_H = 2 * BAR_W + STAT_GAP_MID, 5       # span end-to-end with the two bars above (182), 5px tall
XP_RAMP = ((0x9C, 0xCC, 0x65), (0x7C, 0xB3, 0x42), (0x55, 0x8B, 0x2F))

def _c(t):
    return (t[0], t[1], t[2], 255)

def bar_empty(w=BAR_W, h=BAR_H):
    """Flat SQUARE channel: a solid 1px black outline (corners included) over a dark
    field. No rounded corners, no raised bevel -- matches the reference's square read."""
    im = img(w, h)
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = FIELD_DARK
    # full pure-black outline including the four corners -> hard square edge
    for x in range(w):
        px[x, 0] = px[x, h - 1] = PURE_BLACK
    for y in range(h):
        px[0, y] = px[w - 1, y] = PURE_BLACK
    return im

def _rage_fill(w=BAR_IN_W, h=BAR_IN_H):
    """Rage bar: a solid RAGE_TOP_EDGE highlight row and a solid RAGE_BOT_EDGE floor
    row (flat 3D edges, like the other bars), with an interior that is obvious
    ember-orange up top fading to deep-red at the bottom across a SUBTLE flame-shaped
    seam -- a soft, multi-frequency wander as understated as the sand grain. Flat edges
    keep it reading as a rectangle rather than a round/gradient bar. Deterministic."""
    im = img(w, h)
    px = im.load()

    def _hash(x, y):
        n = ((x * 73856093) ^ (y * 19349663)) & 0xffffffff
        return ((n ^ (n >> 13)) * 1274126177) & 0xffffffff

    itop, ibot = 1, h - 2
    ih = (ibot - itop) or 1
    for x in range(w):
        # flame seam wanders gently around mid-interior; low amplitude -> subtle tongues.
        seam = 0.5 + 0.10 * (0.6 * math.sin(x * 0.5) + 0.3 * math.sin(x * 1.3 + 0.7)
                             + 0.2 * math.sin(x * 2.1 + 1.9))
        for y in range(h):
            if y == 0:
                px[x, y] = _c(RAGE_TOP_EDGE); continue
            if y == h - 1:
                px[x, y] = _c(RAGE_BOT_EDGE); continue
            rel = (y - itop) / ih
            f = max(0.0, min(1.0, 0.5 + (rel - seam) / 0.55))
            f = f * f * (3 - 2 * f)                        # smoothstep -> gentle blend
            r = round(RAGE_ORANGE[0] + (RAGE_RED[0] - RAGE_ORANGE[0]) * f)
            g = round(RAGE_ORANGE[1] + (RAGE_RED[1] - RAGE_ORANGE[1]) * f)
            b = round(RAGE_ORANGE[2] + (RAGE_RED[2] - RAGE_ORANGE[2]) * f)
            j = ((_hash(x, y) & 0xff) - 128) * 5 // 128    # same subtle grain as other bars
            px[x, y] = (max(0, min(255, r + j)), max(0, min(255, g + j)),
                        max(0, min(255, b + j)), 255)
    return im


def bar_fill(kind, w=BAR_IN_W, h=BAR_IN_H):
    """SAND-textured value fill: top highlight + darker floor row for read, mostly the
    main tone carrying a fine granular sand grain -- low-contrast per-pixel speckle,
    faint horizontal striation (windblown sediment layers), and sparse darker grains.
    Warmer/softer than the old high-contrast 'fabric' speckle. Deterministic (no RNG)."""
    if kind == "rage":
        return _rage_fill(w, h)
    light, main, dark = BAR_RAMP[kind]

    def _hash(x, y):
        n = ((x * 73856093) ^ (y * 19349663)) & 0xffffffff
        return ((n ^ (n >> 13)) * 1274126177) & 0xffffffff

    def sanded(rgb, x, y):
        # 1) fine low-contrast base grain (+/-7) -- the granular speckle of sand
        j = ((_hash(x, y) & 0xff) - 128) * 7 // 128
        # 2) faint horizontal striation: a per-row bias so grains settle in layers
        j += ((_hash(0, y) & 0xff) - 128) * 4 // 128
        # 3) sparse darker grains (~1 in 9 pixels dip further) -- individual sand grains
        if (_hash(x * 7 + 1, y * 3 + 2) % 9) == 0:
            j -= 16
        return (max(0, min(255, rgb[0] + j)),
                max(0, min(255, rgb[1] + j)),
                max(0, min(255, rgb[2] + j)), 255)

    im = img(w, h)
    px = im.load()
    for y in range(h):
        if y == 0:                                   # top highlight: flat, uniform (3D edge)
            for x in range(w):
                px[x, y] = _c(light)
        elif y >= h - 1:                             # bottom floor: flat, uniform (3D edge)
            for x in range(w):
                px[x, y] = _c(dark)
        else:                                        # interior carries the sand grain
            for x in range(w):
                px[x, y] = sanded(main, x, y)
    return im

def xp_empty(w=XP_W, h=XP_H):
    im = img(w, h)
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = FIELD_DARK
    for x in range(w):
        px[x, 0] = px[x, h - 1] = PURE_BLACK
    for y in range(h):
        px[0, y] = px[w - 1, y] = PURE_BLACK
    return im

def xp_fill(w=XP_W - 2, h=XP_H - 2):
    light, main, dark = (_c(XP_RAMP[i]) for i in range(3))
    im = img(w, h)
    px = im.load()
    for y in range(h):
        col = light if y == 0 else dark if y >= h - 1 else main
        for x in range(w):
            px[x, y] = col
    return im

# --- flanking stat icons -----------------------------------------------------
# Every icon is a uniform 9x9 box (STAT_ICON_H) so heart/mana/shield/drumstick read at
# the SAME size next to each other, matching the reference. Black outline (K) on all.
# (The hand-drawn _HEART and _DRUM maps were deleted 2026-07-28: heart_icon() and
#  drumstick_icon() have been baked from user-supplied art-src PNGs via _load_src_icon
#  since that art landed, leaving the maps unreferenced. _SHIELD and _GEM below are
#  still drawn from maps and stay.)
_SHIELD = [
    "KKKKKKKKK",
    "KMLMMMMMK",
    "KMMMMMMMK",
    "KMMMMMMMK",
    "KMMMMMMMK",
    ".KMMMMMK.",
    "..KMMMK..",
    "...KMK...",
    "....K....",
]
# 4-point orthogonal sparkle (matches the reference mana icon): blue diamond center (C)
# with a lighter core (H) and up/down/left/right arms, all wrapped in a black outline (K).
_GEM = [
    "....K....",
    "...KCK...",
    "...KCK...",
    ".KKCCCKK.",
    "KCCCHCCCK",
    ".KKCCCKK.",
    "...KCK...",
    "...KCK...",
    "....K....",
]

# ===========================================================================
# Health-bar affliction states (hud-and-icons.md §2 "Bar behaviors")
#
# Modelled on Volya's MMORPG HUD -- which is where the READ comes from: a state
# tints the health bar itself rather than adding a second indicator, so the one
# thing already in the player's eyeline answers "what is happening to me". None
# of their pixels are used; every texture below is drawn here.
#
# WHY THESE HUES ARE NOT CLASS ACCENTS. An affliction is universal -- anyone can
# be poisoned by anything -- so it must not read as a class's signature. Every
# ramp is derived from the VANILLA effect color and then flattened for UI, which
# also steers clear of the crowded red/bright-gold zones `art-style.md` §9 warns
# about. The convention matches the one class docs already follow for status
# NAMES (MC-native), extended to their colors.
#
# Burning is the one hex worth a second look: fire is orange and Pyromancer's
# thread is ember-orange `#EC6C2E`. Kept, because fire has exactly one legible
# color and a burning player is usually burning for a reason -- but it is the
# one affliction that could be argued into a different hue.
#
# STATE IS SHAPE, NOT ONLY COLOR (§1.2). Each one owns a silhouette that survives
# greyscale: poison a rising bubble field, burning tongues climbing off the floor,
# freezing rime biting in from both long edges, wither an opaque pitted char,
# regeneration sparse motes. Told apart with saturation at zero, which is the test.
# ===========================================================================
AFFLICTION = {                      # (light, main, dark), vanilla-derived, UI-flat
    "poison":       ((0x6F, 0xB4, 0x4F), (0x3E, 0x7A, 0x2C), (0x1E, 0x3D, 0x16)),
    "burning":      ((0xF6, 0xA9, 0x3B), (0xE8, 0x63, 0x2A), (0x8E, 0x2A, 0x12)),
    "freezing":     ((0xE4, 0xF0, 0xF8), (0xBB, 0xD6, 0xE8), (0x7F, 0xA8, 0xC4)),
    "wither":       ((0x4A, 0x3F, 0x39), (0x2A, 0x23, 0x20), (0x12, 0x0F, 0x0D)),
    "regeneration": ((0xF0, 0xA8, 0xD8), (0xD9, 0x7F, 0xBE), (0x8E, 0x44, 0x78)),
}


def _ahash(x, y):
    """The same deterministic hash `bar_fill` uses. No RNG anywhere in the generator:
    a regen must produce byte-identical art or the pack sha1 churns for nothing."""
    n = ((x * 73856093) ^ (y * 19349663)) & 0xffffffff
    return ((n ^ (n >> 13)) * 1274126177) & 0xffffffff


def affliction_fill(kind, w=BAR_IN_W, h=BAR_IN_H):
    """One affliction overlay, drawn at the health fill's exact size.

    Sized to BAR_IN_W deliberately: these ride the SAME health listener as
    `lc_fill_health`, and BetterHud reveals each image by a fraction of its own
    width. A narrower texture would let the red fill run ahead of its own tint.

    Returns RGBA with real alpha -- every state except wither is an overlay that
    must let the fill's level read through it. Wither is opaque because "dying"
    outranks "how much is left"."""
    light, main, dark = AFFLICTION[kind]
    im = img(w, h)
    px = im.load()

    if kind == "poison":
        # A bubble field, not a wash. The first cut was a flat low-alpha film with
        # sparse single-pixel bubbles; at 7px it just muddied the red to brown and was
        # indistinguishable from healthy with saturation at zero. What reads is CHUNKS:
        # near-opaque blobs with a dark underside, roughly every 4px, with the red
        # showing between them. Mottled two-tone survives greyscale; a tint does not.
        for y in range(h):
            for x in range(w):
                px[x, y] = (main[0], main[1], main[2], 70)
        for bx in range(0, w, 4):
            seed = _ahash(bx, 7)
            by = 1 + seed % (h - 3)
            bw = 2 + ((seed >> 3) & 1)
            for dx in range(bw):
                x = bx + dx
                if x >= w:
                    break
                px[x, by] = (light[0], light[1], light[2], 245)
                if by + 1 < h:
                    px[x, by + 1] = (dark[0], dark[1], dark[2], 225)

    elif kind == "burning":
        # Tongues climbing off the floor, OPAQUE. The first cut faded them out toward
        # each tip, which at 7px over a red bar left almost nothing: ember-on-red is a
        # near-invisible pairing, and in greyscale it vanished entirely. Solid fire with
        # a bright tip row is what carries.
        #
        # Height is capped at h-1 so the health fill's top highlight row ALWAYS survives.
        # The bar has to keep reading as a health bar while it burns -- if fire can cover
        # the whole interior, a burning player loses the fill-level read.
        for x in range(w):
            tongue = 2 + (_ahash(x, 3) % (h - 2))
            for k in range(tongue):
                y = h - 1 - k
                stop = light if k == tongue - 1 else (dark if k == 0 else main)
                px[x, y] = (stop[0], stop[1], stop[2], 255)

    elif kind == "freezing":
        # Rime biting in from both long edges, clear through the middle. Depth per
        # column is hashed, so the two fronts are jagged and asymmetric -- reads as
        # crystal growth rather than as a second, thinner bar.
        for y in range(h):
            for x in range(w):
                px[x, y] = (main[0], main[1], main[2], 48)
        for x in range(w):
            for edge, seed in ((0, 5), (1, 9)):
                depth = 1 + (_ahash(x, seed) % 3)
                for k in range(depth):
                    y = k if edge == 0 else h - 1 - k
                    stop = light if k == 0 else main
                    px[x, y] = (stop[0], stop[1], stop[2], 235 - 45 * k)

    elif kind == "wither":
        # Opaque char with pits eaten through it. The only state that HIDES the fill,
        # because at that point the number matters less than the fact.
        for y in range(h):
            for x in range(w):
                n = _ahash(x, y) % 11
                stop = dark if n == 0 else (light if n == 10 else main)
                px[x, y] = (stop[0], stop[1], stop[2], 255)

    elif kind == "regeneration":
        # Motes drifting up, plus a lift along the top edge. Still the lightest of the
        # five -- it is the good news and must not hide the bar it is good news about --
        # but the first cut was single pixels every fourth column, which disappeared at
        # zero saturation. Two-pixel dashes every third column plus the top-row lift
        # give it a texture that reads without covering anything.
        for x in range(w):
            px[x, 0] = (light[0], light[1], light[2], 70)
        for x in range(0, w, 3):
            y = 1 + (_ahash(x, 23) % (h - 3))
            px[x, y] = (light[0], light[1], light[2], 240)
            if y + 1 < h:
                px[x, y + 1] = (main[0], main[1], main[2], 170)
    return im


def _ramp_to(im, ramp, floor_alpha=0):
    """Re-map an existing icon onto a three-stop ramp by luminance, preserving alpha.

    Used to derive the affliction hearts from OUR heart rather than drawing four new
    ones: same silhouette, same shading, different material. A state heart that did
    not share the base heart's outline would jump on every state change."""
    light, main, dark = ramp
    src = im.convert("RGBA")
    px = src.load()
    lums = [_lum(*px[x, y][:3]) for y in range(src.height) for x in range(src.width)
            if px[x, y][3] > floor_alpha]
    if not lums:
        return src
    lo, hi = min(lums), max(lums)
    span = max(hi - lo, 1e-6)
    out = src.copy()
    opx = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = opx[x, y]
            if a == 0:
                continue
            t = (_lum(r, g, b) - lo) / span
            stop = dark if t < 0.34 else (main if t < 0.72 else light)
            opx[x, y] = (stop[0], stop[1], stop[2], a)
    return out


def affliction_heart(kind):
    """The flanking heart in its afflicted material. Drawn over `heart.png` in the
    layout, not instead of it, so the base heart stays the one piece of hand art."""
    heart = _ramp_to(heart_icon(), AFFLICTION[kind])
    px = heart.load()
    light, main, dark = AFFLICTION[kind]
    if kind == "burning":
        # Embers gathered along the heart's lower edge -- the same "burns from below"
        # grammar as the bar, so the two read as one event.
        for x in range(heart.width):
            for y in range(heart.height - 1, -1, -1):
                if px[x, y][3] > 0:
                    px[x, y] = (light[0], light[1], light[2], px[x, y][3])
                    break
    elif kind == "wither":
        # Two pits, matching the bar's eaten char.
        for x, y in ((3, 3), (5, 5)):
            if x < heart.width and y < heart.height and px[x, y][3] > 0:
                px[x, y] = (dark[0], dark[1], dark[2], px[x, y][3])
    return heart


# --- the class shield pool: a SHEATH, not a sixth affliction ------------------
# Ward-steel, never gold. `hud-and-icons.md` reserves antique gold `#D9A94A` for the
# value thread and keeps it off every other element, so a gold bar sitting in front of
# health would read as currency. Cold steel reads as borrowed hit points.
SHIELD_RAMP = ((0xD6, 0xE2, 0xEE), (0x8F, 0xA8, 0xC8), (0x46, 0x5A, 0x74))


def shield_fill(w=BAR_W, h=BAR_H):
    """The class shield pool, drawn over the health cell at the OUTLINE's size.

    Every affliction is BAR_IN (88x7) and lives inside the bar. This is BAR_W x BAR_H
    (90x9) and covers the black outline too, so a shielded bar reads as the whole HP
    cell being sheathed rather than as a second bar competing for the same 7px.

    That size difference is the whole design, because it is what carries the greyscale
    test against five states that already exist: rows 0 and h-1 are the two pixel rows
    nothing else in the vitals stack can touch, so the sheath separates on SHAPE and
    never has to win an argument about hue.

    Drawn at the outline's coordinates, not the fill's -- see the layout emitter."""
    light, main, dark = SHIELD_RAMP
    im = img(w, h)
    px = im.load()
    # RAILS ONLY -- the interior is deliberately empty, and that is a correction, not an
    # omission. The first cut carried a faint interior glaze for body; because BetterHud
    # reveals this by a fraction of its own WIDTH, a partial pool tinted only the left
    # part of the health fill and drew a hard vertical seam across it. The bar then read
    # as a health bar with two levels -- exactly the "second bar competing for the same
    # 7px" misread the outline-sized sheath exists to avoid, and it was worse at zero
    # saturation than in colour. Any interior alpha reproduces it, so there is none.
    #
    # Lit top edge, shadowed bottom edge: the same top-left light direction every stat
    # icon uses, which is what makes 1px read as plate rather than as a stray line.
    for x in range(w):
        px[x, 0] = (light[0], light[1], light[2], 255)
        px[x, h - 1] = (dark[0], dark[1], dark[2], 255)
    # A left cap and deliberately NO right one. A closed ring would only ever close at a
    # full pool; an open bracket is honest at every level.
    for y in range(h):
        px[0, y] = (main[0], main[1], main[2], 255)
    return im


def shield_heart():
    """The flanking heart in ward-steel, derived from OUR heart the way the affliction
    hearts are -- same silhouette, same shading, different material -- plus a rim light
    down its leading edge, which is the bar's sheath grammar so the two read as one
    event rather than as two things that happened to turn blue."""
    heart = _ramp_to(heart_icon(), SHIELD_RAMP)
    px = heart.load()
    light = SHIELD_RAMP[0]
    for y in range(heart.height):
        for x in range(heart.width):
            if px[x, y][3] > 0:
                px[x, y] = (light[0], light[1], light[2], px[x, y][3])
                break
    return heart


def _load_src_icon(filename, size=STAT_ICON_H, key_blue=False):
    """Bake a hand-drawn source PNG (art-src/) into a clean stat icon.

    The heart art ships on a solid blue key color (upscaled, slightly AA'd); the
    drumstick art already has a transparent field. We key the blue out (if asked),
    crop to the drawn content, and nearest-neighbour downscale to the uniform
    `size`x`size` icon box so every flanking icon reads at the same scale."""
    im = Image.open(os.path.join(ARTSRC_DIR, filename)).convert("RGBA")
    px = im.load()
    if key_blue:
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if b > 150 and r < 140 and g > 120:      # solid blue key -> transparent
                    px[x, y] = T
    bb = im.getbbox()                                     # trim to drawn content
    if bb:
        im = im.crop(bb)
    if im.size != (size, size):
        im = im.resize((size, size), Image.NEAREST)
    return im

def heart_icon():
    # Baked from art-src/heart_src.png (user-supplied); blue field keyed out.
    return _load_src_icon("heart_src.png", key_blue=True)

def _shade_map(rows, body_chars, tone_for):
    """Render an icon, faking a 3D volume by shading every body pixel along the
    top-left -> bottom-right diagonal: lit at the top-left, in shadow toward the
    bottom-right (same light direction as the heart/drumstick art). `tone_for(t, ch)`
    maps t in 0..1 (0=lit, 1=shadow) + the source char -> rgba.

    The outline is NOT taken from the map's 'K' pixels (those were boxy/gappy); instead
    a solid 1px black outline is auto-grown to HUG the shaded silhouette (8-directional),
    matching the tight continuous outline the heart/drumstick source art carries."""
    h = len(rows)
    w = max(len(r) for r in rows)
    body = {(x, y) for y, r in enumerate(rows)
            for x, ch in enumerate(r) if ch in body_chars}
    diags = [x + y for (x, y) in body]
    dmin, dmax = min(diags), max(diags)
    span = (dmax - dmin) or 1
    im = img(w, h)
    px = im.load()
    for (x, y) in body:
        px[x, y] = tone_for((x + y - dmin) / span, rows[y][x])
    # Grow a hugging black outline into ORTHOGONAL neighbours only (not diagonal): a
    # diagonal-only outline pixel fills concave corners with a black block that sits next
    # to two other blacks, reading as an unnatural solid corner. 4-dir keeps it single-px.
    for (bx, by) in body:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = bx + dx, by + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in body and px[nx, ny] == T:
                px[nx, ny] = PURE_BLACK                    # pure black, matching the heart/food art
    return im

def shield_icon():
    # Steel armor read, now with a 3D bevel: bright top-left face -> mid -> dark
    # bottom-right shadow (4-stop ramp), matching the heart/drumstick lighting.
    ramp = [(0xEC, 0xEF, 0xF4), (0xC2, 0xC8, 0xD0), (0x93, 0x99, 0xA2), (0x55, 0x5B, 0x64)]

    def tone(t, ch):
        i = 0 if t < 0.20 else 1 if t < 0.45 else 2 if t < 0.72 else 3
        return _c(ramp[i])
    return _shade_map(_SHIELD, "ML", tone)

def drumstick_icon():
    # Baked from art-src/drumstick_src.png (user-supplied); already transparent.
    return _load_src_icon("drumstick_src.png", key_blue=False)

# --- energy bolt + rage flame: the other two resource icons ------------------
# Same 9x9 box + TL-light -> BR-shadow shading as the gem, so bolt/flame/sparkle read
# as one family. Saved (with the mana sparkle) as gem_<kind>.png -- the "gem" filename
# is historical; energy and rage are no longer gems.
_BOLT = [
    ".....BB..", "....BB...", "...BB....", "..BBBB...",
    "....BB...", "...BB....", "..BB.....", "..B......", ".........",
]
_BOLT_RAMP = [(0xFA, 0xF0, 0xB8), (0xF6, 0xE6, 0x96), (0xF0, 0xD6, 0x68), (0xBC, 0xA0, 0x40)]


def _bolt_icon():
    def tone(t, ch):
        i = 0 if t < 0.25 else 1 if t < 0.5 else 2 if t < 0.78 else 3
        return _c(_BOLT_RAMP[i])
    return _shade_map(_BOLT, "B", tone)


_FLAME = [
    "....R....", "....RR...", "...RRR...", "..RRRRR..", "..RROOR..",
    ".RROOOOR.", ".ROOYYOR.", ".ROYWYOR.", "..ROOOR..",
]
_FLAME_COL = {"R": (0xD8, 0x45, 0x30), "O": (0xF5, 0x84, 0x2E), "Y": (0xF7, 0xC9, 0x48)}


def _flame_icon():
    # Flat-style nested flame (red -> orange -> yellow layers), run through the gem's
    # TL-light -> BR-shadow ramp for 3D volume, plus a white-hot core specular ('W').
    def tone(t, ch):
        if ch == "W":
            return (0xFF, 0xF4, 0xCE, 255)
        base = _FLAME_COL[ch]
        f = 1.22 if t < 0.20 else 1.06 if t < 0.45 else 0.92 if t < 0.72 else 0.76
        return _c(tuple(max(0, min(255, int(v * f))) for v in base))
    return _shade_map(_FLAME, "ROYW", tone)


def gem_icon(kind):
    """The resource icon flanking the resource bar (saved as gem_<kind>.png). Mana keeps
    the faceted blue sparkle (lightened); energy is a lightning bolt and rage a flame --
    all three share the gem's TL-light -> BR-shadow ramp so the set reads consistent."""
    if kind == "energy":
        return _bolt_icon()
    if kind == "rage":
        return _flame_icon()
    # mana: faceted 3D gem sparkle (bright top-left facets -> mid -> dark bottom-right,
    # near-white specular at the crystal's center, the map's 'H').
    base = GEM_COLOR[kind]

    def sc(f):
        return _c(tuple(max(0, min(255, int(v * f))) for v in base))

    spec = _c(tuple(min(255, int(v * 0.35 + 255 * 0.65)) for v in base))

    def tone(t, ch):
        if ch == "H":
            return spec                                  # central specular glint (the sparkle)
        # Brightest facet stays sc(1.5) (original top blue); the darker facets are lifted
        # (0.85/0.5 -> 1.06/0.9) so the gradient is subtle -- the gem reads as a bright
        # blue star twinkling from its specular core rather than a high-contrast crystal.
        return sc(1.5) if t < 0.22 else sc(1.26) if t < 0.5 else sc(1.06) if t < 0.75 else sc(0.9)
    return _shade_map(_GEM, "CH", tone)

def hotbar_slot(selected=False):
    w, h = 18, 18
    im = img(w, h)
    px = im.load()
    base = PAL["I"] if not selected else PAL["L"]
    hi = PAL["H"] if selected else PAL["L"]
    for y in range(h):
        for x in range(w):
            px[x, y] = base
    for x in range(w):
        px[x, 0] = px[x, h - 1] = PAL["k"]
    for y in range(h):
        px[0, y] = px[w - 1, y] = PAL["k"]
    for x in range(1, w - 1):
        px[x, 1] = hi
        px[x, h - 2] = PAL["i"]
    for y in range(1, h - 1):
        px[1, y] = hi
        px[w - 2, y] = PAL["i"]
    if selected:                                     # bright selection keyline
        for x in range(w):
            px[x, 0] = px[x, h - 1] = PAL["B"]
        for y in range(h):
            px[0, y] = px[w - 1, y] = PAL["B"]
    return im

def export_stat_bars():
    os.makedirs(STAT_DIR, exist_ok=True)
    os.makedirs(SICON_DIR, exist_ok=True)
    save(bar_empty(), os.path.join(STAT_DIR, "bar_empty.png"))
    for kind in BAR_RAMP:
        save(bar_fill(kind), os.path.join(STAT_DIR, f"fill_{kind}.png"))
    save(xp_empty(), os.path.join(STAT_DIR, "xp_empty.png"))
    save(xp_fill(), os.path.join(STAT_DIR, "xp_fill.png"))
    save(hotbar_slot(False), os.path.join(STAT_DIR, "hotbar_slot.png"))
    save(hotbar_slot(True), os.path.join(STAT_DIR, "hotbar_slot_selected.png"))
    save(heart_icon(), os.path.join(SICON_DIR, "heart.png"))
    save(shield_icon(), os.path.join(SICON_DIR, "shield.png"))
    save(drumstick_icon(), os.path.join(SICON_DIR, "drumstick.png"))
    for kind in GEM_COLOR:
        save(gem_icon(kind), os.path.join(SICON_DIR, f"gem_{kind}.png"))
    os.makedirs(VITALS_DIR, exist_ok=True)
    for kind in AFFLICTION:
        save(affliction_fill(kind), os.path.join(VITALS_DIR, f"state_{kind}.png"))
        if kind != "regeneration":      # regeneration has no heart -- the bar pulse is the signal
            save(affliction_heart(kind), os.path.join(VITALS_DIR, f"heart_{kind}.png"))
    # The shield pool's art ships ahead of its element: the two ids it reads do not exist
    # yet (AUD-7's slice), but art is the half that can be judged without them, and the
    # greyscale constraint it has to meet only exists once the five afflictions do.
    save(shield_fill(), os.path.join(VITALS_DIR, "shield_fill.png"))
    save(shield_heart(), os.path.join(VITALS_DIR, "heart_shield.png"))

def _bar_tile(kind, frac, num):
    """empty + fill(frac) + centered white numeral — one preview bar."""
    t = bar_empty().copy()
    fill = bar_fill(kind)
    fw = max(0, min(BAR_IN_W, round(BAR_IN_W * frac)))
    if fw > 0:
        paste(t, fill.crop((0, 0, fw, BAR_IN_H)), BAR_PAD, BAR_PAD)
    g = glyph(num, color=(255, 255, 255, 255))
    paste(t, g, (BAR_W - g.width) // 2, (BAR_H - g.height) // 2)
    return t

def stat_hud_mock():
    """The full chunky stat block (2x2 bars + icons + XP + hotbar) as a preview."""
    n = 10
    pad = 6                                        # preview background margin only
    gap_mid, icon_gap, IW, row_gap = STAT_GAP_MID, STAT_ICON_GAP, STAT_IW, STAT_ROW_GAP
    vgap = STAT_BAR_VGAP
    lx_icon = pad
    lx_bar = lx_icon + IW + icon_gap
    rx_bar = lx_bar + BAR_W + gap_mid
    rx_icon = rx_bar + BAR_W + icon_gap
    xp_x = lx_bar + (2 * BAR_W + gap_mid - XP_W) // 2   # center XP under the two-bar span
    span_w = 2 * BAR_W + gap_mid                        # two-bar span == vanilla hotbar width (182)
    block_w = rx_icon + IW
    total_w = max(block_w, lx_bar + span_w) + pad
    total_h = pad + BAR_H * 2 + vgap + row_gap + XP_H + 5 + 18 + pad
    bg = Image.new("RGBA", (total_w * n, total_h * n), (28, 32, 38, 255))

    def blit(im, x, y):
        paste(bg, scale(im, n), x * n, y * n)

    iy = (BAR_H - STAT_ICON_H) // 2
    y0 = pad
    blit(heart_icon(), lx_icon, y0 + iy)
    blit(_bar_tile("health", 1.0, "17 / 17"), lx_bar, y0)
    blit(_bar_tile("armor", 1.0, "20 / 20"), rx_bar, y0)
    blit(shield_icon(), rx_icon, y0 + iy)
    y1 = y0 + BAR_H + vgap
    blit(gem_icon("mana"), lx_icon, y1 + iy)
    blit(_bar_tile("mana", 0.68, "340 / 500"), lx_bar, y1)
    blit(_bar_tile("food", 1.0, "20 / 20"), rx_bar, y1)
    blit(drumstick_icon(), rx_icon, y1 + iy)
    yx = y1 + BAR_H + row_gap
    xp = xp_empty().copy()
    fw = round((XP_W - 2) * 0.35)
    paste(xp, xp_fill().crop((0, 0, fw, XP_H - 2)), 1, 1)
    blit(xp, xp_x, yx)
    blit(glyph("1", color=(0x9C, 0xCC, 0x65, 255)), xp_x + XP_W // 2 - 1, yx - 1)
    xpnum = glyph("40 / 400", color=(255, 255, 255, 255))   # current/needed, right-aligned
    blit(xpnum, xp_x + XP_W - 2 - xpnum.width, yx - 1)
    yh = yx + XP_H + 5
    # Draw the vanilla hotbar to TRUE scale (9 slots spanning ~182px) centered under the
    # two-bar span, so the preview shows the intended in-client alignment: the bars run
    # edge-to-edge with the hotbar and the flanking icons overhang just past its ends.
    slot = 20                                          # 9 * 20 = 180 ~= 182 hotbar width
    hb_x = lx_bar + (span_w - 9 * slot) // 2
    for i in range(9):
        s = hotbar_slot(i == 3).resize((slot, slot), Image.NEAREST)
        blit(s, hb_x + i * slot, yh)
        blit(glyph(str(i + 1), color=PAL["B"]), hb_x + i * slot + 2, yh + 2)
    return bg

def hudline_composite_mock(feedback):
    """Screen-space composite for HUDLINE's three stacked lanes.

    This is positional evidence, not a Minecraft screenshot: it renders the generated skill
    chrome and stat block around labelled stand-ins for BetterHud's default-bitmap feedback and
    the client's native held-item name. Keeping both labels in one image makes an accidental
    lane overlap visible before the pack reaches mc-dev.
    """
    n = 5
    screen_w, screen_h = 236, 132
    screen_bottom = 126
    layout_x = (screen_w - (2 * BAR_W + STAT_GAP_MID)) // 2 - (STAT_IW + STAT_ICON_GAP)
    layout_y = screen_bottom + STAT_HUD_Y
    bg = Image.new("RGBA", (screen_w * n, screen_h * n), (24, 29, 35, 255))

    def blit(im, x, y):
        paste(bg, scale(im, n), x * n, y * n)

    # Four-slot subclass row: shared frame + placeholder art is enough to prove its footprint.
    total = 4 * SKILL_TILE + 3 * SKILL_FRAME_GAP
    row_x = screen_w // 2 - total // 2
    row_y = layout_y + SKILL_ROW_Y_PX
    for i in range(4):
        x = row_x + i * (SKILL_TILE + SKILL_FRAME_GAP)
        blit(skill_frame(), x, row_y)
        blit(icon_placeholder().resize((ART, ART), Image.NEAREST),
             x + SKILL_ART_OFF, row_y + SKILL_ART_OFF)

    # The native item label is intentionally not part of BetterHud; this labelled stand-in
    # occupies the client lane so the generated preview will expose future geometry drift.
    draw = ImageDraw.Draw(bg)
    font = ImageFont.load_default(size=6 * n)
    item_y = (screen_bottom - VANILLA_ITEM_NAME_OFFSET_PX) * n
    draw.text((screen_w * n // 2 + n, item_y + n), "Iron Longsword", font=font,
              fill=(32, 32, 32, 255), anchor="mm")
    draw.text((screen_w * n // 2, item_y), "Iron Longsword", font=font,
              fill=(255, 255, 255, 255), anchor="mm")
    if feedback:
        feedback_y = (layout_y + FEEDBACK_LINE_Y_PX + FEEDBACK_TEXT_HEIGHT_PX // 2) * n
        draw.text((screen_w * n // 2, feedback_y), feedback, font=font,
                  fill=(255, 255, 255, 255), stroke_width=n,
                  stroke_fill=(20, 22, 26, 255), anchor="mm")

    # Stat rows and XP channel at the unchanged live anchor.
    bl = layout_x + STAT_IW + STAT_ICON_GAP
    br = bl + BAR_W + STAT_GAP_MID
    r0 = layout_y
    r1 = r0 + BAR_H + STAT_BAR_VGAP
    blit(_bar_tile("health", 0.82, "17 / 20"), bl, r0)
    blit(_bar_tile("armor", 1.0, "20 / 20"), br, r0)
    blit(_bar_tile("mana", 0.68, "340 / 500"), bl, r1)
    blit(_bar_tile("food", 1.0, "20 / 20"), br, r1)
    blit(heart_icon(), layout_x, r0)
    blit(shield_icon(), br + BAR_W + STAT_ICON_GAP, r0)
    blit(gem_icon("mana"), layout_x, r1)
    blit(drumstick_icon(), br + BAR_W + STAT_ICON_GAP, r1)
    xpy = r1 + BAR_H + STAT_ROW_GAP
    xpx = bl + (2 * BAR_W + STAT_GAP_MID - XP_W) // 2
    xp = xp_empty().copy()
    paste(xp, xp_fill().crop((0, 0, round((XP_W - 2) * 0.35), XP_H - 2)), 1, 1)
    blit(xp, xpx, xpy)

    # Vanilla hotbar stand-in at its screen edge position.
    slot = 20
    hotbar_x = screen_w // 2 - 9 * slot // 2
    hotbar_y = screen_bottom - 20
    for i in range(9):
        blit(hotbar_slot(i == 3).resize((slot, slot), Image.NEAREST), hotbar_x + i * slot, hotbar_y)
    return bg

# ===========================================================================
# BetterHud config for the chunky stat HUD (schema verified against BetterHud
# 2.0.0 wiki + source). Native listener bars drive health/armor/food; the
# resource + XP bars are placeholder-driven from the LegendCraft PAPI expansion
# (papi:legendcraft_*). Per-class resource recolor uses `conditions:` on the
# resource-type placeholder. Offsets share the STAT_* geometry with the preview
# compositor, so art and YAML cannot drift.
# ===========================================================================
def _bh_stat_images_yml():
    lines = ["# GENERATED by assets/tools/generate_hud.py -- do not hand-edit.",
             "# Image registry for the LegendCraft chunky stat HUD (BetterHud 2.0.0).",
             ""]
    singles = {
        "lc_bar_empty": "legendcraft/bars/bar_empty.png",
        "lc_xp_empty": "legendcraft/bars/xp_empty.png",
        "lc_icon_heart": "legendcraft/stat-icons/heart.png",
        "lc_icon_shield": "legendcraft/stat-icons/shield.png",
        "lc_icon_drumstick": "legendcraft/stat-icons/drumstick.png",
        "lc_gem_mana": "legendcraft/stat-icons/gem_mana.png",
        "lc_gem_energy": "legendcraft/stat-icons/gem_energy.png",
        "lc_gem_rage": "legendcraft/stat-icons/gem_rage.png",
        # Affliction hearts — Volya MMORPG HUD art on our own 9x9 heart silhouette, so they
        # layer over `lc_icon_heart` rather than replacing it.
        "lc_heart_poison": "legendcraft/vitals/heart_poison.png",
        "lc_heart_burning": "legendcraft/vitals/heart_burning.png",
        "lc_heart_freezing": "legendcraft/vitals/heart_freezing.png",
        "lc_heart_wither": "legendcraft/vitals/heart_wither.png",
    }
    for name, file in singles.items():
        lines += [f"{name}:", "  type: single", f"  file: {file}", ""]
    # Native vitals bars — BetterHud built-in listener classes (no PAPI needed).
    for name, file, cls in (
        ("lc_fill_health", "legendcraft/bars/fill_health.png", "health"),
        ("lc_fill_armor", "legendcraft/bars/fill_armor.png", "armor"),
        ("lc_fill_food", "legendcraft/bars/fill_food.png", "food"),
        # Affliction fills ride the SAME health listener as lc_fill_health, so a tint reveals to
        # exactly the fraction the red fill does and never paints the empty channel.
        ("lc_state_poison", "legendcraft/vitals/state_poison.png", "health"),
        ("lc_state_burning", "legendcraft/vitals/state_burning.png", "health"),
        ("lc_state_freezing", "legendcraft/vitals/state_freezing.png", "health"),
        ("lc_state_wither", "legendcraft/vitals/state_wither.png", "health"),
        ("lc_state_regeneration", "legendcraft/vitals/state_regeneration.png", "health"),
    ):
        lines += [f"{name}:", "  type: listener", f"  file: {file}",
                  "  split: 25", "  split-type: left",
                  "  setting:", "    listener:", f"      class: {cls}", ""]
    # Placeholder-driven resource fills — one per family, recolored by condition.
    for name, file in (
        ("lc_fill_mana", "legendcraft/bars/fill_mana.png"),
        ("lc_fill_energy", "legendcraft/bars/fill_energy.png"),
        ("lc_fill_rage", "legendcraft/bars/fill_rage.png"),
    ):
        lines += [f"{name}:", "  type: listener", f"  file: {file}",
                  "  split: 25", "  split-type: left",
                  "  setting:", "    listener:", "      class: placeholder",
                  '      value: "(number)papi:legendcraft_resource_current"',
                  '      max: "(number)papi:legendcraft_resource_max"', ""]
    # XP fill — our progression (0-100 percent), NOT vanilla exp.
    lines += ["lc_fill_xp:", "  type: listener", "  file: legendcraft/bars/xp_fill.png",
              "  split: 25", "  split-type: left",
              "  setting:", "    listener:", "      class: placeholder",
              '      value: "(number)papi:legendcraft_xp_percent"',
              "      max: 100", ""]
    return "\n".join(lines)

def _bh_stat_layout_yml():
    IW, IG, GM, p = STAT_IW, STAT_ICON_GAP, STAT_GAP_MID, BAR_PAD
    bl = IW + IG                       # left-column bar x
    br = bl + BAR_W + GM               # right-column bar x
    ir = br + BAR_W + IG               # right-column icon x
    # The skill row lives in THIS layout (BetterHud renders only ONE hud, so a separate skill
    # hud never draws) — a SKILL_BAND is reserved above and the stat block shifts down into it.
    # Stat block stays at its proven-good position (y=0, hud pixel.y=STAT_HUD_Y). The skill row
    # rides ABOVE it at NEGATIVE y so the stat block can't drift into the hotbar.
    r0 = 0                             # top bar-row y
    r1 = r0 + BAR_H + STAT_BAR_VGAP    # bottom bar-row y (gap between the two rows)
    xpy = r1 + BAR_H + STAT_ROW_GAP    # XP-row y
    xpx = bl + (2 * BAR_W + GM - XP_W) // 2   # center the XP bar under the two-bar span
    img_lines, n = [], 1

    def conds_block(conds):
        # conds: a single tuple or a list of them, AND-ed via `gate: and`. Each tuple is
        # (ph, val) -> '==', or (ph, val, op) for '!='.
        #
        # The == / != restriction is a property of the OPERAND TYPE, not of layout conditions.
        # BetterHud's `Operations` holds three operator maps and `Conditions.parse` picks one from
        # `PlaceholderBuilder.getClazz`: Number carries == != >= <= < >, while Boolean and String
        # carry only == and !=. A bare `papi:...` is a String, which is why the ordering operators
        # were rejected at load here — every condition this helper writes compares strings. Cast an
        # operand with `(number)` and the ordering operators resolve; the party layout's planned
        # low-health gate is the first place that will matter.
        if isinstance(conds, tuple):
            conds = [conds]
        lines = ["      conditions:"]
        if len(conds) > 1:
            lines.append("        gate: and")
        for j, cond in enumerate(conds, 1):
            ph, val = cond[0], cond[1]
            op = cond[2] if len(cond) > 2 else "=="
            lines += [f"        {j}:",
                      f'          first: "papi:{ph}"',
                      f"          second: \"'{val}'\"",
                      f"          operation: '{op}'"]
        return lines

    def add(name, x, y, layer, cond=None):
        nonlocal n
        block = [f"    {n}:", f"      name: {name}",
                 f"      x: {x}", f"      y: {y}", f"      layer: {layer}"]
        if cond:
            block += conds_block(cond)
        img_lines.extend(block)
        n += 1

    def add_builtin(name, x, y, layer, first, second, op="=="):
        """Same as `add`, but gated on a BetterHud BUILT-IN placeholder rather than a
        `papi:legendcraft_*` one. Built-ins are already typed (Number / Boolean), so they take
        neither the `papi:` prefix nor `conds_block`'s string quoting — quoting a Boolean here
        makes BetterHud compare a Boolean against a String and the element never draws."""
        nonlocal n
        img_lines.extend([f"    {n}:", f"      name: {name}",
                          f"      x: {x}", f"      y: {y}", f"      layer: {layer}",
                          "      conditions:", "        1:",
                          f"          first: {first}",
                          f"          second: {second}",
                          f"          operation: '{op}'"])
        n += 1

    RT = "legendcraft_resource_type"
    add("lc_bar_empty", bl, r0, 1)                  # channels (layer 1)
    add("lc_bar_empty", br, r0, 1)
    add("lc_bar_empty", bl, r1, 1)
    add("lc_bar_empty", br, r1, 1)
    add("lc_xp_empty", xpx, xpy, 1)
    add("lc_fill_health", bl + p, r0 + p, 2)        # fills (layer 2)
    add("lc_fill_armor", br + p, r0 + p, 2)
    add("lc_fill_mana", bl + p, r1 + p, 2, (RT, "mana"))
    add("lc_fill_energy", bl + p, r1 + p, 2, (RT, "energy"))
    add("lc_fill_rage", bl + p, r1 + p, 2, (RT, "rage"))
    add("lc_fill_food", br + p, r1 + p, 2)
    add("lc_fill_xp", xpx + 1, xpy + 1, 2)
    iy0 = r0 + (BAR_H - STAT_ICON_H) // 2       # icons are 9px tall on 7px bars -> overhang 1px
    iy1 = r1 + (BAR_H - STAT_ICON_H) // 2
    add("lc_icon_heart", 0, iy0, 3)                 # icons + gems (layer 3)
    add("lc_icon_shield", ir, iy0, 3)
    add("lc_gem_mana", 0, iy1, 3, (RT, "mana"))
    add("lc_gem_energy", 0, iy1, 3, (RT, "energy"))
    add("lc_gem_rage", 0, iy1, 3, (RT, "rage"))
    add("lc_icon_drumstick", ir, iy1, 3)

    # --- Health-bar affliction states (hud-and-icons.md §2 "Bar behaviors"). ------------------
    # Every gate is a BetterHud BUILT-IN placeholder, so none of this reaches `HudPlaceholders`
    # and none of it can go dark the way a `papi:legendcraft_*` element does when the plugin jar
    # and this config ship from different revisions. `!= 0` rather than `> 0` because BetterHud
    # LAYOUT conditions reject the ordering operators (see conds_block).
    for img, ico, il, icl, first, second in (
        ("lc_state_poison", "lc_heart_poison", VIT_L_POISON, VIT_L_ICON_POISON,
         "potion_effect_duration:poison", 0),
        ("lc_state_burning", "lc_heart_burning", VIT_L_BURNING, VIT_L_ICON_BURNING,
         "burning", "true"),
        ("lc_state_freezing", "lc_heart_freezing", VIT_L_FREEZE, VIT_L_ICON_FREEZE,
         "frozen", "true"),
        ("lc_state_wither", "lc_heart_wither", VIT_L_WITHER, VIT_L_ICON_WITHER,
         "potion_effect_duration:wither", 0),
    ):
        op = "!=" if second == 0 else "=="
        add_builtin(img, bl + p, r0 + p, il, first, second, op)
        add_builtin(ico, 0, iy0, icl, first, second, op)
    # Regeneration has no heart of its own — the pulse over the fill is the whole signal.
    add_builtin("lc_state_regeneration", bl + p, r0 + p, VIT_L_REGEN,
                "potion_effect_duration:regeneration", 0, "!=")

    # --- Framed skill-icon row, centered above the two-bar span. Two variants selected by the
    # class's visible-slot count (legendcraft_slot_count): a 3-slot row (base classes) and a
    # 4-slot row (subclasses, + ult slot), EACH centered for its own width so 3 and 4 both
    # sit centered. Weathered-iron frame + the real per-class art from hud_icon_map, falling
    # back to the placeholder field for any skill whose icon isn't drawn yet. Every tile is
    # SKILL_TILE square (the peaked ult keystone is still deferred, so no ULT_* geometry is
    # read here). Classless (slot_count 0) shows neither row. The cooldown shroud, out-of-mana
    # tint, countdown numeral, charge pips and deny flash all ship — see the per-slot adds below.
    span_cx = bl + (2 * BAR_W + GM) // 2

    txt_lines, tn = [], 1

    def addt(pattern, x, y, align="center", scale=STAT_TEXT_SCALE, cond=None, font="lc_stat_text"):
        nonlocal tn
        block = [f"    {tn}:", f"      name: {font}",
                 f'      pattern: "{pattern}"',
                 f"      align: {align}", f"      scale: {scale}",
                 f"      x: {x}", f"      y: {y}", f"      layer: {TILE_L_TEXT}"]
        if cond:
            block += conds_block(cond)
        txt_lines.extend(block)
        tn += 1

    def framed_row(slot_ids, count_val):
        # All slots use the same subclass frame (the special ult keystone is deferred). One tile is
        # the TILE_L_* stack, bottom to top: the frame, the near-black field, the per-class art, the
        # circle-split cooldown shroud (a listener that self-hides at 0%), the out-of-mana tint
        # (shown only when this row AND the slot is starved), the charge pips / locked-ult art, and
        # the cast-deny flash — plus a self-blanking countdown numeral. The ordering lives in those
        # constants and NOWHERE else: never restate a layer number here, because a comment that
        # repeats one is how the shroud and the tint came to claim the same layer in the first
        # place. Gated on slot_count so only this row shows.
        total = len(slot_ids) * SKILL_TILE + (len(slot_ids) - 1) * SKILL_FRAME_GAP
        x0 = span_cx - total // 2
        fy = SKILL_ROW_Y_PX                      # hoisted above the native held-item-name lane
        cnt = ("legendcraft_slot_count", count_val)
        for i, sid in enumerate(slot_ids):
            fx = x0 + i * (SKILL_TILE + SKILL_FRAME_GAP)
            ax, ay = fx + SKILL_ART_OFF, fy + SKILL_ART_OFF
            add("lc_skill_frame", fx, fy, TILE_L_FRAME, cnt)
            add("lc_icon_placeholder", ax, ay, TILE_L_FIELD, cnt)
            # Real per-class art (from hud_icon_map) drawn OVER the placeholder field (TILE_L_ART),
            # gated on this row AND the player's class. A slot without a finished icon keeps the placeholder.
            # A class contributes to a row when its list is at least this row's width (`>=`). Base
            # classes (3 entries) feed only the 3-slot row; subclasses (4) feed the 4-slot row. The
            # `>=` also lets a subclass draw its 3 CORE icons in the 3-slot row, which nothing
            # currently selects — a subclass reports slot_count=4 at EVERY level, including below 20
            # (LegendCraft-Classes c74b672; before that, a sub-20 subclass showed the 3-slot row).
            # Kept because it costs nothing and is the correct fallback if a 3-slot subclass ever exists.
            for classid, icons in CLASS_SKILL_ICONS.items():
                if len(icons) >= len(slot_ids) and icons[i]:
                    add(f"lc_hud_{classid}_{icons[i]}", ax, ay, TILE_L_ART,
                        [cnt, ("legendcraft_subclass", classid)])
            add(f"lc_cd_shroud_{sid}", ax, ay, TILE_L_SHROUD, cnt)
            # The out-of-mana tint sits STRICTLY ABOVE the sweep (§3 "Both"): a slot that is both
            # cooling down and unaffordable shows the radial ticking down AND the red wash over it,
            # so neither problem hides the other. The plugin reports `starved` on affordability
            # alone (independent of cooldown) to make this reachable.
            add("lc_oom_soft", ax, ay, TILE_L_OOM, [cnt, (f"legendcraft_{sid}_state", "starved")])
            # Cast-deny fade-in (UX-1a): a play_once translucent-white wash that fades in over the
            # ability when a cast on this slot is denied (cooldown / no resource / frozen / killswitch).
            # Placed at the icon's own (ax,ay) with scale 0.5 so it covers the skill icon exactly (not
            # the frame border); TILE_L_DENY so it reads over the icon art, the shroud and the tint.
            add("lc_deny_flash", ax, ay, TILE_L_DENY, [cnt, (f"legendcraft_{sid}_flash", "deny")])
            if sid == "ult":
                # Locked ultimate (subclass level < 20): the slot stays in the row and draws
                # the ult's `_locked` art (motif silhouette on its dimmed painted field) over
                # the ready art, plus the parchment unlock-level numeral — a promise, not a
                # button (HUD_AND_ICONS.md §3). LIVE since LegendCraft-Classes c74b672 — the
                # plugin now reports slot_count=4 for pre-20 subclasses, which is the gate this
                # was dormant behind. Before that these elements were unreachable in every
                # build: they need slot_count=='4' AND ult_state=='locked', and those two were
                # mutually exclusive while slot_count counted the ult only from level 20.
                for classid, icons in CLASS_SKILL_ICONS.items():
                    if len(icons) >= len(slot_ids) and icons[i]:
                        add(f"lc_hud_{classid}_{icons[i]}_locked", ax, ay, TILE_L_BADGE,
                            [cnt, ("legendcraft_subclass", classid),
                             ("legendcraft_ult_state", "locked")])
                addt("<gray>20", fx + SKILL_TILE // 2,
                     fy + (SKILL_TILE - SKILL_TEXT_H) // 2,
                     cond=[cnt, ("legendcraft_ult_state", "locked")],
                     scale=SKILL_NUM_SCALE)
            # Center numeral (same font as the stat bars, lc_stat_text) — shown for ALL abilities:
            # normal skills = cooldown seconds, charge skills = seconds until the next charge. The
            # charge COUNT sits outside the top-right corner so the two never collide.
            addt(f"<white>[papi:legendcraft_{sid}_cd_secs]", fx + SKILL_TILE // 2,
                 fy + (SKILL_TILE - SKILL_TEXT_H) // 2, cond=cnt, scale=SKILL_NUM_SCALE)
            # Charge pips — a gold row across the TOP of the icon (keybinds will own the bottom).
            # The row is 8px (even) so it sits EXACTLY centred in the 16px field. One row sprite per
            # charge count, gated on this slot's `charges == k` (BetterHud layout conditions are
            # ==/!= only). `charges` is blank for non-charge skills, so none of 0..max match and the
            # row is hidden; a charge skill at k charges shows k lit + (max-k) dulled pips.
            pip_start = ax + (ART - (SKILL_PIP * SKILL_MAX_PIPS + SKILL_PIP_GAP * (SKILL_MAX_PIPS - 1))) // 2
            for k in range(SKILL_MAX_PIPS + 1):
                add(f"lc_charge_row_{k}", pip_start, ay + 1, TILE_L_BADGE,
                    [cnt, (f"legendcraft_{sid}_charges", k)])
            # UX-2 input hint (shared chrome, identical for every class): Sneak + L/R/Q/F
            # straddling the bottom frame border. Centred on the tile; placed by the sprite's
            # base_ref so all four slots' hints share one bottom edge regardless of pair
            # height. Gated only on this row (slot presence); the ult keeps its hint while
            # locked. INPUT_L_GLYPH so the glyph outlines override the steel keyline.
            gsprite, _ = input_glyph(sid)
            # the sprite is hi-res but BetterHud renders it at KEY_SCALE, so place by the
            # on-screen (scaled) size: centred, bottom KEY_DROP px below the tile bottom.
            dw = round(gsprite.width * KEY_SCALE)
            dh = round(gsprite.height * KEY_SCALE)
            add(f"lc_input_{sid}",
                fx + (SKILL_TILE - dw) // 2,
                fy + SKILL_TILE + KEY_DROP - dh, INPUT_L_GLYPH, cnt)

    framed_row(["slot1", "slot2", "slot3"], "3")
    framed_row(["slot1", "slot2", "slot3", "ult"], "4")

    # One painted line owns all short combat feedback. The plugin returns an empty snapshot
    # when its two-second TTL has elapsed, so the element disappears without a layout gate.
    addt("<white>[papi:legendcraft_feedback_line]", span_cx, FEEDBACK_LINE_Y_PX,
         scale=FEEDBACK_TEXT_SCALE)

    # BetterHud's text parser EATS a single "/". The structure that parses cleanly is a tag on
    # BOTH sides of the separator (current <white>, max <white>, <gray> carrying the divider); the
    # separator must be "//" so one slash survives the eating and renders as "17 / 17". A bare "/"
    # here rendered as "2020" (eaten); dropping the tag after it broke parsing entirely. Spaces sit
    # inside the <gray> run around the "//" to match the reference's "17 / 17" spacing.
    W, G, GR = "<white>", "<gray>", "<green>"
    SEP = f"{G} // {W}"                              # gray, spaced divider that survives the eating
    # BetterHud text y is the element TOP, so center vertically = row_top + (bar_h - text_h)/2.
    # (The old `mid + DY` treated y as the mid-line and pushed the numerals out the bar bottom.)
    ty0 = r0 + (BAR_H - STAT_TEXT_H) // 2 + STAT_TEXT_DY
    ty1 = r1 + (BAR_H - STAT_TEXT_H) // 2 + STAT_TEXT_DY
    tyx = xpy + (XP_H - STAT_TEXT_H) // 2 + STAT_TEXT_DY          # 5px XP numerals fill the 5px bar
    tyl = xpy + (XP_H - STAT_LEVEL_H) // 2 + STAT_TEXT_DY         # 7px level overhangs the bar 1px
    addt(f"{W}[papi:legendcraft_health]{SEP}[papi:legendcraft_max_health]", bl + BAR_W // 2, ty0)
    addt(f"{W}[papi:legendcraft_armor]{SEP}20", br + BAR_W // 2, ty0)
    addt(f"{W}[papi:legendcraft_resource_current]{SEP}[papi:legendcraft_resource_max]", bl + BAR_W // 2, ty1)
    addt(f"{W}[papi:legendcraft_food]{SEP}20", br + BAR_W // 2, ty1)
    # XP row: level centered on the bar (larger, overhangs); "current / needed" XP right-aligned at the end.
    addt(f"{GR}[papi:legendcraft_level]", xpx + XP_W // 2, tyl, scale=STAT_LEVEL_SCALE)
    addt(f"{W}[papi:legendcraft_xp_current]{SEP}[papi:legendcraft_xp_needed]", xpx + XP_W - 2, tyx, align="right")

    out = ["# GENERATED by assets/tools/generate_hud.py -- do not hand-edit.",
           "# Chunky 2x2 stat block: HP | armor / resource | food, then XP bar + level.",
           "lc_stat:", "  images:"] + img_lines + ["  texts:"] + txt_lines
    return "\n".join(out)

# Party frames (hand-authored, `betterhud/layouts/legendcraft-party.yml`) ride as a SECOND
# LAYOUT of the one hud, never as a second hud: BetterHud gives each default-hud its own bossbar
# carrier and only the first repositions, so a second default-hud dumps its glyphs at the top
# boss-bar line. Layouts carry their own anchors, so `lc_party` gets the left edge while
# `lc_stat` keeps bottom-center. The layout is defined by hand because it is Volya-derived art
# on its own geometry -- nothing here computes its offsets, so nothing here can drift from it.
PARTY_HUD_GUI_X = 0      # left screen edge
PARTY_HUD_GUI_Y = 50     # vertically centered
PARTY_HUD_X = 4          # small inset off the edge
PARTY_HUD_Y = -42        # lift the 4-row stack (4 * PARTY_ROW_PITCH = 84) to straddle the center


def _bh_stat_hud_yml():
    return "\n".join([
        "# GENERATED by assets/tools/generate_hud.py -- do not hand-edit.",
        "# gui: percent anchor (50/100 = bottom center); pixel: px offset from it.",
        "# y offset sits the block above the vanilla hotbar -- tune in-client.",
        "lc_stat_hud:",
        "  layouts:",
        "    1:",
        "      name: lc_stat",
        "      gui:",
        "        x: 50",
        "        y: 100",
        "      pixel:",
        f"        x: {STAT_HUD_X}",
        f"        y: {STAT_HUD_Y}",   # stat block at its proven position; skill row is negative-y above it
        "    2:",
        "      name: lc_party",
        "      gui:",
        f"        x: {PARTY_HUD_GUI_X}",
        f"        y: {PARTY_HUD_GUI_Y}",
        "      pixel:",
        f"        x: {PARTY_HUD_X}",
        f"        y: {PARTY_HUD_Y}",
    ])

def _bh_stat_texts_yml():
    # A BetterHud "text" is a font definition; the numerals reference lc_stat_text.
    # Same schema as the stock entity_font, merging the default bitmap so digits render.
    return "\n".join([
        "# GENERATED by assets/tools/generate_hud.py -- do not hand-edit.",
        "# Font used by the stat HUD numerals (health/resource/level readouts).",
        "lc_stat_text:",
        "  merge-default-bitmap: true",
        "  use-unifont: true",
        "  include: []",
    ])

def export_betterhud_stat():
    for sub in ("images", "layouts", "huds", "texts"):
        os.makedirs(os.path.join(BH_DIR, sub), exist_ok=True)
    with open(os.path.join(BH_DIR, "texts", "legendcraft-stat.yml"), "w", encoding="utf-8") as f:
        f.write(_bh_stat_texts_yml() + "\n")
    with open(os.path.join(BH_DIR, "images", "legendcraft-stat.yml"), "w", encoding="utf-8") as f:
        f.write(_bh_stat_images_yml() + "\n")
    with open(os.path.join(BH_DIR, "layouts", "legendcraft-stat.yml"), "w", encoding="utf-8") as f:
        f.write(_bh_stat_layout_yml() + "\n")
    with open(os.path.join(BH_DIR, "huds", "legendcraft-stat.yml"), "w", encoding="utf-8") as f:
        f.write(_bh_stat_hud_yml() + "\n")

HUD_CONTRACT_IDS = {"shield_current", "shield_max"}


def export_placeholder_manifest():
    """Write hud-placeholders.txt: every emitted `papi:legendcraft_<id>` plus contract-carried
    plugin ids, one per line, sorted. This is the config side of the plugin<->HUD placeholder
    contract: every id listed here MUST be answered by LegendCraft-Classes' HudPlaceholders, or
    the HUD element gated on it silently vanishes (which is exactly how the skill-icon row went
    dark once). The plugin's HudPlaceholderContractTest reads this list and fails the build if the
    plugin stops answering any of them, so a rebuild can't drop a placeholder unnoticed. Scans only
    the config YAML (never README examples), and within it only NON-COMMENT lines. Both
    exclusions matter for the same reason: anything landing in this file becomes an obligation
    the plugin's build enforces. A prose mention of `papi:legendcraft_party_member_N` in a
    hand-authored layout's header comment would otherwise contribute the truncated id
    `legendcraft_party_member_` -- an id nothing can ever answer, failing the contract test
    forever over a sentence. Comments in these files are whole-line, so a first-non-space `#`
    is the whole test; an inline `#` is left alone because it is a hex color, not a comment."""
    # Shield projection is already part of the Classes contract. Carry those ids through unrelated
    # generator runs so a HUD slice cannot silently shrink the synchronized cross-repo manifest.
    found = set(HUD_CONTRACT_IDS)
    for sub in ("images", "layouts", "huds", "texts"):
        d = os.path.join(BH_DIR, sub)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if not name.endswith(".yml"):
                continue
            with open(os.path.join(d, name), encoding="utf-8") as f:
                body = "\n".join(ln for ln in f.read().splitlines()
                                 if not ln.lstrip().startswith("#"))
            found.update(re.findall(r"papi:legendcraft_([a-z0-9_]+)", body))
    path = os.path.join(BH_DIR, "hud-placeholders.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# GENERATED by generate_hud.py -- the plugin<->HUD placeholder contract.\n")
        f.write("# Every id here must be answered by LegendCraft-Classes HudPlaceholders\n")
        f.write("# (enforced by HudPlaceholderContractTest). One `legendcraft_<id>` per line.\n")
        for pid in sorted(found):
            f.write(f"legendcraft_{pid}\n")
    print(f"wrote {len(found)} HUD placeholder ids -> {path}")

def main():
    export_true_res()
    export_stat_bars()
    export_betterhud()
    export_betterhud_stat()
    export_placeholder_manifest()  # must run AFTER the exports so it scans the written YAML
    save(stat_hud_mock(), os.path.join(DIRS["prev"], "stat_hud_mock.png"))
    save(hudline_composite_mock(""), os.path.join(DIRS["prev"], "hudline-native-gap.png"))
    save(hudline_composite_mock("No target in sight."),
         os.path.join(DIRS["prev"], "hudline-target-deny.png"))
    save(hudline_composite_mock("+240 XP"), os.path.join(DIRS["prev"], "hudline-xp.png"))
    print("HUD assets written under", ROOT)

if __name__ == "__main__":
    main()
