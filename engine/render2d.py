#!/usr/bin/env python3
"""Sample: replicate the reference promo style with code.
Reference DNA: saturated color chapters, 3D tilting cards, liquid warp
transitions, RGB split, flying text banners, particle streaks, checker outro.
1280x720 @60fps, 13.5s.
"""
import math, os, glob, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1280, 720, 60, 13.5
NFRAMES = int(FPS * DUR)
OUT = os.path.expanduser("~/workspace/video-edit/ref-agent-test/frames_out")
os.makedirs(OUT, exist_ok=True)

# ---------- fonts ----------
fd = os.path.expanduser("~/workspace/bolm-search-worker/cairo-font/static")
def pick(*names):
    for n in names:
        p = os.path.join(fd, n)
        if os.path.exists(p): return p
    g = glob.glob(fd + "/Cairo-*.ttf"); return g[0]
F_XBOLD = pick("Cairo-ExtraBold.ttf", "Cairo-Bold.ttf", "Cairo-SemiBold.ttf")
F_SEMI  = pick("Cairo-SemiBold.ttf", "Cairo-Medium.ttf")
def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)

def text_size(dr, s, f):
    b = dr.textbbox((0, 0), s, font=f, direction="rtl", language="ar")
    return b[2] - b[0], b[3] - b[1], b

# ---------- easing ----------
def clamp01(x): return max(0.0, min(1.0, x))
def ease_out_cubic(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_inout_cubic(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - ((-2 * x + 2) ** 3) / 2
def ease_out_back(x, s=1.9):
    x = clamp01(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def ease_out_expo(x): x = clamp01(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)

# ---------- helpers ----------
def vgrad(w, h, top, bot):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top = np.array(top, dtype=np.float32)[None, None, :]
    bot = np.array(bot, dtype=np.float32)[None, None, :]
    arr = (top * (1 - t) + bot * t).astype(np.uint8)
    return Image.fromarray(np.repeat(arr, w, axis=1), "RGB")

def vignette(img, strength=0.45):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (x - W / 2) / (W / 2); dy = (y - H / 2) / (H / 2)
    d = np.clip(dx * dx + dy * dy, 0, 1.6)
    m = (1 - strength * d * 0.55).astype(np.float32)
    arr = np.asarray(img).astype(np.float32) * m[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

def find_coeffs(target, source):
    # PIL PERSPECTIVE maps output->input: build rows from TARGET points,
    # solve for SOURCE points.
    matrix = []
    for p1, p2 in zip(target, source):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array(source, dtype=np.float64).reshape(8)
    return np.linalg.solve(A, B)

def project_corners(w, h, yaw, pitch, scale, focal=950.0):
    """3D rotate a centered card, return its 4 corners in output space."""
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    out = []
    for x, y in pts:
        x1 = x * cy; z1 = -x * sy
        y2 = y * cp - z1 * sp; z2 = y * sp + z1 * cp
        f = focal / (focal + z2)
        out.append((x1 * f * scale, y2 * f * scale))
    return out

def paste_3d(base, card, cx, cy, yaw, pitch, scale):
    w, h = card.size
    corners = project_corners(w, h, yaw, pitch, scale)
    tgt = [(cx + x, cy + y) for x, y in corners]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    coeffs = find_coeffs(tgt, src)
    warped = card.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    base.alpha_composite(warped)
    return base

def rgb_split(img, dx):
    if dx == 0: return img
    arr = np.asarray(img).copy()
    r = arr[:, :, 0]; b = arr[:, :, 2]
    arr[:, :, 0] = np.roll(r, dx, axis=1)
    arr[:, :, 2] = np.roll(b, -dx, axis=1)
    return Image.fromarray(arr, img.mode)

def rounded_chip(text, fnt, pad_x=34, pad_y=16, bg=(10, 10, 14, 235),
                 fg=(255, 255, 255, 255), radius=18, border=None):
    tmp = Image.new("RGBA", (8, 8)); dr = ImageDraw.Draw(tmp)
    tw, th, b = text_size(dr, text, fnt)
    w, h = tw + pad_x * 2, th + pad_y * 2
    chip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(chip)
    dr.rounded_rectangle([1, 1, w - 2, h - 2], radius=radius, fill=bg,
                         outline=border, width=3 if border else 1)
    dr.text((pad_x - b[0], pad_y - b[1]), text, font=fnt, fill=fg,
            direction="rtl", language="ar")
    return chip

def paste_rot(base, layer, cx, cy, angle_deg, alpha=1.0):
    if alpha <= 0: return
    l = layer if alpha >= 1 else layer.copy()
    if alpha < 1:
        a = l.split()[3].point(lambda v: int(v * alpha)); l.putalpha(a)
    r = l.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(r, (int(cx - r.width / 2), int(cy - r.height / 2)))

# ---------- chapter backgrounds ----------
def bg_green():
    im = vignette(vgrad(W, H, (38, 106, 24), (16, 54, 10)))
    dr = ImageDraw.Draw(im, "RGBA")
    rng = np.random.default_rng(7)
    for _ in range(260):  # texture speckle
        x, y = rng.integers(0, W), rng.integers(0, H)
        dr.point((x, y), fill=(255, 255, 255, 14))
    return im.convert("RGBA")

def bg_blue():
    im = vignette(vgrad(W, H, (8, 16, 84), (3, 5, 32)))
    dr = ImageDraw.Draw(im, "RGBA")
    rng = np.random.default_rng(11)
    for _ in range(120):
        x, y = rng.integers(0, W), rng.integers(0, H)
        dr.ellipse([x, y, x + 2, y + 2], fill=(160, 200, 255, 60))
    return im.convert("RGBA")

def bg_red():
    return vignette(vgrad(W, H, (66, 2, 12), (24, 0, 5))).convert("RGBA")

def bg_purple():
    return vignette(vgrad(W, H, (34, 2, 62), (12, 0, 26))).convert("RGBA")

def bg_teal_outro():
    # perspective checkerboard floor + teal wall
    im = vgrad(W, H, (10, 44, 48), (6, 22, 26))
    chk = Image.new("RGB", (1024, 512))
    d = ImageDraw.Draw(chk)
    s = 64
    for yy in range(8):
        for xx in range(16):
            c = (16, 92, 96) if (xx + yy) % 2 == 0 else (8, 40, 46)
            d.rectangle([xx * s, yy * s, (xx + 1) * s, (yy + 1) * s], fill=c)
    src = [(0, 0), (1024, 0), (1024, 512), (0, 512)]
    tgt = [(-300, 400), (1580, 400), (980, 720), (300, 720)]
    coeffs = find_coeffs(tgt, src)
    floor = chk.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    im.paste(floor, (0, 0), floor.convert("L").point(lambda v: 255 if v > 0 else 0))
    # blend floor softly
    base = vgrad(W, H, (10, 44, 48), (6, 22, 26))
    base.paste(floor, (0, 0))
    return vignette(base, 0.35).convert("RGBA")

BGS = {"green": bg_green(), "blue": bg_blue(), "red": bg_red(),
       "purple": bg_purple(), "teal": bg_teal_outro()}
print("backgrounds ready", flush=True)

# ---------- card / object builders ----------
def scene_card():
    """flat mini landscape scene, 760x470"""
    w, h = 760, 470
    im = vgrad(w, h, (120, 200, 235), (240, 220, 160)).convert("RGBA")
    dr = ImageDraw.Draw(im, "RGBA")
    dr.ellipse([560, 40, 660, 140], fill=(255, 214, 90, 255))          # sun
    dr.polygon([(0, 300), (200, 150), (420, 300)], fill=(70, 120, 90, 255))
    dr.polygon([(260, 300), (520, 120), (760, 300)], fill=(50, 95, 75, 255))
    dr.rectangle([0, 300, w, h], fill=(86, 150, 80, 255))               # ground
    dr.ellipse([330, 185, 430, 285], fill=(0, 0, 0, 70))                # shadow
    dr.ellipse([322, 175, 438, 291], outline=(255, 255, 255, 255), width=10)
    dr.polygon([(362, 205), (362, 262), (412, 233)], fill=(255, 255, 255, 255))
    dr.rounded_rectangle([6, 6, w - 6, h - 6], radius=26, outline=(255, 255, 255, 255), width=6)
    return im

def ai_icon(size=300):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g = vgrad(size, size, (64, 110, 255), (140, 60, 235)).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([4, 4, size - 4, size - 4], radius=64, fill=255)
    im.paste(g, (0, 0), mask)
    dr = ImageDraw.Draw(im)
    f = font(F_XBOLD, 128)
    tw, th, b = text_size(dr, "AI", f)
    dr.text(((size - tw) / 2 - b[0], (size - th) / 2 - b[1]), "AI", font=f,
            fill=(255, 255, 255, 255))
    return im

def video_card():
    w, h = 720, 440
    im = vgrad(w, h, (24, 24, 34), (10, 10, 16)).convert("RGBA")
    dr = ImageDraw.Draw(im, "RGBA")
    dr.rounded_rectangle([4, 4, w - 4, h - 4], radius=24, outline=(255, 255, 255, 200), width=4)
    grd = vgrad(w - 80, h - 150, (90, 60, 160), (30, 90, 140)).convert("RGBA")
    im.alpha_composite(grd, (40, 40))
    dr = ImageDraw.Draw(im, "RGBA")
    dr.ellipse([310, 120, 410, 220], fill=(255, 255, 255, 235))
    dr.polygon([(348, 142), (348, 198), (388, 170)], fill=(20, 20, 30, 255))
    dr.rounded_rectangle([40, h - 78, w - 40, h - 62], radius=8, fill=(255, 255, 255, 60))
    dr.rounded_rectangle([40, h - 78, 300, h - 62], radius=8, fill=(255, 90, 90, 255))
    return im

def plain_card(w, h, c1, c2, glyph=None):
    im = vgrad(w, h, c1, c2).convert("RGBA")
    dr = ImageDraw.Draw(im, "RGBA")
    dr.rounded_rectangle([3, 3, w - 3, h - 3], radius=18, outline=(255, 255, 255, 170), width=3)
    if glyph:
        f = font(F_XBOLD, 90)
        tw, th, b = text_size(dr, glyph, f)
        dr.text(((w - tw) / 2 - b[0], (h - th) / 2 - b[1]), glyph, font=f,
                fill=(255, 255, 255, 235), direction="rtl", language="ar")
    return im

SCENE = scene_card(); ICON = ai_icon(); VCARD = video_card()
FLY1 = plain_card(300, 200, (70, 130, 255), (40, 70, 180), "قص")
FLY2 = plain_card(300, 200, (255, 170, 60), (200, 90, 30), "لون")
FLY3 = plain_card(300, 200, (90, 220, 170), (30, 140, 100), "حركة")

F_BIG = font(F_XBOLD, 64); F_MED = font(F_XBOLD, 44); F_SMALL = font(F_SEMI, 34)
CHIP_TOP = {}
def banner(text, fnt=F_BIG, **kw):
    if text not in CHIP_TOP: CHIP_TOP[text] = rounded_chip(text, fnt, **kw)
    return CHIP_TOP[text]

# ---------- warp transition ----------
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_cx, _cy = _xx - W / 2, _yy - H / 2
_r = np.sqrt(_cx ** 2 + _cy ** 2)
_rn = _r / (W * 0.62)
def warp_frame(img, amp):
    if amp <= 0.001: return img
    ph = _rn * 9.0 - amp * 5.0
    off = np.sin(ph) * amp * 26.0 * np.exp(-_rn * 1.4)
    ux = (_cx / (_r + 1e-5)) * off; uy = (_cy / (_r + 1e-5)) * off
    mx = np.clip(_xx - ux, 0, W - 1).astype(np.int32)
    my = np.clip(_yy - uy, 0, H - 1).astype(np.int32)
    arr = np.asarray(img.convert("RGB"))
    out = arr[my, mx]
    res = Image.fromarray(out, "RGB")
    return rgb_split(res.convert("RGBA"), int(amp * 14))

# ---------- chapters ----------
def ch_green(t):
    im = BGS["green"].copy()
    p = ease_inout_cubic((t - 0.15) / 1.5)
    scale = 1.42 - 0.78 * p                      # pull back 1.42 -> 0.64
    yaw = -0.32 * p; pitch = 0.14 * p
    paste_3d(im, SCENE, W / 2, H / 2 + 10, yaw, pitch, scale)
    a = ease_out_back((t - 0.95) / 0.55)
    if a > 0:
        x = -500 + (W / 2 + 120) * a
        paste_rot(im, banner("تحليل فريم بفريم"), x, 84, -2.5, clamp01((t - 0.95) / 0.3))
    a2 = ease_out_back((t - 1.25) / 0.55)
    if a2 > 0:
        x = W + 500 - (W / 2 + 330) * a2
        paste_rot(im, banner("الخطوة الأولى", F_MED, bg=(90, 30, 10, 235)), x, H - 78, 2.0,
                  clamp01((t - 1.25) / 0.3))
    return im

def ch_blue(t):
    im = BGS["blue"].copy()
    # orbiting mini cards
    for i, (card, rad, sp, ph) in enumerate([
            (FLY1, 330, 0.9, 0.0), (FLY2, 390, -0.7, 2.2), (FLY3, 300, 1.15, 4.1)]):
        ang = ph + t * sp
        x = W / 2 + math.cos(ang) * rad; y = H / 2 + math.sin(ang) * rad * 0.42
        s = 0.42 + 0.1 * math.sin(ang)
        paste_3d(im, card, x, y, math.sin(ang) * 0.7, 0.15, s)
    s = ease_out_back(t / 0.6, s=2.4)
    glow = ICON.resize((int(300 * 1.5), int(300 * 1.5))).filter(ImageFilter.GaussianBlur(28))
    paste_rot(im, glow, W / 2, H / 2 - 10, 0, 0.55)
    icon = ICON.resize((300, 300)).rotate(math.sin(t * 1.4) * 5, resample=Image.BICUBIC, expand=True)
    sc = max(0.01, s)
    icon = icon.resize((int(300 * sc), int(300 * sc)))
    im.alpha_composite(icon, (int(W / 2 - icon.width / 2), int(H / 2 - 10 - icon.height / 2)))
    a = ease_out_back((t - 0.7) / 0.5)
    if a > 0:
        y = -90 + (96 + 90) * a
        paste_rot(im, banner("استخراج الأرقام"), W / 2, y, 1.5, clamp01((t - 0.7) / 0.3))
    return im

def ch_red(t):
    im = BGS["red"].copy()
    dr = ImageDraw.Draw(im, "RGBA")
    for i in range(3):  # orbit rings
        r = 250 + i * 46 + math.sin(t * 2 + i) * 6
        dr.ellipse([W / 2 - r, H / 2 - r * 0.62, W / 2 + r, H / 2 + r * 0.62],
                   outline=(255, 90, 90, 60), width=3)
    beat = math.exp(-((t * 2) % 1.0) * 6)         # pulse at 120bpm
    scale = 0.92 + 0.05 * beat
    card = rgb_split(VCARD, int(3 + 7 * abs(math.sin(t * 3.1))))
    paste_3d(im, card, W / 2, H / 2, math.sin(t * 1.7) * 0.16, 0.08, scale)
    a = ease_out_back((t - 0.5) / 0.5)
    if a > 0:
        x = W + 480 - (W / 2 + 480 - W / 2) * a
        paste_rot(im, banner("إعادة البناء بالكود"), W / 2 + (1 - a) * 500, 82, -1.5,
                  clamp01((t - 0.5) / 0.3))
    return im

_rng_p = np.random.default_rng(42)
STREAKS = [(int(_rng_p.integers(0, W)), float(_rng_p.uniform(140, 420)),
            float(_rng_p.uniform(0, H)), int(_rng_p.integers(26, 90))) for _ in range(70)]
def ch_purple(t):
    im = BGS["purple"].copy()
    dr = ImageDraw.Draw(im, "RGBA")
    for x, sp, off, ln in STREAKS:
        y = (off + t * sp) % (H + 120) - 60
        dr.line([x, y, x, y + ln], fill=(190, 140, 255, 90), width=2)
    flyers = [(FLY1, 0.0, -260, 0.9), (FLY2, 0.55, 300, -1.1), (FLY3, 1.1, 0, 1.4)]
    for card, delay, xoff, rot in flyers:
        lt = t - delay
        if lt < 0: continue
        p = clamp01(lt / 1.5)
        scale = 0.12 + 1.5 * (p ** 2)
        y = H / 2 + (1 - p) * 130 - 40
        x = W / 2 + xoff * (1 - p * 0.4)
        alpha = 1.0 if p < 0.85 else 1 - (p - 0.85) / 0.15
        c = card if alpha >= 1 else card.copy()
        if alpha < 1:
            a = c.split()[3].point(lambda v: int(v * alpha)); c.putalpha(a)
        paste_3d(im, c, x, y, rot * p * 1.6, 0.3 * p, scale)
    a = ease_out_back((t - 0.4) / 0.5)
    if a > 0:
        paste_rot(im, banner("تطبيق الأسلوب"), W / 2, -70 + (84 + 70) * a, 2.0,
                  clamp01((t - 0.4) / 0.3))
    return im

def ch_teal(t):
    zoom = 1.0 + 0.05 * ease_inout_cubic(t / 2.3)
    im = BGS["teal"].copy()
    if zoom > 1.0:
        im = im.resize((int(W * zoom), int(H * zoom))).crop(
            ((int(W * zoom) - W) // 2, (int(H * zoom) - H) // 2,
             (int(W * zoom) + W) // 2, (int(H * zoom) + H) // 2))
    a = ease_out_back(t / 0.6)
    card = Image.new("RGBA", (620, 300), (0, 0, 0, 0))
    dr = ImageDraw.Draw(card)
    dr.rounded_rectangle([2, 2, 618, 298], radius=26, fill=(6, 26, 30, 238),
                         outline=(90, 230, 220, 255), width=3)
    f1 = font(F_XBOLD, 74); f2 = font(F_SEMI, 36)
    tw, th, b = text_size(dr, "تقنية المستقبل", f1)
    dr.text(((620 - tw) / 2 - b[0], 58 - b[1]), "تقنية المستقبل", font=f1,
            fill=(255, 255, 255, 255), direction="rtl", language="ar")
    tw, th, b = text_size(dr, "عيّنة مونتاج بالكود", f2)
    dr.text(((620 - tw) / 2 - b[0], 168 - b[1]), "عيّنة مونتاج بالكود", font=f2,
            fill=(140, 240, 235, 255), direction="rtl", language="ar")
    tw, th, b = text_size(dr, "من تحليل مرجع حقيقي، فريم بفريم", font(F_SEMI, 27))
    dr.text(((620 - tw) / 2 - b[0], 224 - b[1]), "من تحليل مرجع حقيقي، فريم بفريم",
            font=font(F_SEMI, 27), fill=(200, 220, 220, 255), direction="rtl", language="ar")
    paste_3d(im, card, 430, 330, -0.1 * a, 0.05, 0.4 + 0.6 * a)
    # QR-ish card
    qr = Image.new("RGBA", (210, 210), (255, 255, 255, 255))
    dq = ImageDraw.Draw(qr)
    rng = np.random.default_rng(3); cell = 15
    for yy in range(14):
        for xx in range(14):
            if rng.random() < 0.42:
                dq.rectangle([xx * cell, yy * cell, (xx + 1) * cell, (yy + 1) * cell],
                             fill=(10, 20, 22, 255))
    for (qx, qy) in [(0, 0), (165, 0), (0, 165)]:
        dq.rectangle([qx, qy, qx + 45, qy + 45], outline=(10, 20, 22, 255), width=7)
    paste_3d(im, qr, 1010, 320, 0.22 * a, 0.06, 0.4 + 0.6 * a)
    if a > 0:
        paste_rot(im, banner("العيّنة 01", F_MED, bg=(6, 40, 44, 235)), 1010, 486, 0,
                  clamp01(t / 0.3))
    return im

CHAPTERS = [  # (start, end, fn)
    (0.0, 2.4, ch_green), (2.8, 5.2, ch_blue), (5.6, 8.0, ch_red),
    (8.35, 10.85, ch_purple), (11.2, 13.5, ch_teal),
]
WARPS = [(2.4, 2.8), (5.2, 5.6), (8.0, 8.35), (10.85, 11.2)]

def render_frame(i):
    t = i / FPS
    for (s, e, fn) in CHAPTERS:
        if s <= t < e:
            return fn(t - s)
    for (s, e) in WARPS:
        if s <= t < e:
            prev = [c for c in CHAPTERS if c[1] <= s][-1]
            nxt = [c for c in CHAPTERS if c[0] >= e][0]
            p = (t - s) / (e - s)
            f1 = prev[2](prev[1] - prev[0] - 0.01)
            f2 = nxt[2](0.01)
            amp = math.sin(p * math.pi)
            base = Image.blend(f1.convert("RGB"), f2.convert("RGB"),
                               ease_inout_cubic(p)).convert("RGBA")
            return warp_frame(base, amp)
    return CHAPTERS[-1][2](2.29)

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else NFRAMES
    for i in range(start, end):
        p = os.path.join(OUT, f"fr_{i:04d}.png")
        if os.path.exists(p): continue
        render_frame(i).convert("RGB").save(p)
        if i % 60 == 0: print(f"frame {i}/{NFRAMES}", flush=True)
    print("RENDER_DONE", flush=True)
