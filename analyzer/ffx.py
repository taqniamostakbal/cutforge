#!/usr/bin/env python3
"""Decode After Effects .ffx preset binaries (RIFX / FaFX containers).

Findings (verified 2026-11-17 on the endlesswave pack, six presets):
- Chunk tree is plain RIFX: LISTs of `tdbs` property streams. Every stream
  carries one `cdat` chunk whose payload is big-endian float64 values:
  the FIRST double (or first two for 2-D points, first four for colors)
  is the parameter's static value; the rest are zero for static props.
  No cdat in these six files carries keyframe tangents.
- `tdmn` chunks are 40-byte ASCII property/effect names, NOT numbers.
- `tdb4` (124 B) is per-property metadata (only 9-10 distinct 16-byte
  heads per file), NOT one record per keyframe.
- `ldat` chunks hold the actual time-series/keyframe data (fractions
  like 1/6, 1/3 and values like 26/33/41/55 appear as BE doubles), but
  their record layout is NOT yet decoded -- see the open item in
  INSTRUCTION.md. Do not claim keyframe exactness until that lands.
- There are NO wiggle expressions in shake 25/27 (strings search):
  the two-sine frequencies in fxlib.shake_dirblur are OUR approximation,
  not numbers from the file. The shake's real driver is BCC
  Directional Blur (+ Tile edges) with the static params decoded here.

Usage: python3 analyzer/ffx.py <file.ffx>...  -> prints JSON to stdout.
"""
import struct
import sys
import json
import re
from collections import OrderedDict


def walk(data, off, end, out):
    while off + 8 <= end:
        cid = data[off:off + 4].decode("latin1")
        size = struct.unpack(">I", data[off + 4:off + 8])[0]
        if size < 0 or off + 8 + size > len(data) + 8:
            return
        body = off + 8
        out.append((cid, off, size, body))
        if cid in ("RIFX", "LIST"):
            walk(data, body + 4, body + size, out)
        off = body + size + (size % 2)


def clean_name(raw):
    """Payloads are either plain null-padded ASCII (tdmn) or
    b'Utf8' + BE uint32 length + name (pdnm/tdsn/fnam)."""
    if raw[:4] == b"Utf8" and len(raw) >= 8:
        n = struct.unpack(">I", raw[4:8])[0]
        if 0 < n <= len(raw) - 8:
            try:
                return raw[8:8 + n].decode("utf-8")
            except UnicodeDecodeError:
                return raw[8:8 + n].decode("latin1", "replace")
    m = re.search(rb"[ -~]{2,}", raw)
    return m.group(0).decode("latin1") if m else raw.decode("latin1", "replace").strip("\x00")


def decode_file(path):
    d = open(path, "rb").read()
    chunks = []
    walk(d, 0, len(d), chunks)
    streams = OrderedDict()
    animated = []
    ldat = []
    tdb4_heads = set()
    for i, (cid, off, size, body) in enumerate(chunks):
        raw = d[body:body + size]
        if cid == "cdat":
            n = size // 8
            vals = struct.unpack(">" + "d" * n, raw[: n * 8]) if n else ()
            # nearest preceding property + effect names
            prop = ""
            effect = ""
            for j in range(i - 1, max(0, i - 8), -1):
                c2, _o2, _s2, b2 = chunks[j]
                name = clean_name(d[b2:b2 + _s2])
                if c2 in ("tdsn", "pdnm") and not prop:
                    prop = name
                if c2 == "tdmn" and not effect:
                    effect = name
                if prop and effect:
                    break
            key = f"{effect} :: {prop}" if effect and prop else (prop or effect or f"cdat@{off}")
            streams[key] = [round(v, 6) for v in vals]
        elif cid == "ldat":
            ldat.append({"offset": off, "size": size})
            # animated property: nearest preceding names (wider window: the
            # stream's tdmn/tdsn sit above the tdb4 + lhd3 pair)
            prop = ""
            effect = ""
            for j in range(i - 1, max(0, i - 12), -1):
                c2, _o2, _s2, b2 = chunks[j]
                name = clean_name(d[b2:b2 + _s2])
                if c2 in ("tdsn", "pdnm") and not prop:
                    prop = name
                if c2 == "tdmn" and not effect:
                    effect = name
                if prop and effect:
                    break
            n = size // 8
            vals = struct.unpack(">" + "d" * n, raw[: n * 8]) if n else ()
            animated.append({
                "effect": effect, "property": prop, "ldat_bytes": size,
                "head_doubles": [round(v, 4) for v in vals[:8]],
            })
        elif cid == "tdb4":
            tdb4_heads.add(raw[:16].hex())
    # keep only the meaningful leading values: first 1-2, or 4 for colors
    params = OrderedDict()
    for key, vals in streams.items():
        if not vals:
            continue
        # 2-D points have exactly 6 doubles with [x, y, 0, 0, 0, 0]
        if len(vals) == 6 and vals[2:] == [0.0] * 4:
            params[key] = vals[:2]
        elif len(vals) >= 5 and all(v == 0.0 for v in vals[1:]):
            params[key] = vals[0]
        else:
            params[key] = vals
    return {
        "file": path.split("/")[-1],
        "bytes": len(d),
        "streams": len(streams),
        "params": params,
        "animated": animated,
        "ldat_chunks": len(ldat),
        "ldat_total_bytes": sum(c["size"] for c in ldat),
        "ldat_sizes": [c["size"] for c in ldat],
        "tdb4_distinct_heads": len(tdb4_heads),
    }


if __name__ == "__main__":
    out = [decode_file(f) for f in sys.argv[1:]]
    print(json.dumps(out, indent=1, ensure_ascii=False))
