#!/usr/bin/env python3
"""Flame Surge flame retime: rebuilds the three shipping surge_flame rigs' `erupt` clip at the source's pace.

Durable and re-runnable. Geometry, textures and bones come from the artist's delivery
(`surge_flame_<rank>.bbmodel`); the clip comes from the samusdev source state
`lava_obsidian_infernal_judgement` (3.05 s) in `infernal_judgement_vfx.bbmodel`, whose bones the
delivery keeps under their source uuids.

BetterModel advances one keyframe segment per tick, so a clip plays at its source pace only when
every animated channel carries a key on every tick. Each source channel is evaluated the way
Blockbench evaluates it (step holds the key before; catmullrom is Blockbench's uniform spline
through the two neighbouring keys on each side; otherwise linear) at every 0.05 s from 0 to 3.05,
and every sample is kept as a linear key, constant runs included. Position samples are multiplied
by the rank's downscale; rotation and scale samples are dimensionless and copied. A run is
byte-stable: key uuids derive from the bone, channel and tick.

    python mobs-src/props/surge_flame_retime.py <delivery>/flame-surge <source infernal_judgement_vfx.bbmodel>
"""

from __future__ import annotations

import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_CLIP = "lava_obsidian_infernal_judgement"
CLIP = "erupt"
TICK = 0.05
EPS = 1e-6

# The delivery's uniform downscale of the source, per rank.
DOWNSCALE = {
    "red": 0.0910929713,
    "orange": 0.1392054562,
    "white": 0.1873179410,
}


def value(key: dict, axis: str) -> float:
    return float(key["data_points"][0][axis])


def catmull(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    v0 = (p2 - p0) * 0.5
    v1 = (p3 - p1) * 0.5
    t2, t3 = t * t, t * t * t
    return (2 * p1 - 2 * p2 + v0 + v1) * t3 + (-3 * p1 + 3 * p2 - 2 * v0 - v1) * t2 + v0 * t + p1


def spline(points: list[float], t: float) -> float:
    """three.js SplineCurve.getPoint(t).y over `points`, the curve Blockbench samples."""
    p = (len(points) - 1) * t
    i = int(p)
    w = p - i
    p0 = points[i if i == 0 else i - 1]
    p1 = points[i]
    p2 = points[len(points) - 1 if i > len(points) - 2 else i + 1]
    p3 = points[len(points) - 1 if i > len(points) - 3 else i + 2]
    return catmull(w, p0, p1, p2, p3)


def sample(keys: list[dict], time: float, axis: str) -> float:
    if time <= keys[0]["time"] + EPS:
        return value(keys[0], axis)
    if time >= keys[-1]["time"] - EPS:
        return value(keys[-1], axis)
    i = max(n for n, k in enumerate(keys) if k["time"] <= time + EPS)
    before, after = keys[i], keys[i + 1]
    if abs(before["time"] - time) < EPS:
        return value(before, axis)
    alpha = (time - before["time"]) / (after["time"] - before["time"])
    if before["interpolation"] == "step":
        return value(before, axis)
    if before["interpolation"] == "catmullrom" or after["interpolation"] == "catmullrom":
        points = []
        if i > 0:
            points.append(value(keys[i - 1], axis))
        points += [value(before, axis), value(after, axis)]
        if i + 2 < len(keys):
            points.append(value(keys[i + 2], axis))
        return spline(points, (alpha + (1 if i > 0 else 0)) / (len(points) - 1))
    return value(before, axis) + (value(after, axis) - value(before, axis)) * alpha


def resampled(source: dict, length: float, downscale: float, bone: str) -> list[dict]:
    by_channel: dict[str, list] = {}
    for key in source.get("keyframes", []):
        assert len(key["data_points"]) == 1 and key["interpolation"] in ("linear", "catmullrom", "step")
        by_channel.setdefault(key["channel"], []).append(key)
    ticks = int(round(length / TICK))
    out = []
    for channel, keys in sorted(by_channel.items()):
        keys.sort(key=lambda k: k["time"])
        factor = downscale if channel == "position" else 1.0
        for tick in range(ticks + 1):
            time = round(tick * TICK, 4)
            point = {axis: round(sample(keys, time, axis) * factor, 9) for axis in ("x", "y", "z")}
            out.append({
                "channel": channel,
                "data_points": [point],
                "uuid": str(uuid.uuid5(uuid.NAMESPACE_OID, "%s/%s/%d" % (bone, channel, tick))),
                "time": time,
                "color": -1,
                "interpolation": "linear",
            })
    return out


def retime(model: dict, source: dict, downscale: float) -> None:
    (clip,) = model["animations"]
    assert clip["name"] == CLIP
    state = next(a for a in source["animations"] if a["name"] == SOURCE_CLIP)
    for bone, animator in clip["animators"].items():
        animator["keyframes"] = resampled(state["animators"].get(bone, {}), state["length"],
                                          downscale, bone)
    clip["length"] = state["length"]
    clip["loop"] = "hold"


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    with open(argv[2], encoding="utf-8") as handle:
        source = json.load(handle)
    for rank, downscale in DOWNSCALE.items():
        name = "surge_flame_%s.bbmodel" % rank
        with open(os.path.join(argv[1], name), encoding="utf-8") as handle:
            model = json.load(handle)
        retime(model, source, downscale)
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as out:
            json.dump(model, out, indent=2)
        print(name, model["animations"][0]["length"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
