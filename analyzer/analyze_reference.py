#!/usr/bin/env python3
"""Reference analyzer: measure a video's style DNA.

Outputs a JSON report: stream facts (ffprobe), hard-cut timestamps
(mean-abs-diff spikes), per-chapter dominant colors, and motion peaks.
This is the exact workflow that produced the AFTER LIGHT measurements in
instruction/INSTRUCTION.md — automated.

Usage: python3 analyze_reference.py <video> [sample_fps] [out.json]
"""
import json
import subprocess
import sys

import numpy as np
from PIL import Image
import imageio.v3 as iio


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,codec_name",
         "-show_entries", "format=duration", "-of", "json", path],
        capture_output=True, text=True).stdout
    d = json.loads(out)
    s = d["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return {"width": s["width"], "height": s["height"],
            "fps": round(int(num) / int(den), 3), "codec": s["codec_name"],
            "duration": round(float(d["format"]["duration"]), 3)}


def analyze(path, sample_fps=5):
    info = probe(path)
    frames = []
    step = 1.0 / sample_fps
    meta = iio.immeta(path, plugin="pyav") if False else None
    import imageio
    reader = imageio.get_reader(path, fps=sample_fps)
    prev = None
    diffs = []
    colors = []
    for i, fr in enumerate(reader):
        small = np.asarray(Image.fromarray(fr).resize((160, 90))).astype(np.float32)
        gray = small.mean(axis=2)
        if prev is not None:
            diffs.append(float(np.abs(gray - prev).mean()))
        prev = gray
        colors.append(small.reshape(-1, 3).mean(axis=0))
    reader.close()
    diffs = np.array(diffs)
    thr = max(12.0, diffs.mean() + 3 * diffs.std())
    cuts = [round((i + 1) * step, 3) for i, d in enumerate(diffs) if d > thr]
    # chapters between cuts; dominant color per chapter
    bounds = [0.0] + cuts + [info["duration"]]
    chapters = []
    colors = np.array(colors)
    for a, b in zip(bounds[:-1], bounds[1:]):
        ia, ib = int(a * sample_fps), max(int(b * sample_fps), int(a * sample_fps) + 1)
        seg = colors[ia:ib]
        if len(seg):
            mean = seg.mean(axis=0)
            chapters.append({"start": a, "end": b,
                             "dominant_rgb": [round(float(x)) for x in mean],
                             "dominant_hex": "#%02x%02x%02x" % tuple(int(x) for x in mean)})
    return {**info, "sample_fps": sample_fps, "cut_threshold": round(float(thr), 2),
            "cuts": cuts, "chapters": chapters,
            "motion_peak": round(float(diffs.max()), 2) if len(diffs) else 0.0}


if __name__ == "__main__":
    path = sys.argv[1]
    fps = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    report = analyze(path, fps)
    out = sys.argv[3] if len(sys.argv) > 3 else None
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if out:
        open(out, "w").write(text)
    print(text)
