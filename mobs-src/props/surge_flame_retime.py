#!/usr/bin/env python3
"""Flame Surge flame retime: writes the four shipping surge_flame rigs from the artist's delivery.

Durable and re-runnable. The delivered `surge_flame_<rank>.bbmodel` clips open with a 0.20 s
lead (keys from 0, action from 0.20, length 1.10) that matches the volcano's eruption inside the
comparison scene. In game the plugin spawns the flame 4 ticks (0.20 s) into the volcano's
`erupt_*` clip, so the lead is cut here: every key moves 0.20 s earlier, the pose each channel
holds at 0.20 s (the key there, or the linear sample between its neighbours) becomes its key at 0,
and the clip is 0.90 s. A run is byte-stable: the new key 0 takes an id derived from the key
it was sampled from. All delivered keys are linear with one data point, which the script
asserts. Geometry, textures and bones are unchanged.

    python mobs-src/props/surge_flame_retime.py <delivery>/flame-surge
"""

from __future__ import annotations

import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
RANKS = ("red", "orange", "white", "blue")
LEAD = 0.2
DELIVERED_LENGTH = 1.1
EPS = 1e-6


def lerp_point(a: dict, b: dict, t: float) -> dict:
    out = {}
    for axis in ("x", "y", "z"):
        va, vb = float(a[axis]), float(b[axis])
        out[axis] = "%.9f" % (va + (vb - va) * t)
    return out


def retime(model: dict) -> None:
    (clip,) = model["animations"]
    assert clip["name"] == "erupt" and abs(clip["length"] - DELIVERED_LENGTH) < EPS
    for animator in clip["animators"].values():
        by_channel: dict[str, list] = {}
        for key in animator["keyframes"]:
            assert key["interpolation"] == "linear" and len(key["data_points"]) == 1
            by_channel.setdefault(key["channel"], []).append(key)
        kept = []
        for keys in by_channel.values():
            keys.sort(key=lambda k: k["time"])
            before = [k for k in keys if k["time"] <= LEAD + EPS]
            after = [k for k in keys if k["time"] > LEAD + EPS]
            if before:
                last = before[-1]
                if abs(last["time"] - LEAD) < EPS or not after:
                    start = dict(last["data_points"][0])
                else:
                    t = (LEAD - last["time"]) / (after[0]["time"] - last["time"])
                    start = lerp_point(last["data_points"][0], after[0]["data_points"][0], t)
                first = dict(last)
                first["time"] = 0
                first["uuid"] = str(uuid.uuid5(uuid.NAMESPACE_OID, last["uuid"] + "/lead"))
                first["data_points"] = [start]
                kept.append(first)
            for key in after:
                moved = dict(key)
                moved["time"] = round(key["time"] - LEAD, 4)
                kept.append(moved)
        animator["keyframes"] = kept
    clip["length"] = round(clip["length"] - LEAD, 4)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    for rank in RANKS:
        name = "surge_flame_%s.bbmodel" % rank
        with open(os.path.join(argv[1], name), encoding="utf-8") as handle:
            model = json.load(handle)
        retime(model)
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as out:
            json.dump(model, out, indent=2)
        print(name, model["animations"][0]["length"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
