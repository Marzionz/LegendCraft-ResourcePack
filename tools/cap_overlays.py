"""Rewrite a built pack so no shader overlay claims a format above --max-format.

Every other entry is copied byte-for-byte; only pack.mcmeta changes. A client on a newer
format than the cap then skips those overlays and renders with its own vanilla shaders
instead of rejecting the whole pack on a shader compile failure.

  python tools/cap_overlays.py <in.zip> <out.zip> --max-format 96

Prints the out-zip's sha1 for server.properties.
"""
import argparse
import hashlib
import json
import zipfile


def cap(meta, max_format):
    for entry in meta.get("overlays", {}).get("entries", []):
        if entry.get("max_format", 0) > max_format and entry.get("min_format", 0) <= max_format:
            entry["max_format"] = max_format
            formats = entry.get("formats")
            if isinstance(formats, dict):
                formats["max_inclusive"] = max_format
            elif isinstance(formats, list):
                formats[-1] = max_format
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--max-format", type=int, required=True)
    a = ap.parse_args()
    with zipfile.ZipFile(a.src) as zin, zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info)
            if info.filename == "pack.mcmeta":
                data = json.dumps(cap(json.loads(data), a.max_format), indent=2).encode()
            zout.writestr(info, data)
    with open(a.dst, "rb") as f:
        print(hashlib.sha1(f.read()).hexdigest())


if __name__ == "__main__":
    main()
