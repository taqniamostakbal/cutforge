# CutForge — The Master Instruction

## 0. The destination (owner's order, 2026-11-17, no limits)

Any model plugs in and drives EVERYTHING: analysis, decoded recipes,
Blender, rendering, comparison, correction — and produces the edit the
owner dreams of, from all the absorbed material. The output bar is the
professionals' own edits, measured against the reference itself, never
judged by claims. The road climbs, in order:

1. Rebuild After Effects' semantics from observed behavior.
2. One universal motion representation, lossless across tools.
3. A foundation model trained on real decoded pro motion (the Motion
   Bank — data nobody else has, because nobody decoded the binaries).
4. Mathematical proof of equivalence to the reference, per frame.
5. The holy grail: finished video in → full editable project out.
6. Above all: a forge that learns by itself — every decoded preset
   enters the bank, the rules re-train nightly, improvements publish
   themselves.

Every level is reached through the same door: **decode the numbers.**
Complexity lives in the destination; the steps do not change.

*The permanent brain of the editing agent. Every rule, recipe and number in
this file was extracted from real professional material and verified by
rendering. Nothing here is decoration: if it is written, it was measured.*

---

## 0. The Mission

Take any reference video. Extract its style into numbers. Rebuild that style
with code (2D engine + Blender true 3D) until a pixel-diff comparator can no
longer tell the rebuild from a sibling of the original. Then generalize:
the numbers become recipes, the recipes become a library, the library powers
an agent that edits new videos in that style — connected to **any** brain:
an API model or a local open model. The forge does not care who thinks.

## 1. Laws (never break)

1. **Real only.** Every effect must truly render. No fake UI, no cosmetic
   claims. If a step fails, say so and show the failure frame.
2. **Proof first.** One verified render before any scale-up. Contact sheets
   and measured numbers, not adjectives.
3. **Analysis is measurement.** Cuts, colors, timings and curves come from
   the file (ffprobe, frame sampling, binary inspection), never from vibes.
4. **Honesty about the gap.** Distinguish three states for every recipe:
   `extracted` (their numbers), `rebuilt` (our code, same logic),
   `approximated` (our code, similar look). Never blur the labels.
5. **Presets are binary gold.** `.ffx` files are RIFX containers.
   Decoded 2026-11-17 (`analyzer/ffx.py`, data in
   `examples/analysis/ffx_params.json`): static values live in `cdat`
   chunks as big-endian float64 (first double = value; first two = 2-D
   point; first four = color). Keyframed properties carry NO `cdat` —
   they carry an `ldat` chunk instead (the time-series container; its
   record layout is still open, §3.7). `tdb4` is per-property metadata,
   not one record per keyframe. Effect names and parameter strings are
   readable inside; expressions are stored as plain text. Never claim a
   number is extracted until it appears in `ffx_params.json`.
6. **Copyright hygiene.** Recipes capture *technique* (effect stacks,
   parameters, math). We never redistribute the original packs, plugins or
   project files.

## 2. Reference DNA — "AFTER LIGHT" promo (measured 2026-11-17)

Source: 16.17 s, 2560×1440, 60 fps, H.264 73.8 Mbps.

| Chapter | Time | Dominant color | Content |
|---|---|---|---|
| Scene card | 0.0–1.5 | green `#2b601c` family | anime scene card, pull-back + tilt |
| Goo transition | 1.5–1.75 | green→blue | liquid morph |
| Icon | 1.75–2.633 | blue | glowing "Ae" app icon, orbiting cards |
| Pony | 2.633–4.5 | gold `#6b5420` / `#3e2d06` | character card (Mister Horse) |
| 8-BIT card | 4.5–7.0 | red `#3a000a` | RGB-split title card |
| Fly-through | 7.0–13.3 | purple `#1d0038` / `#120027` | panel assembly, tumbling objects, light streaks |
| Goo transition | ~13.3–13.7 | purple→teal | liquid morph |
| Outro | 13.7–16.17 | teal `#143e42` | checkerboard floor, QR, logo |

Hard cuts at **2.633 s, 4.5 s, 7.0 s**. Style constants: saturated
single-color chapters ≈2.5 s each; everything lives in 3D space; RGB split
on fast elements; overshoot (back-eased) flying banners; particle streaks;
music-driven cutting at 60 fps; checkerboard outro.

### 2.1 Frame atlas — every one of the 970 frames measured

Full-rate pass (`analyzer/frame_atlas.py`, data in
`examples/analysis/atlas_reference.json`). Motion-spike frames
independently confirm the chapter map and add its sub-beats:

| Frame | Time | Event |
|---|---|---|
| 97–98 | 1.63 s | goo transition ignites |
| 158 | 2.63 s | hard cut (icon → pony) |
| 269–274 | 4.48–4.57 s | hard cut (pony → 8-BIT), peak motion 63.2 |
| 420–421 | 7.0 s | hard cut (8-BIT → fly-through), peak 63.8 |
| 510–512 | 8.5 s | fly-through assembly beat, peak 75.9 (the promo's motion maximum) |
| 750 | 12.5 s | last fly-through beat, 46.6 |
| 804–824 | 13.4–13.7 s | goo into the outro |

RGB-split signature: non-zero in **152/970 frames (16%)**, saturating the
±6 px search cap (at 160-px analysis width) in frames 145–151 and 807 —
i.e. chroma distortion is a *transition/fast-element* weapon, not a
constant grade. Rebuilds must pulse it the same way: on at cuts and
impacts, off at rest.

### 2.2 The channel's material videos — also atlased, all frames

The endlesswave channel's own material files are **assets, not
tutorials** (measured, `examples/analysis/atlas_*.json`):

- `endlesswave(2)/(13)/(14).mp4` — 20 s loops at 24 fps with near-zero
  motion (mean ≤0.6) and constant luminance: **static background
  plates**. (13) carries a constant chroma offset baked into the artwork
  itself — split ≠ 0 in all 481 frames with zero motion.
- `steklo.mp4` ("glass") — 8.5 s dark overlay (luminance 0–27), motion
  bursts to 23.8, split active in 76/256 frames: an animated
  glass/refraction element.
- `1.mp4` — a 1.1 s dark micro-flash element.

Doctrine: when a "video" measures as a plate, treat it as a plate —
composite it, don't learn timing from it.

## 3. Extracted recipes (from the endlesswave pack, `.ffx` internals)

Effect stacks read from the RIFX binaries with `strings`; counts are chunk
occurrences, i.e. real usage weight inside the preset.

### 3.1 Chroma_1 — the RGB-split look of the promo
`S_DistortChroma ×98 · ADBE Camera Lens Blur ×47 · ADBE Exposure2 ×47 ·
S_StretchFrameEdges ×24 · ADBE Minimax ×13`
Extracted static values: `S_DistortChroma` Warp Red **0.5**, Warp Blue
**1.0**, Steps **27.9**, Blur Lens **1966**, Wrap X/Y **3**, Amount Rel X/Y
**1.0**; `S_StretchFrameEdges` Center Width **0.4**, Smooth **0.5**;
`ADBE Minimax` Operation **2**, Channel **1**, Direction **1**;
`ADBE Exposure2` Master **0** (no exposure lift — the earlier "+6%"
claim was wrong). Keyframed (ldat, series layout open): DistortChroma
Amount, Exposure, Center Squeeze, Minimax Radius, Lens Blur Radius +
Aspect Ratio. → `engine/fxlib.py: distort_chroma` (`rebuilt`; its
`amount=13` default is OUR scale, not the file's — re-map to Warp
Red 0.5 / Blue 1.0 on the next fxlib pass).

### 3.2 shake 25 / shake 27 — impact shakes
`Directional Blur ×337 · ADBE Tile ×19 · Offset ×16 · Levels · Transform ·
ADBE Geometry2 (27 only)`
Extracted static values (both): BCC Directional Blur Angle **90°** (27)
vs **0°** (25), Maximum Deviation **255**, Thin/Spread/Blur Threshold
**0**, Apply Mix **100**; Tile Center **(0.5, 0.5)**, Tile **100%**,
Output **130%** (27) vs **200%** (25), Mirror Edges **on**. Beat Reactor
wiring is present (Effect on Parameter **2** = Blur Amount, Apply
Strength **100%**, Falloff **0.5 s**, three Samplers at 20–2000 Hz with
corners offset by 0.11) but **disabled** in the saved file (Enable = 0),
so it does NOT drive the shake as saved. Keyframed (ldat): Transform
Position (**936 B** series in 27 — the main motion), Scale, Rotation;
Blur Amount (ldat head 90 in 27, 80 in 25); Iris Scale. CORRECTION:
the "two-sine 11/23 Hz x, 13/27 Hz y, amp 13px" in `fxlib.shake_dirblur`
was NEVER in the file — no wiggle expression exists in either preset.
It is our approximation, kept as a stand-in until the ldat series is
decoded. Status: `rebuilt` (approximation) + static params `extracted`.

### 3.3 smooth shake — floating camera feel
`S_BlurMotion ×105 · ADBE Geometry2 ×41 · Curves`
Extracted static values: `S_BlurMotion` To Z Dist **0.8**, Exposure Bias
**0.5**, Brightness **1.0**, Wrap X/Y **1**; LensBlur Noise Intensity **0**,
Scale **100**, Stretch **0**, Blur **10**, Seed **0**; Iris Shape **5**,
Bokeh Shading **20**, Gamma **220**. Keyframed (ldat): Transform
Position / Scale / Rotation, Curves, S_BlurMotion From Z Dist.
Plus the crown jewel below (§4). → `fxlib.smooth_shake` (`rebuilt`).

### 3.4 glitch
`S_ScanLines ×86 · ADBE Channel Combiner ×19 · ADBE Ripple ×17` + controls
named *Position Wiggle, Scale Wiggle, Crop Wiggle, Wiggle Quantization Steps*.
Extracted static values: `S_ScanLines` Lines Frequency **150**, Sharpness
**1**, Angle **−35°**, Gamma **2**, Saturation **1**, Blur Mask **12**;
Glitchify Amount **20**, Speed **20**; Ripple wave speed **0.2**, height
**20**, center **(1/3, 1/3)** (Russian UI). Keyframed (ldat): Ripple
radius + wave width, Glitchify Completion, Channel Combiner (the
**1584 B** series — the biggest single keyframe block in the pack).
Logic: quantized wiggle (values change in steps, not smoothly), slice
offsets, channel swaps, scanline multiply. → `fxlib.glitch` (`rebuilt`).

### 3.5 стилизация (stylization)
`S_HalfTone ×73 · ADBE Turbulent Displace ×31`
Extracted static values: PEDG Radius **500**, Exposure **0.2**,
Downsample **80**; `S_HalfTone` Dots Frequency **126**. NO animated
properties at all — the only fully static preset of the six, so its
numbers are complete as extracted. Logic: halftone dot screen (dot
radius ∝ darkness) over a gently turbulence-displaced image. →
`fxlib.halftone` (`rebuilt`; two failed mixing formulas are documented
in the lab notes — verify visually, always).

### 3.6 !shake
`ADBE Turbulent Displace ×31 · ADBE Tile ×19 · Motion Blur`
Extracted: Tile 100% / Output 130% (same Tile as shake 27), Mirror Edges
on. Keyframed (ldat): Tile Center, Turbulent Displace Amount / Size /
Evolution, Motion Blur Length (ldat head 55). Logic: animated noise
displacement field, edges tiled. →
`fxlib.turbulent_shake` (`rebuilt`; its "+/-11px, 90px cells, 6–7 Hz"
figures are our approximation, not file numbers).

### 3.7 What the decoder proved (2026-11-17) — and what is still open

Tool: `analyzer/ffx.py` (RIFX walker + `cdat` BE-float64 reader +
`ldat` animated-property inventory). Full tables:
`examples/analysis/ffx_params.json` (105–333 streams per file).

- Static parameters: **decoded, complete** for all six presets.
- Animated properties: **inventoried, complete** (5–6 per file; see §3.1–3.6).
  A property is animated iff its stream has `ldat` instead of `cdat`.
- OPEN: the `ldat` record layout. Each `ldat` holds the keyframe series
  (fractions 1/6, 1/3 and values like 26/33/41/55/80/90 appear as BE
  doubles), but times vs. values vs. bezier tangents are not yet split
  into records. Decoding that layout is the last mile to numerically
  exact motion — do not claim it until a decoded series replays and
  matches the reference frame by frame.
- CORRECTIONS this decode forced: (1) shake frequencies 11/23/13/27 Hz
  were invented — the real shake is keyframed Position/Scale/Rotation;
  (2) Chroma "R×1.0/G×0.45/B×1.6, +6% exposure" was invented — the file
  says Warp Red 0.5 / Blue 1.0, Exposure 0; (3) the "hundreds of
  Directional Blur keyframe points" reading was wrong — ×337 is chunk
  occurrences, and `tdb4` is per-property metadata.

## 4. The extracted expression (verbatim logic, real parameters)

Recovered as plain text from inside `smooth shake.ffx`. This is the classic
inertial-bounce: after each keyframe, the property keeps oscillating with
the velocity it arrived with.

```
amp = .02 · freq = 2.0 · decay = 6.0 · active while t_since_key < 1 s
value + v * amp * sin(freq * t * 2π) / exp(decay * t)
```

Implemented exactly in `fxlib.bounce_value` and verified numerically
(v = −1040 px/s → overshoot −8.0 px at t = 0.15 s, +2.0 px at 0.3 s, 0 at
0.5 s). Status: `extracted` numbers, `rebuilt` code — behavior identical.

## 5. Easing canon (engine defaults)

- `easeOutCubic` — UI settles. `easeOutBack (s=1.3017)` — banner entrances
  (promo overshoot). `easeInOutCubic` — camera moves. `easeOutBounce` —
  playful drops only.
- AE temporal ease = (speed, influence) per keyframe side; when decoding
  `.ffx` binaries, map influence → cubic-bezier handles before comparing.

## 6. The 3D doctrine (Blender)

- After Effects "3D" is 2.5D cards; Blender gives true geometry. For
  fly-through chapters, Blender wins outright.
- Proven pipeline on weak CPUs: build scene in Python → save `.blend` →
  render with the CLI (`blender -b file.blend -E CYCLES`). In-script
  `bpy.ops.render.render()` can abort headless; the CLI path is reliable.
- Cycles CPU ≈ 5 s/frame at 960×540, 16 samples, no denoiser — budget
  renders accordingly; Eevee needs a real GPU/display stack.
- Textured boxes: primitive-cube UVs are an atlas — put textures on child
  planes with full 0..1 UVs, parented to the body. Panels are self-lit
  screens: image → Base Color **and** Emission (strength ≈ 0.6).

## 7. The verification loop (how "exact" is earned)

1. Analyzer measures the reference (cuts, colors, motion peaks).
2. Builder renders the rebuild with the recipe's numbers.
3. Comparator aligns frames and scores pixel difference per chapter.
4. Any chapter above threshold goes back to (2) with corrected numbers.
A chapter ships when its diff is in the noise band of re-encoding the
original itself. Until then it is labeled `approximated`, proudly.

## 8. Model connection (any brain)

`providers/model.py` speaks three dialects through one interface:
OpenAI-compatible APIs (also covers most gateways), Anthropic, and local
open models via Ollama / LM Studio. Config is env-only:
`CUTFORGE_MODEL`, `CUTFORGE_BASE_URL`, `CUTFORGE_API_KEY`. The brain plans
and writes scene code; the forge renders and verifies. Swap brains freely —
the Instruction (this file) is the constant.

## 9. Open veins (known, unsolved, do not fake)

- `.ffx` keyframe series decoding — static params decoded and animated
  properties inventoried (§3.7); the `ldat` record layout (times vs.
  values vs. bezier tangents) is the last mile to numerically exact motion.
- Flow v1.5.0's curve library: its `dialog.js` (1.96 MB) is a bundled shell
  with no curve data; the engine lives in the host scripts — unmined.
- Sapphire/BCC algorithms are proprietary: rebuilds match behavior, not
  bits.
- Render throughput: 1440p60 needs a GPU; CPU renders are proof-grade, not
  production-grade.

## 10. Source map

- Lab (local): `~/workspace/video-edit/ref-agent-test/` — reference, engines,
  renders, proofs. `~/workspace/editing-lab/pack1/` — the harvested pack.
- Origin channel: Telegram `@plugins_endlesswave` ("Плагины endlesswave");
  materials readme points to `@endlesswavee`.
- This repo is the public forge: code + instruction + recipes. Raw packs
  and reference media never enter the repo.
