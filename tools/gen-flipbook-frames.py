#!/usr/bin/env python3
"""Flat-flipbook frame generator: one item model per frame of each flipbook rig.

A flat flipbook is authored in Blockbench as a stack of frame bones that a clip shows one at a
time by stepping each bone's scale between 0.001 and its shown value. A BetterModel bone is an
item display and the client tweens that scale, so the stack morphs between drawings instead of
cutting. The plugin plays these frames on ONE item display that changes the item model it wears
on each frame's tick instead; this script writes those item models.

Durable, re-runnable tooling: it reads `mobs-src/props/FLIPBOOKS.md` (the table of flipbooks)
and each rig's `.bbmodel` named there, and rewrites, for every frame, under
`src/assets/legendcraft/`:

    items/classes/<frames>_<n>.json           the item definition the display's ITEM_MODEL names
    models/item/classes/<frames>_<n>.json     the frame's geometry, every plane it shows
    textures/item/classes/<frames>_<n>[_<k>].png   the textures those planes wear

Frames are numbered from 1 in the order the clip shows them. A frame is every element of every
bone visible over one span of the clip, so a split-hybrid or crossed frame is one model holding
all of its planes. Each element is placed where the rig draws it on that frame: its bones'
pivots and rotations, and the shown scale the clip steps its frame bone to, are baked into the
element, so the item model is the drawing at the size and orientation the rig showed it.

An item model's elements must stay inside [-16, 32] on every axis, a three-block box centred on
the display. A rig whose frames overrun it declares a `shrink` in FLIPBOOKS.md and is drawn at
1/shrink of its authored size; the plugin scales the display back up by the same factor. A row
whose frames still overrun the box is refused.

Output is deterministic: coordinates are rounded to a fixed precision and the PNGs are the
rig's embedded texture bytes, written unchanged. Before writing a flipbook it deletes that
flipbook's earlier frames, so a frame that no longer exists shows as a deleted file.

    python tools/gen-flipbook-frames.py
    python tools/check_generator_drift.py

Only the standard library is required.
"""

from __future__ import annotations

import base64
import json
import math
import os
import re
import sys

from void_marker import void_item

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
PROPS_DIR = os.path.join(REPO_ROOT, "mobs-src", "props")
TABLE_PATH = os.path.join(PROPS_DIR, "FLIPBOOKS.md")
ASSETS = os.path.join(REPO_ROOT, "src", "assets", "legendcraft")
ITEMS_DIR = os.path.join(ASSETS, "items", "classes")
MODELS_DIR = os.path.join(ASSETS, "models", "item", "classes")
TEXTURES_DIR = os.path.join(ASSETS, "textures", "item", "classes")

NAMESPACE = "legendcraft"
TICKS_PER_SECOND = 20

# Blockbench and Minecraft both count 16 model units to the block, and an item display draws its
# model with the model's (8, 8, 8) at the entity's position.
MODEL_CENTRE = 8.0
MODEL_MIN = -16.0
MODEL_MAX = 32.0

# A frame bone parked at 0.001 is hidden; anything above this is shown.
VISIBLE_SCALE = 0.01

# Six decimals of a model unit is far below a pixel and keeps every coordinate reproducible.
PRECISION = 6

# How far a baked element's linear part may stray from a uniformly scaled rotation.
UNIFORM_TOLERANCE = 1.0e-6

ALLOWED_SHRINKS = (1, 2, 4)

# A tinted flipbook multiplies every face by the first colour of the worn item's
# custom_model_data component; an item with no colour draws the frame as painted. A void
# flipbook's faces carry the void-window mark instead (see void_marker.py).
TINT_INDEX = 0
UNTINTED = -1

FRAME_SUFFIX = re.compile(r"^_\d+(?:_\d+)?\.(?:json|png)$")


class GeneratorError(Exception):
    pass


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------

def read_table(path=TABLE_PATH):
    """The FLIPBOOKS.md rows: frames name, rig, clip, shrink, and the bones the display animates."""
    if not os.path.isfile(path):
        raise GeneratorError("no flipbook table at %s" % path)
    rows = []
    header = None
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line.startswith("|"):
                if header is not None and rows:
                    break
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if header is None:
                if cells and cells[0] == "frames":
                    header = cells
                continue
            if set(cells[0]) <= set("-: "):
                continue
            row = dict(zip(header, cells))
            rows.append(row)
    if header is None:
        raise GeneratorError("%s has no table whose first column is `frames`" % path)
    parsed = []
    seen = set()
    for row in rows:
        frames = strip_code(row.get("frames", ""))
        rig = strip_code(row.get("rig", ""))
        clip = strip_code(row.get("clip", ""))
        try:
            shrink = int(strip_code(row.get("shrink", "")))
        except ValueError:
            raise GeneratorError("row %s: shrink must be one of %s" % (frames, ALLOWED_SHRINKS))
        if shrink not in ALLOWED_SHRINKS:
            raise GeneratorError("row %s: shrink %d is not one of %s"
                                 % (frames, shrink, ALLOWED_SHRINKS))
        native = [strip_code(bone) for bone in row.get("native", "").split(",")
                  if strip_code(bone)]
        tint = strip_code(row.get("tint", ""))
        if tint not in ("", "yes", "void"):
            raise GeneratorError("row %s: tint is `yes`, `void` or empty, not %r"
                                 % (frames, tint))
        if not re.fullmatch(r"[a-z0-9_]+", frames or "!"):
            raise GeneratorError("row %r: frames must be a lower-case item name" % frames)
        if frames in seen:
            raise GeneratorError("row %s appears twice" % frames)
        seen.add(frames)
        parsed.append({"frames": frames, "rig": rig, "clip": clip, "shrink": shrink,
                       "native": native, "tint": tint or None})
    if not parsed:
        raise GeneratorError("%s names no flipbook" % path)
    return parsed


def strip_code(cell):
    return cell.strip().strip("`").strip()


# ---------------------------------------------------------------------------
# Linear algebra, 3x3 and affine
# ---------------------------------------------------------------------------

def rot_x(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def rot_y(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rot_z(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def apply(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def euler_matrix(rotation):
    """Blockbench and Minecraft both turn about X, then Y, then Z: R = Rz . Ry . Rx."""
    x, y, z = (float(value) for value in rotation)
    return mul(rot_z(z), mul(rot_y(y), rot_x(x)))


def euler_of(m):
    """The (x, y, z) degrees whose X-then-Y-then-Z turn is the rotation matrix {@code m}."""
    sy = -m[2][0]
    sy = max(-1.0, min(1.0, sy))
    y = math.asin(sy)
    if abs(math.cos(y)) > 1.0e-9:
        x = math.atan2(m[2][1], m[2][2])
        z = math.atan2(m[1][0], m[0][0])
    else:
        x = math.atan2(-m[1][2], m[1][1])
        z = 0.0
    return [math.degrees(x), math.degrees(y), math.degrees(z)]


class Affine:
    """p -> linear . p + offset."""

    def __init__(self, linear, offset):
        self.linear = linear
        self.offset = offset

    @staticmethod
    def identity():
        return Affine([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, 0.0])

    def then_inner(self, inner):
        """self(inner(p))."""
        return Affine(mul(self.linear, inner.linear),
                      [a + b for a, b in zip(apply(self.linear, inner.offset), self.offset)])

    def at(self, point):
        return [a + b for a, b in zip(apply(self.linear, point), self.offset)]


def about(pivot, linear):
    """A linear map applied about {@code pivot}."""
    moved = apply(linear, pivot)
    return Affine(linear, [p - m for p, m in zip(pivot, moved)])


def scale_matrix(scale):
    return [[scale[0], 0, 0], [0, scale[1], 0], [0, 0, scale[2]]]


# ---------------------------------------------------------------------------
# The rig
# ---------------------------------------------------------------------------

def load_rig(name):
    path = os.path.join(PROPS_DIR, name + ".bbmodel")
    if not os.path.isfile(path):
        raise GeneratorError("rig %s has no %s" % (name, os.path.relpath(path, REPO_ROOT)))
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def bones_of(rig):
    """Every bone by uuid: its name, pivot, rest rotation, parent uuid and element uuids.

    A Blockbench 5 save keeps each bone's properties in a top-level ``groups`` list and only its
    uuid and children in the outliner; an older save keeps both in the outliner."""
    bones = {}
    groups = {group["uuid"]: group for group in rig.get("groups", [])}

    def walk(children, parent):
        for child in children:
            if isinstance(child, dict):
                props = dict(groups.get(child["uuid"], {}), **child)
                bones[child["uuid"]] = {
                    "name": props["name"],
                    "origin": [float(v) for v in props.get("origin", [0, 0, 0])],
                    "rotation": [float(v) for v in props.get("rotation", [0, 0, 0])],
                    "parent": parent,
                    "elements": [c for c in child.get("children", []) if isinstance(c, str)],
                }
                walk(child.get("children", []), child["uuid"])

    walk(rig.get("outliner", []), None)
    return bones


def clip_of(rig, clip_name):
    for animation in rig.get("animations", []):
        if animation.get("name") == clip_name:
            return animation
    raise GeneratorError("rig has no clip %r" % clip_name)


def ticks(seconds):
    return int(round(float(seconds) * TICKS_PER_SECOND))


def scale_value(keyframe):
    point = keyframe["data_points"][0]
    values = [float(point.get(axis, 1.0)) for axis in ("x", "y", "z")]
    return values


def step_tracks(clip, bones, native, row_name):
    """The scale-step track of every bone the clip animates: [(tick, (sx, sy, sz)), ...]."""
    by_name = {bone["name"]: uuid for uuid, bone in bones.items()}
    tracks = {}
    for animator_id, animator in clip.get("animators", {}).items():
        name = animator.get("name")
        uuid = animator_id if animator_id in bones else by_name.get(name)
        if uuid is None:
            continue
        keyframes = animator.get("keyframes", [])
        if not keyframes:
            continue
        if name in native:
            continue
        for keyframe in keyframes:
            if keyframe.get("channel") != "scale" or keyframe.get("interpolation") != "step":
                raise GeneratorError(
                    "%s: bone %s carries a %s %s key; a flipbook frame only steps its scale, and "
                    "a bone the display animates is named in the row's `native` column"
                    % (row_name, name, keyframe.get("interpolation"), keyframe.get("channel")))
        track = sorted(((ticks(k["time"]), tuple(scale_value(k))) for k in keyframes),
                       key=lambda entry: entry[0])
        tracks[uuid] = track
    if not tracks:
        raise GeneratorError("%s: the clip steps no bone" % row_name)
    return tracks


def value_at(track, tick):
    shown = None
    for at, value in track:
        if at <= tick:
            shown = value
        else:
            break
    return shown if shown is not None else (1.0, 1.0, 1.0)


def frame_spans(clip, tracks, row_name):
    """The clip's spans in order: (start tick, {bone uuid: shown scale}) for every span that shows
    something. A span starts at every tick a key changes what is shown."""
    length = ticks(clip.get("length", 0))
    boundaries = sorted({0} | {at for track in tracks.values() for at, _ in track if at < length})
    spans = []
    previous = None
    for start in boundaries:
        shown = {}
        for uuid, track in tracks.items():
            value = value_at(track, start)
            if min(value) > VISIBLE_SCALE:
                shown[uuid] = value
            elif max(value) > VISIBLE_SCALE:
                raise GeneratorError("%s: a bone is shown on one axis and hidden on another at "
                                     "tick %d" % (row_name, start))
        key = tuple(sorted((uuid, value) for uuid, value in shown.items()))
        if key == previous:
            continue
        previous = key
        if shown:
            spans.append((start, shown))
    if not spans:
        raise GeneratorError("%s: the clip never shows a frame" % row_name)
    return spans


def chain(bones, uuid):
    """The bone and its ancestors, root first."""
    out = []
    while uuid is not None:
        out.append(uuid)
        uuid = bones[uuid]["parent"]
    return list(reversed(out))


def bone_transform(bones, uuid, shown):
    """Model space from the bone's own space: every ancestor's rest turn about its pivot, with the
    shown scale of any stepped bone applied about that bone's pivot."""
    total = Affine.identity()
    for link in chain(bones, uuid):
        bone = bones[link]
        linear = euler_matrix(bone["rotation"])
        if link in shown:
            linear = mul(linear, scale_matrix(shown[link]))
        total = total.then_inner(about(bone["origin"], linear))
    return total


def is_visible(bones, uuid, shown, tracks):
    """Whether every stepped bone on the chain is shown on this span."""
    for link in chain(bones, uuid):
        if link in tracks and link not in shown:
            return False
    return True


def uniform_rotation(linear, where):
    """(scale, rotation) for a linear part that is a positive uniform scale of a rotation."""
    columns = [[linear[r][c] for r in range(3)] for c in range(3)]
    lengths = [math.sqrt(sum(v * v for v in col)) for col in columns]
    scale = lengths[0]
    if scale <= 0 or any(abs(length - scale) > UNIFORM_TOLERANCE * max(1.0, scale)
                         for length in lengths):
        raise GeneratorError("%s: a non-uniform scale meets a rotation; an item-model element "
                             "can carry a rotation or a stretch, not both" % where)
    rotation = [[linear[r][c] / scale for c in range(3)] for r in range(3)]
    det = (rotation[0][0] * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
           - rotation[0][1] * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
           + rotation[0][2] * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0]))
    if det < 0:
        raise GeneratorError("%s: a mirrored element cannot be drawn by an item model" % where)
    return scale, rotation


def axis_scales(linear):
    """The per-axis stretch of a linear part with no rotation, or None if it rotates."""
    for r in range(3):
        for c in range(3):
            if r != c and abs(linear[r][c]) > UNIFORM_TOLERANCE:
                return None
    return [linear[0][0], linear[1][1], linear[2][2]]


def number(value):
    value = round(value, PRECISION)
    if value == 0:
        return 0
    if value == int(value):
        return int(value)
    return value


def bake_element(element, transform, shrink, where):
    """The item-model element for one rig element as its frame draws it."""
    origin = [float(v) for v in element.get("origin", [0, 0, 0])]
    local = about(origin, euler_matrix(element.get("rotation", [0, 0, 0])))
    placed = transform.then_inner(local)
    low = [float(v) for v in element["from"]]
    high = [float(v) for v in element["to"]]
    centre = [(a + b) / 2.0 for a, b in zip(low, high)]
    half = [(b - a) / 2.0 for a, b in zip(low, high)]

    stretch = axis_scales(placed.linear)
    if stretch is not None:
        scales = stretch
        angles = [0.0, 0.0, 0.0]
        if any(s <= 0 for s in scales):
            raise GeneratorError("%s: a mirrored or collapsed element" % where)
    else:
        uniform, rotation = uniform_rotation(placed.linear, where)
        scales = [uniform] * 3
        angles = euler_of(rotation)

    world_centre = placed.at(centre)
    model_centre = [c / shrink + MODEL_CENTRE for c in world_centre]
    model_half = [h * s / shrink for h, s in zip(half, scales)]
    lo = [c - h for c, h in zip(model_centre, model_half)]
    hi = [c + h for c, h in zip(model_centre, model_half)]
    for value in lo + hi:
        if value < MODEL_MIN - 1.0e-9 or value > MODEL_MAX + 1.0e-9:
            raise GeneratorError("%s: element %s reaches %.3f, outside the item model's [%d, %d] "
                                 "box at shrink %d; raise the row's shrink"
                                 % (where, element.get("name"), value, MODEL_MIN, MODEL_MAX,
                                    shrink))
    baked = {"from": [number(v) for v in lo], "to": [number(v) for v in hi]}
    angles = [number(a) for a in angles]
    if any(angles):
        rotation = {"origin": [number(v) for v in model_centre]}
        for axis, angle in zip(("x", "y", "z"), angles):
            if angle:
                rotation[axis] = angle
        baked["rotation"] = rotation
    return baked


def face_uv(uv, texture):
    width = float(texture.get("uv_width") or texture.get("width"))
    height = float(texture.get("uv_height") or texture.get("height"))
    return [number(uv[0] * 16.0 / width), number(uv[1] * 16.0 / height),
            number(uv[2] * 16.0 / width), number(uv[3] * 16.0 / height)]


def texture_bytes(texture, where):
    source = texture.get("source", "")
    prefix = "data:image/png;base64,"
    if not source.startswith(prefix):
        raise GeneratorError("%s: texture %s is not embedded as a PNG" % (where, texture["name"]))
    data = base64.b64decode(source[len(prefix):])
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise GeneratorError("%s: texture %s does not decode to a PNG" % (where, texture["name"]))
    return data


# ---------------------------------------------------------------------------
# One flipbook
# ---------------------------------------------------------------------------

def build(row):
    """Every file one flipbook row writes: {relative path: bytes}."""
    rig = load_rig(row["rig"])
    where = "%s (%s.%s)" % (row["frames"], row["rig"], row["clip"])
    bones = bones_of(rig)
    elements = {element["uuid"]: element for element in rig.get("elements", [])}
    textures = rig.get("textures", [])
    clip = clip_of(rig, row["clip"])
    tracks = step_tracks(clip, bones, row["native"], where)
    spans = frame_spans(clip, tracks, where)

    files = {}
    for index, (start, shown) in enumerate(spans, start=1):
        name = "%s_%d" % (row["frames"], index)
        frame_where = "%s frame %d (tick %d)" % (where, index, start)
        used = []
        baked_elements = []
        for uuid in bones_in_outliner_order(rig):
            if not is_visible(bones, uuid, shown, tracks):
                continue
            transform = bone_transform(bones, uuid, shown)
            for element_id in bones[uuid]["elements"]:
                element = elements[element_id]
                if element.get("type", "cube") != "cube":
                    raise GeneratorError("%s: element %s is not a cube"
                                         % (frame_where, element.get("name")))
                baked = bake_element(element, transform, row["shrink"], frame_where)
                faces = {}
                for side in ("north", "east", "south", "west", "up", "down"):
                    face = element.get("faces", {}).get(side)
                    if not face or face.get("texture") is None:
                        continue
                    texture_index = int(face["texture"])
                    if texture_index not in used:
                        used.append(texture_index)
                    entry = {"uv": face_uv(face["uv"], textures[texture_index]),
                             "texture": "#%d" % used.index(texture_index)}
                    if face.get("rotation"):
                        entry["rotation"] = int(face["rotation"])
                    if row["tint"]:
                        entry["tintindex"] = TINT_INDEX
                    faces[side] = entry
                if not faces:
                    continue
                baked["faces"] = faces
                baked_elements.append(baked)
        if not baked_elements:
            raise GeneratorError("%s shows no textured face" % frame_where)

        texture_names = []
        for position, texture_index in enumerate(used, start=1):
            texture_name = name if len(used) == 1 else "%s_%d" % (name, position)
            texture_names.append(texture_name)
            files[os.path.join("textures", "item", "classes", texture_name + ".png")] = \
                texture_bytes(textures[texture_index], frame_where)

        model = {
            "textures": dict([(str(i), "%s:item/classes/%s" % (NAMESPACE, t))
                              for i, t in enumerate(texture_names)]
                             + [("particle", "%s:item/classes/%s" % (NAMESPACE, texture_names[0]))]),
            "elements": baked_elements,
        }
        item = {"model": {"type": "minecraft:model",
                          "model": "%s:item/classes/%s" % (NAMESPACE, name)}}
        if row["tint"] == "void":
            item = void_item("%s:item/classes/%s" % (NAMESPACE, name))
        elif row["tint"]:
            item["model"]["tints"] = [{"type": "minecraft:custom_model_data",
                                       "index": TINT_INDEX, "default": UNTINTED}]
        files[os.path.join("models", "item", "classes", name + ".json")] = encode(model)
        files[os.path.join("items", "classes", name + ".json")] = encode(item)
    return files


def bones_in_outliner_order(rig):
    order = []

    def walk(children):
        for child in children:
            if isinstance(child, dict):
                order.append(child["uuid"])
                walk(child.get("children", []))

    walk(rig.get("outliner", []))
    return order


NUMBER_LIST = re.compile(r"\[\s*(-?[0-9][0-9.e+-]*(?:,\s*-?[0-9][0-9.e+-]*)*)\s*\]")


def encode(document):
    """Indented JSON with every list of numbers kept on one line."""
    text = json.dumps(document, indent=2, ensure_ascii=False)
    text = NUMBER_LIST.sub(lambda m: "[" + ", ".join(re.split(r",\s*", m.group(1))) + "]", text)
    return (text + "\n").encode("utf-8")


def stale_frames(stem):
    """Every file an earlier run wrote for flipbook {@code stem}."""
    out = []
    for directory in (ITEMS_DIR, MODELS_DIR, TEXTURES_DIR):
        if not os.path.isdir(directory):
            continue
        for entry in os.listdir(directory):
            if entry.startswith(stem) and FRAME_SUFFIX.match(entry[len(stem):]):
                out.append(os.path.join(directory, entry))
    return out


def main(argv=None) -> int:
    try:
        rows = read_table()
        stems = {row["frames"] for row in rows}
        for row in rows:
            for other in stems:
                if other != row["frames"] and other.startswith(row["frames"] + "_") \
                        and re.fullmatch(r"\d+", other[len(row["frames"]) + 1:] or "x"):
                    raise GeneratorError("frames %s collides with %s's frame names"
                                         % (other, row["frames"]))
        outputs = {}
        for row in rows:
            for path, data in build(row).items():
                if path in outputs:
                    raise GeneratorError("two rows write %s" % path)
                outputs[path] = data
    except GeneratorError as error:
        print("FAIL: %s" % error)
        return 1

    for row in rows:
        for path in stale_frames(row["frames"]):
            os.remove(path)
    written = 0
    for path, data in sorted(outputs.items()):
        target = os.path.join(ASSETS, path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as handle:
            handle.write(data)
        written += 1
    frames = sum(1 for path in outputs if path.startswith(os.path.join("items", "")))
    print("OK: %d flipbook(s), %d frame(s), %d file(s) written" % (len(rows), frames, written))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
