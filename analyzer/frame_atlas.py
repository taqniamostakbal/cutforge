#!/usr/bin/env python3
"""Frame atlas: EVERY frame of a video, measured.

Per frame (at native fps, frames downscaled to 320x180 for speed):
  rgb      mean color
  lum      mean luminance
  motion   mean |diff| vs previous frame (0..255)
  split    estimated horizontal RGB-split in px: the shift in [-6..6]
           that best aligns the B channel to the R channel (chroma
           aberration signature — peaks mark DistortChroma moments)
  sharp    gradient energy (falls during motion blur / goo transitions)

Output: one JSON per video + chapter segmentation from motion spikes.
Usage: python3 frame_atlas.py <video> <out.json>
"""
import json
import subprocess
import sys

import numpy as np


def probe_fps(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    num, den = out.split("/")
    return int(num) / int(den)


def split_estimate(fr):
    """fr: HxWx3 float32 at 160x90. Best B->R horizontal alignment shift."""
    r = fr[:, :, 0]
    b = fr[:, :, 2]
    h, w = r.shape
    x0, x1 = 20, w - 20
    rc = r[:, x0:x1]
    best_s, best_v = 0, None
    for s in range(-6, 7):
        bs = np.roll(b, s, axis=1)[:, x0:x1]
        v = float(np.abs(rc - bs).mean())
        if best_v is None or v < best_v:
            best_v, best_s = v, s
    return best_s


def atlas(path):
    fps = probe_fps(path)
    W, H = 320, 180
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    frames = []
    prev = None
    fsize = W * H * 3
    while True:
        buf = proc.stdout.read(fsize)
        if len(buf) < fsize:
            break
        small = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3).astype(np.float32)
        gray = small.mean(axis=2)
        motion = 0.0
        if prev is not None:
            motion = float(np.abs(gray - prev).mean())
        prev = gray
        tiny = small[::2, ::2]
        sharp = float(np.abs(np.diff(gray, axis=1)).mean())
        frames.append({
            "rgb": [round(float(x), 1) for x in small.reshape(-1, 3).mean(axis=0)],
            "lum": round(float(gray.mean()), 2),
            "motion": round(motion, 3),
            "split": split_estimate(tiny),
            "sharp": round(sharp, 3),
        })
    proc.wait()
    mot = np.array([f["motion"] for f in frames])
    thr = max(10.0, mot.mean() + 3 * mot.std()) if len(mot) else 10.0
    spikes = [i for i, m in enumerate(mot) if m > thr]
    return {"file": path.split("/")[-1], "fps": round(fps, 3),
            "frames": len(frames), "duration_s": round(len(frames) / fps, 3),
            "motion_threshold": round(float(thr), 2),
            "transition_frames": spikes, "data": frames}


if __name__ == "__main__":
    rep = atlas(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        json.dump(rep, f)
    print(f"{rep['file']}: {rep['frames']} frames @ {rep['fps']}fps, "
          f"{len(rep['transition_frames'])} transition frames")
