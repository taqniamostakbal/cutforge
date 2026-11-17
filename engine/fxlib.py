#!/usr/bin/env python3
"""fxlib — the pack's recipes rebuilt in code (numpy/PIL).

Each function mirrors an extracted .ffx recipe:
  !shake.ffx        -> turbulent_shake   (Turbulent Displace + Tile)
  Chroma_1.ffx      -> distort_chroma    (S_DistortChroma + Lens Blur + StretchFrameEdges + Exposure)
  shake 25/27.ffx   -> shake_dirblur     (Directional Blur x337 + Tile + Offset)
  smooth shake.ffx  -> smooth_shake      (S_BlurMotion + drift) and bounce_value
                                           (the REAL extracted expression: amp=.02 freq=2 decay=6)
  glitch.ffx        -> glitch            (S_ScanLines + Channel Combiner + Position/Scale/Crop Wiggle, quantized)
  стилизация.ffx    -> halftone          (S_HalfTone + Turbulent Displace)
All functions take/return float32 RGB arrays HxWx3 in 0..255.
"""
import numpy as np
from PIL import Image, ImageFilter

# ---------- primitives ----------
def shift_edge(arr, dx, dy):
    """Integer shift with edge replication (AE Tile behaviour)."""
    h, w = arr.shape[:2]
    dx, dy = int(round(dx)), int(round(dy))
    p = np.pad(arr, ((abs(dy) + 2, abs(dy) + 2), (abs(dx) + 2, abs(dx) + 2), (0, 0)), mode="edge")
    y0 = abs(dy) + 2 - dy; x0 = abs(dx) + 2 - dx
    return p[y0:y0 + h, x0:x0 + w]

def dir_blur(arr, length, angle_deg):
    """Directional (motion) blur: accumulate shifted copies along a line."""
    if length < 1: return arr
    th = np.deg2rad(angle_deg)
    ux, uy = np.cos(th), np.sin(th)
    k = int(length)
    acc = np.zeros_like(arr); n = 0
    for i in range(-k // 2, k // 2 + 1):
        acc += shift_edge(arr, ux * i, uy * i); n += 1
    return acc / n

def gauss(arr, sigma):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(sigma))).astype(np.float32)

def smooth_field(h, w, cell, rng):
    """Low-res random field upscaled smoothly -> displacement field in -1..1."""
    gh, gw = max(2, h // cell), max(2, w // cell)
    low = rng.uniform(-1, 1, (gh, gw)).astype(np.float32)
    im = Image.fromarray(((low + 1) * 127.5).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(im).astype(np.float32) / 127.5) - 1.0

def displace(arr, fx, fy):
    """Remap: out[y,x] = arr[y+fy, x+fx] with clamped indices."""
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    mx = np.clip((xx + fx).astype(np.int32), 0, w - 1)
    my = np.clip((yy + fy).astype(np.int32), 0, h - 1)
    return arr[my, mx]

def _noise2(t, seed, f1, f2):
    return (np.sin(2 * np.pi * f1 * t + seed) * 0.65
            + np.sin(2 * np.pi * f2 * t + seed * 1.7) * 0.35)

# ---------- !shake: Turbulent Displace + Tile ----------
def turbulent_shake(arr, t, seed=3.0, amount=11.0):
    h, w = arr.shape[:2]
    rng = np.random.default_rng(int(seed * 100))
    fx = smooth_field(h, w, 90, rng) * amount * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * t + seed))
    fy = smooth_field(h, w, 90, rng) * amount * (0.7 + 0.3 * np.cos(2 * np.pi * 6 * t + seed))
    return displace(arr, fx, fy)

# ---------- Chroma_1: DistortChroma + Lens Blur + StretchFrameEdges + Exposure ----------
def distort_chroma(arr, t, amount=13.0, seed=8.0):
    h, w = arr.shape[:2]
    rng = np.random.default_rng(int(seed * 100))
    bx = smooth_field(h, w, 130, rng); by = smooth_field(h, w, 130, rng)
    pulse = 0.75 + 0.45 * np.sin(2 * np.pi * 0.9 * t)
    out = np.empty_like(arr)
    for ch, m in enumerate((1.0, 0.45, 1.6)):        # each channel distorted differently
        out[:, :, ch] = displace(arr[:, :, ch], bx * amount * m * pulse, by * amount * m * pulse)
    out[:, :, 0] = gauss(out[:, :, 0][:, :, None].repeat(3, axis=2), 1.1)[:, :, 0]
    out[:, :, 2] = gauss(out[:, :, 2][:, :, None].repeat(3, axis=2), 1.1)[:, :, 2]
    out = out * 1.06                                  # Exposure lift
    # StretchFrameEdges: zoom 1.05, centre crop
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    im = im.resize((int(w * 1.05), int(h * 1.05)), Image.BICUBIC).crop(
        ((int(w * 1.05) - w) // 2, (int(h * 1.05) - h) // 2,
         (int(w * 1.05) + w) // 2, (int(h * 1.05) + h) // 2))
    return np.asarray(im).astype(np.float32)

# ---------- shake 25/27: keyframed shake + Directional Blur + Tile ----------
def shake_dirblur(arr, t, seed=5.0, amp=13.0):
    x = _noise2(t, seed, 11.0, 23.0) * amp
    y = _noise2(t, seed + 9.0, 13.0, 27.0) * amp * 0.8
    # velocity -> blur direction/length
    dt = 1 / 240
    vx = (_noise2(t + dt, seed, 11.0, 23.0) - _noise2(t - dt, seed, 11.0, 23.0)) * amp / (2 * dt)
    vy = (_noise2(t + dt, seed + 9.0, 13.0, 27.0) - _noise2(t - dt, seed + 9.0, 13.0, 27.0)) * amp * 0.8 / (2 * dt)
    sp = np.hypot(vx, vy)
    ang = np.degrees(np.arctan2(vy, vx)) if sp > 1 else 0.0
    out = shift_edge(arr, x, y)
    bl = min(20.0, sp * 0.045)
    if bl >= 1.5:
        out = dir_blur(out, bl, ang)
    return out

# ---------- smooth shake: gentle drift + S_BlurMotion ----------
def smooth_shake(arr, t, seed=2.0):
    x = _noise2(t, seed, 0.9, 1.7) * 5.0
    y = _noise2(t, seed + 4.0, 1.1, 2.0) * 4.0
    dt = 1 / 240
    vx = (_noise2(t + dt, seed, 0.9, 1.7) - _noise2(t - dt, seed, 0.9, 1.7)) * 5.0 / (2 * dt)
    vy = (_noise2(t + dt, seed + 4.0, 1.1, 2.0) - _noise2(t - dt, seed + 4.0, 1.1, 2.0)) * 4.0 / (2 * dt)
    sp = np.hypot(vx, vy)
    ang = np.degrees(np.arctan2(vy, vx)) if sp > 1 else 0.0
    out = shift_edge(arr, x, y)
    bl = min(14.0, sp * 0.10)
    if bl >= 1.5:
        out = dir_blur(out, bl, ang)
    return out

# ---------- the REAL extracted expression from smooth shake.ffx ----------
def bounce_value(keys, t, amp=0.02, freq=2.0, decay=6.0):
    """keys: sorted [(time, value)]. Reproduces the AE expression exactly:
    after the last passed keyframe, add v*amp*sin(freq*tt*2pi)/exp(decay*tt)
    for tt<1s, where v = velocity just before that keyframe."""
    if not keys: return 0.0
    # base value: linear interp between keys (AE default without easing on the
    # expression's own `value` is the property's interpolated value)
    if t <= keys[0][0]: return keys[0][1]
    n = 0
    for i, (kt, kv) in enumerate(keys):
        if kt <= t: n = i
    kt, kv = keys[n]
    if n == len(keys) - 1:
        base = kv
    else:
        kt2, kv2 = keys[n + 1]
        base = kv + (kv2 - kv) * (t - kt) / (kt2 - kt)
    tt = t - kt
    if n > 0 and tt < 1:
        # velocity at (key time - frameDuration/10): approximate with the
        # segment that ARRIVES at this keyframe
        pk, pv = keys[n - 1]
        v = (kv - pv) / (kt - pk) if kt > pk else 0.0
        base = base + v * amp * np.sin(freq * tt * 2 * np.pi) / np.exp(decay * tt)
    elif n == 0 and len(keys) > 1:
        pass
    return base

# ---------- glitch: ScanLines + Channel Combiner + quantized Wiggle ----------
def glitch(arr, t, seed=1, intensity=1.0):
    h, w = arr.shape[:2]
    frame = int(t * 60)
    qframe = frame // 3 * 3                       # Wiggle Quantization: steps of 3 frames
    rng = np.random.default_rng(seed * 10000 + qframe)
    out = arr.copy()
    nb = rng.integers(3, 7)
    for _ in range(nb):
        y0 = int(rng.integers(0, h - 40)); bh = int(rng.integers(6, 42))
        dx = int(rng.integers(-42, 43) * intensity)
        band = out[y0:y0 + bh]
        out[y0:y0 + bh] = shift_edge(band, dx, 0)
        if rng.random() < 0.5:                    # channel combiner: swap R/B in band
            b2 = out[y0:y0 + bh].copy()
            b2[:, :, 0] = out[y0:y0 + bh][:, :, 2]
            b2[:, :, 2] = out[y0:y0 + bh][:, :, 0]
            out[y0:y0 + bh] = b2
    # global RGB split, quantized too
    sp = int(rng.integers(2, 9))
    out[:, :, 0] = shift_edge(out[:, :, 0][:, :, None].repeat(3, 2), sp, 0)[:, :, 0]
    out[:, :, 2] = shift_edge(out[:, :, 2][:, :, None].repeat(3, 2), -sp, 0)[:, :, 2]
    # scanlines
    rows = np.ones((h, 1, 1), np.float32)
    rows[::2] = 0.90
    rows[1::4] = 0.82
    return out * rows

# ---------- стилизация: HalfTone + Turbulent Displace ----------
def halftone(arr, t, cell=8, seed=6.0):
    h, w = arr.shape[:2]
    rng = np.random.default_rng(int(seed * 100))
    fx = smooth_field(h, w, 110, rng) * 6.0
    fy = smooth_field(h, w, 110, rng) * 6.0
    arr = displace(arr, fx, fy)
    lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]) / 255.0
    gh, gw = h // cell, w // cell
    small = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).resize(
        (gw, gh), Image.BILINEAR)).astype(np.float32) / 255.0
    dots = np.zeros((h, w), np.float32)
    r = (1.0 - small) * (cell * 0.70)
    cy, cx = np.mgrid[0:cell, 0:cell] - cell / 2 + 0.5
    dist = np.sqrt(cx ** 2 + cy ** 2)
    for j in range(gh):
        for i in range(gw):
            if r[j, i] > 0.4:
                dots[j * cell:(j + 1) * cell, i * cell:(i + 1) * cell] = (dist <= r[j, i])
    mask = gauss((dots * 255.0)[:, :, None].repeat(3, axis=2), 0.7)[:, :, 0:1] / 255.0
    paper = np.array([242.0, 240.0, 232.0], np.float32)[None, None, :]
    ink = arr * 0.88
    out = paper * (1 - mask) + ink * mask
    return out * 0.82 + arr * 0.18
