#!/usr/bin/env python3
"""FFX-RAY v1: structural decoder for After Effects .ffx presets (RIFX).

Parses the RIFF/RIFX chunk tree, then reports per effect:
  - fnam name (Utf8), property names (pdnm), pard record count,
  - keyframe-stream LIST sizes.
And dumps the first pard records under several numeric hypotheses so the
148-byte record layout can be identified.

Usage: python3 ffx_decode.py <file.ffx> [--dump N]
"""
import struct
import sys


def name(b):
    try:
        return b.decode("ascii")
    except Exception:
        return repr(b)


class Chunk:
    def __init__(self, tag, size, off, data):
        self.tag = tag
        self.size = size
        self.off = off
        self.data = data
        self.children = []
        self.form = None

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def find_all(self, tag):
        return [c for c in self.walk() if c.tag == tag]


def parse(buf, off, end):
    out = []
    while off + 8 <= end:
        tag = buf[off:off + 4]
        size = struct.unpack(">I", buf[off + 4:off + 8])[0]
        if size > end - off - 8:
            break
        c = Chunk(tag, size, off, buf[off + 8:off + 8 + size])
        if tag == b"LIST" or tag == b"RIFX":
            c.form = buf[off + 8:off + 12]
            c.children = parse(buf, off + 12, off + 8 + size)
        else:
            # generic container heuristic: children parse cleanly?
            sub = try_parse(buf, off + 8, off + 8 + size)
            if sub is not None:
                c.children = sub
        out.append(c)
        off += 8 + size + (size & 1)
    return out


def try_parse(buf, off, end):
    """Return children only if the whole span parses as clean chunks."""
    out = []
    while off + 8 <= end:
        tag = buf[off:off + 4]
        if not all(32 <= b < 127 or b == 0 for b in tag):
            return None
        size = struct.unpack(">I", buf[off + 4:off + 8])[0]
        if size > end - off - 8:
            return None
        out.append(Chunk(tag, size, off, buf[off + 8:off + 8 + size]))
        off += 8 + size + (size & 1)
    return out if off == end else None


def utf8_of(chunk):
    for c in chunk.walk():
        if c.tag == b"Utf8":
            return c.data.rstrip(b"\x00").decode("utf-8", "replace")
    return None


def main():
    path = sys.argv[1]
    dump_n = 3
    if "--dump" in sys.argv:
        dump_n = int(sys.argv[sys.argv.index("--dump") + 1])
    buf = open(path, "rb").read()
    assert buf[:4] == b"RIFX", "not a RIFX file"
    roots = parse(buf, 0, len(buf))
    root = roots[0]
    print(f"{path.split('/')[-1]}: {len(buf)} bytes, form={name(root.form or b'')}")
    # effects = LIST chunks that contain an fnam
    effects = [c for c in root.walk() if c.tag == b"LIST" and c.find_all(b"fnam")]
    print(f"effects: {len(effects)}")
    for i, fx in enumerate(effects):
        fname = None
        for f in fx.find_all(b"fnam"):
            fname = utf8_of(f)
            if fname:
                break
        pards = fx.find_all(b"pard")
        pdnms = [utf8_of(p) for p in fx.find_all(b"pdnm")]
        streams = [c for c in fx.children if c.tag == b"LIST"]
        print(f"\n[{i}] {fname!r}  pard={len(pards)}  "
              f"properties={len(pdnms)}  child lists={len(streams)}")
        named = [p for p in pdnms if p]
        if named:
            print("    names:", ", ".join(named[:12]))
        for j, pd in enumerate(pards[:dump_n]):
            d = pd.data
            be32 = struct.unpack(">%df" % (len(d) // 4), d[:len(d) // 4 * 4])
            ints = struct.unpack(">%di" % (len(d) // 4), d[:len(d) // 4 * 4])
            print(f"    pard[{j}] ({len(d)}B) int32: {list(ints[:10])}")
            print(f"             float32: {[round(v, 4) for v in be32[:10]]}")


if __name__ == "__main__":
    main()
