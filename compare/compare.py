#!/usr/bin/env python3
"""Pixel-diff comparator: score a rebuild against its reference.

For each sampled timestamp: extract the same frame from both videos,
compute mean absolute difference (0..255) and a similarity %, and build a
side-by-side contact sheet. A rebuild "ships" when its mean diff is in the
noise band of re-encoding the original itself (measure that baseline with
--baseline).

Usage:
  python3 compare.py reference.mp4 rebuild.mp4 [times...]
  python3 compare.py reference.mp4 rebuild.mp4 --sheet out.jpg
"""
import subprocess
import sys
import tempfile
import os

import numpy as np
from PIL import Image


def frame_at(video, t, size=(640, 360)):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", video,
                    "-frames:v", "1", "-y", tmp], check=True)
    im = Image.open(tmp).convert("RGB").resize(size)
    os.unlink(tmp)
    return im


def compare(ref, reb, times, sheet=None):
    scores = []
    tiles = []
    for t in times:
        a = frame_at(ref, t)
        b = frame_at(reb, t)
        d = float(np.abs(np.asarray(a).astype(np.float32)
                         - np.asarray(b).astype(np.float32)).mean())
        scores.append((t, d))
        tile = Image.new("RGB", (640, 736), (12, 12, 12))
        tile.paste(a, (0, 0)); tile.paste(b, (0, 376))
        tiles.append(tile)
    if sheet and tiles:
        cols = len(tiles)
        out = Image.new("RGB", (640 * cols, 736), (0, 0, 0))
        for i, tile in enumerate(tiles):
            out.paste(tile, (i * 640, 0))
        out.save(sheet, quality=90)
    return scores


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sheet = None
    if "--sheet" in sys.argv:
        sheet = sys.argv[sys.argv.index("--sheet") + 1]
    ref, reb = args[0], args[1]
    times = [float(x) for x in args[2:]] or [1.0, 3.5, 6.0, 10.0, 15.0]
    res = compare(ref, reb, times, sheet)
    for t, d in res:
        print(f"t={t:>5}s  mean|diff|={d:6.2f}  similarity={100 * (1 - d / 255):5.1f}%")
    mean = sum(d for _, d in res) / len(res)
    print(f"MEAN diff = {mean:.2f}  (0 = identical)")
