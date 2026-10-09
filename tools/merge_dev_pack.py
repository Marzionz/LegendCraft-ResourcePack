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

Prints the sha1 to pin in mc-dev server.properties; upload with
  gh release upload dev dist/LegendCraft-Pack-dev.zip --clobber
"""
import glob
import hashlib
import json
import os
import re
import zipfile

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
    entries["pack.mcmeta"] = json.dumps(meta).encode()
    return entries, []


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
