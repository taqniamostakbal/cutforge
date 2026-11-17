#!/usr/bin/env python3
"""Motion Bank exporter: every keyframe stream decoded from .ffx files.

Walks RIFX with the simple declared-size walker (never prunes), pairs
each `ldat` with its preceding `lhd3` header, and emits JSON:
  {file, kind, count, record_bytes, records: [[float64...], ...],
   parsed_1d: [{t, v, tan_in_v, tan_t, tan_out_v}] when record == 48B}

1-D layout (verified): [0]=0 reserved, [1]=value, [2]=in-tangent value,
[3]=tangent time, [4]=out-tangent value, [5]=keyframe time (seconds).
Multi-dim records are exported raw; their per-dimension pairing is
documented in DECODE_NOTES.md.

Usage: python3 motion_bank.py <out.json> <file.ffx> [more.ffx ...]
"""
import json
import struct
import sys


def walk_streams(d):
    out = []
    last_hdr = None

    def walk(off, end):
        nonlocal last_hdr
        while off + 8 <= end:
            tag = d[off:off + 4]
            size = struct.unpack(">I", d[off + 4:off + 8])[0]
            if size > end - off - 8:
                return
            if tag == b"lhd3":
                last_hdr = d[off + 8:off + 8 + size]
            elif tag == b"ldat" and last_hdr is not None:
                h = [struct.unpack(">i", last_hdr[k:k + 4])[0]
                     for k in range(0, len(last_hdr) - 3, 4)]
                out.append((h, d[off + 8:off + 8 + size]))
                last_hdr = None
            if tag in (b"LIST", b"RIFX"):
                walk(off + 12, off + 8 + size)
            off += 8 + size + (size & 1)

    walk(0, len(d))
    return out


def main():
    out_path = sys.argv[1]
    bank = []
    for path in sys.argv[2:]:
        d = open(path, "rb").read()
        if d[:4] != b"RIFX":
            continue
        for h, data in walk_streams(d):
            count, kind, recsz = h[2], h[3], h[4]
            if count * recsz != len(data) or recsz % 8:
                continue
            nd = recsz // 8
            recs = [[struct.unpack(">d", data[r * recsz + k * 8:
                        r * recsz + k * 8 + 8])[0] for k in range(nd)]
                    for r in range(count)]
            entry = {"file": path.split("/")[-1], "kind": kind,
                     "count": count, "record_bytes": recsz,
                     "records": [[round(v, 6) for v in r] for r in recs]}
            if recsz == 48:
                entry["parsed_1d"] = [
                    {"t": r[5], "v": r[1], "tan_in_v": r[2],
                     "tan_t": r[3], "tan_out_v": r[4]} for r in recs]
            bank.append(entry)
    with open(out_path, "w") as f:
        json.dump(bank, f, indent=1)
    total_kf = sum(b["count"] for b in bank)
    print(f"{len(bank)} streams, {total_kf} keyframes -> {out_path}")


if __name__ == "__main__":
    main()
