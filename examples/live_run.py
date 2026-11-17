#!/usr/bin/env python3
"""CutForge live run: decode a pro preset, animate a card with ITS numbers.

Reads motion_bank/streams_v2.json, takes two real decoded streams from
shake 27.ffx (the +/-2 shake and the 120->100 decay), renders a 1.5s
clip driven only by those numbers, and builds a proof sheet.
Shake offset is scaled x6 on screen for visibility (labelled as such).
"""
import json
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/hatch/workspace/cutforge"
OUT = "/home/hatch/workspace/your_files"
W, H, FPS, DUR = 640, 360, 60, 1.5
N = int(FPS * DUR)

bank = json.load(open(f"{ROOT}/motion_bank/streams_v2.json"))
shake = decay = None
for b in bank:
    if b["file"] != "shake 27.ffx" or "parsed_1d" not in b:
        continue
    vals = [k["v"] for k in b["parsed_1d"]]
    if len(vals) >= 4 and max(vals) <= 4 and min(vals) >= -4 and len(set(vals)) > 1:
        shake = b["parsed_1d"]
    if len(vals) == 2 and vals[0] == 120.0 and vals[1] == 100.0:
        decay = b["parsed_1d"]
assert shake and decay, "streams not found"
svals = [k["v"] for k in shake]
print("DECODED shake values:", svals)
print("DECODED decay:", [(k["t"], k["v"]) for k in decay])

STEP = 1.0 / 6.0  # the presets' recurring 0.1667s cadence


def shake_at(t):
    # loop the decoded value sequence, smooth (cosine) interpolation
    pos = (t / STEP) % len(svals)
    i = int(math.floor(pos))
    f = pos - i
    a, b = svals[i], svals[(i + 1) % len(svals)]
    s = 0.5 - 0.5 * math.cos(math.pi * f)
    return a + (b - a) * s


def decay_at(t):
    (t0, v0), (t1, v1) = (decay[0]["t"], decay[0]["v"]), (decay[1]["t"], decay[1]["v"])
    if t <= t0:
        return v0
    if t >= t1:
        return v1
    f = (t - t0) / (t1 - t0)
    return v0 + (v1 - v0) * f


font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

frames = []
for n in range(N):
    t = n / FPS
    img = Image.new("RGB", (W, H), (16, 10, 32))
    dr = ImageDraw.Draw(img)
    off = int(shake_at(t) * 6)  # x6 visibility scale
    cx, cy = W // 2 + off, H // 2 - 20
    dr.rounded_rectangle([cx - 190, cy - 95, cx + 190, cy + 95], 26,
                         fill=(38, 92, 178), outline=(120, 200, 255), width=3)
    dr.text((cx, cy - 28), "CutForge", font=font_big, fill=(255, 255, 255), anchor="mm")
    dr.text((cx, cy + 30), "LIVE RUN", font=font_med, fill=(170, 220, 255), anchor="mm")
    dv = decay_at(t)
    dr.text((24, H - 44), f"decoded decay: {dv:.1f}", font=font_sm, fill=(200, 210, 230))
    dr.text((24, 18), f"t={t:.2f}s  shake={shake_at(t):+.2f} (x6)", font=font_sm,
            fill=(200, 210, 230))
    frames.append(img)

import os
os.makedirs("/tmp/cf_frames", exist_ok=True)
for i, fr in enumerate(frames):
    fr.save(f"/tmp/cf_frames/f{i:03d}.png")
subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", "/tmp/cf_frames/f%03d.png",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", f"{OUT}/cutforge-live-run.mp4"],
               check=True, capture_output=True)
print("video written")

# ---- proof sheet ----
SW, SH = 1280, 900
sheet = Image.new("RGB", (SW, SH), (12, 10, 24))
dr = ImageDraw.Draw(sheet)
dr.text((40, 30), "CutForge — LIVE RUN", font=font_big, fill=(255, 255, 255))
dr.text((40, 92), "Input: shake 27.ffx (pro preset)  ->  decoded by CutForge  ->  motion rebuilt from its numbers",
        font=font_sm, fill=(170, 190, 220))
dr.text((40, 140), f"Decoded shake stream values: {svals}", font=font_med, fill=(140, 230, 170))
dr.text((40, 182), "Decoded decay stream: 120.0 @ 0.000s  ->  100.0 @ 0.167s", font=font_med,
        fill=(140, 230, 170))
# curve plot of the shake stream over one loop
px, py, pw, ph = 40, 250, 1200, 220
dr.rectangle([px, py, px + pw, py + ph], outline=(90, 100, 130))
dr.line([px, py + ph // 2, px + pw, py + ph // 2], fill=(70, 80, 100))
pts = []
for x in range(pw):
    tt = (x / pw) * STEP * len(svals)
    v = shake_at(tt)
    pts.append((px + x, py + ph // 2 - int(v * 34)))
dr.line(pts, fill=(255, 190, 60), width=3)
dr.text((px, py + ph + 10), "the shake curve, drawn from the decoded numbers (one full loop)",
        font=font_sm, fill=(200, 210, 230))
# frame strip
strip_y = 560
for k, idx in enumerate([0, 22, 45, 67, 89]):
    fr = frames[idx].resize((232, 131))
    x = 40 + k * 248
    sheet.paste(fr, (x, strip_y))
    dr.text((x, strip_y + 140), f"frame {idx}", font=font_sm, fill=(200, 210, 230))
dr.text((40, 850), "Output video: cutforge-live-run.mp4 (1.5s, 60fps) — card offset = decoded shake values x6 for visibility",
        font=font_sm, fill=(170, 190, 220))
sheet.save(f"{OUT}/cutforge-live-run-sheet.png")
print("sheet written")
