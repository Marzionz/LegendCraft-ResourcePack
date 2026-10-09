"""DURABLE, re-runnable (referenced in the repo README): build dist/LegendCraft-Pack-dev.zip,
the pack mc-dev's server.properties points at.

Merges FOUR sources — run AFTER the server has booted with the current models/HUD/armour
config, because the first three are generated at plugin startup:

  1. mc-dev BetterModel  build.zip  (generated model assets)
  2. mc-dev BetterHud    build.zip  (generated HUD assets + versioned shader OVERLAYS)
  3. mc-dev MythicArmors pack.zip   (baked 3D armour + versioned core entity shader OVERLAYS)
  4. our built pack dist/LegendCraft-Pack-<version>.zip (run build.ps1 first)

Later sources win file conflicts (ours last). pack.mcmeta is MERGED, not picked: ours as the
base plus the union of every source's `overlays` entries. Dropping BetterHud's overlays breaks
the HUD: its text shaders live in version-gated overlay directories the client only applies
when pack.mcmeta declares them.

Every range in the merged pack.mcmeta is bounded at TESTED_MAX_FORMAT. The plugin packs declare
overlays reaching formats no one has run them on (MythicArmors' reach 65535), and a client that
applies an overlay whose core shaders it cannot compile rejects the whole pack. A range ending
above the bound is cut to it in both forms; an overlay starting above it is dropped from the
manifest, its files left in place and unread. An overlay whose core shaders still use
`#moj_import` is bounded below MOJ_IMPORT_REJECTED_FORMAT the same way, since a client from that
format up cannot compile them. Each clamp and drop is printed.

Prints the sha1 to pin in mc-dev server.properties; upload with
  gh release upload dev dist/LegendCraft-Pack-dev.zip --clobber
"""
import glob
import hashlib
import json
import os
import re
import zipfile

from check_overlay_shaders import MOJ_IMPORT, core_shaders
from pack_formats import (MOJ_IMPORT_REJECTED_FORMAT, OVERLAY_RANGE_KEY, PACK_RANGE_KEY,
                          TESTED_MAX_FORMAT, declared_ranges, describe, major)

RP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = [
    "C:/Repositories/mc-dev/server/plugins/BetterModel/build.zip",
    "C:/Repositories/mc-dev/server/plugins/BetterHud/build.zip",
    "C:/Repositories/mc-dev/server/plugins/MythicArmors/pack.zip",
]


def newest_our_pack():
    packs = [p for p in glob.glob(os.path.join(RP, "dist", "LegendCraft-Pack-*.zip"))
             if not p.endswith("-dev.zip")]
    if not packs:
        raise SystemExit("no dist/LegendCraft-Pack-<version>.zip — run build.ps1 first")

    def version_key(path):
        m = re.search(r"Pack-([0-9.]+)", os.path.basename(path))
        return [int(x) for x in m.group(1).rstrip(".").split(".")] if m else [0]
    return max(packs, key=version_key)


def clamp_upper(section, range_key, ceiling):
    """Cut every upper bound `section` declares above `ceiling` to it, in both forms."""
    if "max_format" in section and major(section["max_format"]) > ceiling:
        section["max_format"] = ceiling
    value = section.get(range_key)
    if isinstance(value, list) and value and major(value[-1]) > ceiling:
        value[-1] = ceiling
    elif isinstance(value, dict) and value.get("max_inclusive", 0) > ceiling:
        value["max_inclusive"] = ceiling


def bound_formats(meta, ceiling, importing):
    """Bound `meta`'s base range and overlay ranges at `ceiling`, and the overlays named in
    `importing` below MOJ_IMPORT_REJECTED_FORMAT, returning one line per change."""
    report = []
    pack = meta["pack"]
    ranges = declared_ranges(pack, PACK_RANGE_KEY)
    if pack.get("pack_format", 0) > ceiling or any(low[0] > ceiling for low, _ in ranges):
        raise SystemExit("the base pack.mcmeta declares format %s, range %s, above format %d"
                         % (pack.get("pack_format"), describe(ranges), ceiling))
    if any(high[0] > ceiling for _, high in ranges):
        clamp_upper(pack, PACK_RANGE_KEY, ceiling)
        report.append("clamped the base range %s to end at %d" % (describe(ranges), ceiling))

    overlays = meta.get("overlays", {}).get("entries", [])
    kept = []
    for entry in overlays:
        directory = entry.get("directory")
        limit, reason = ceiling, ""
        if directory in importing and ceiling >= MOJ_IMPORT_REJECTED_FORMAT:
            limit = MOJ_IMPORT_REJECTED_FORMAT - 1
            reason = " (its core shaders use #moj_import)"
        ranges = declared_ranges(entry, OVERLAY_RANGE_KEY)
        if any(low[0] > limit for low, _ in ranges):
            report.append("dropped overlay %s: range %s starts above %d%s"
                          % (directory, describe(ranges), limit, reason))
            continue
        if any(high[0] > limit for _, high in ranges):
            clamp_upper(entry, OVERLAY_RANGE_KEY, limit)
            report.append("clamped overlay %s: range %s to end at %d%s"
                          % (directory, describe(ranges), limit, reason))
        kept.append(entry)
    if overlays:
        meta["overlays"]["entries"] = kept
    return report


def merge(source_paths):
    """The merged pack's entries, by zip path, and one report line per change to its pack.mcmeta."""
    entries = {}
    overlay_entries = []
    for path in source_paths:
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if not n.endswith("/"):
                    entries[n] = z.read(n)
            meta = json.loads(z.read("pack.mcmeta"))
        for entry in meta.get("overlays", {}).get("entries", []):
            if entry not in overlay_entries:
                overlay_entries.append(entry)

    meta = json.loads(entries["pack.mcmeta"])  # the last source's: it won the conflict
    if overlay_entries:
        meta["overlays"] = {"entries": overlay_entries}
    importing = {entry.get("directory") for entry in overlay_entries
                 if any(MOJ_IMPORT in entries[name]
                        for name in core_shaders([entry.get("directory")], entries))}
    report = bound_formats(meta, TESTED_MAX_FORMAT, importing)
    entries["pack.mcmeta"] = json.dumps(meta).encode()
    return entries, report


def main():
    sources = SOURCES + [newest_our_pack()]
    entries, report = merge(sources)
    for line in report:
        print(line)

    out_path = os.path.join(RP, "dist", "LegendCraft-Pack-dev.zip")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as out:
        for n in sorted(entries):
            out.writestr(n, entries[n])
    sha1 = hashlib.sha1(open(out_path, "rb").read()).hexdigest()
    open(out_path + ".sha1", "w").write(sha1)
    overlays = json.loads(entries["pack.mcmeta"]).get("overlays", {}).get("entries", [])
    print(f"merged {len(sources)} sources -> {out_path}")
    print(f"entries: {len(entries)}  overlays: {[e['directory'] for e in overlays]}")
    print(f"sha1: {sha1}")


if __name__ == "__main__":
    main()
