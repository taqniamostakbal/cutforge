# CutForge — The Master Instruction

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
5. **Presets are binary gold.** `.ffx` files are RIFX containers. Effect
   names and parameter strings are readable inside; expressions are stored
   as plain text; keyframe values are binary floats — decode before claiming
   exactness.
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

## 3. Extracted recipes (from the endlesswave pack, `.ffx` internals)

Effect stacks read from the RIFX binaries with `strings`; counts are chunk
occurrences, i.e. real usage weight inside the preset.

### 3.1 Chroma_1 — the RGB-split look of the promo
`S_DistortChroma ×98 · ADBE Camera Lens Blur ×47 · ADBE Exposure2 ×47 ·
S_StretchFrameEdges ×24 · ADBE Minimax ×13`
Logic: distort each color channel with a *different* warp field, blur the
outer channels like a lens, stretch the frame edges to hide the seams, lift
exposure. → `engine/fxlib.py: distort_chroma` (`rebuilt`).

### 3.2 shake 25 / shake 27 — impact shakes
`Directional Blur ×337 · ADBE Tile ×19 · Offset ×16 · Levels · Transform ·
ADBE Geometry2 (27 only)`
Logic: position shake whose *velocity* drives a directional blur along the
motion vector; Tile replicates edges so the frame never shows void.
→ `fxlib.shake_dirblur` (`rebuilt`).

### 3.3 smooth shake — floating camera feel
`S_BlurMotion ×105 · ADBE Geometry2 ×41 · Curves`
Plus the crown jewel below (§4). → `fxlib.smooth_shake` (`rebuilt`).

### 3.4 glitch
`S_ScanLines ×86 · ADBE Channel Combiner ×19 · ADBE Ripple ×17` + controls
named *Position Wiggle, Scale Wiggle, Crop Wiggle, Wiggle Quantization Steps*.
Logic: quantized wiggle (values change in steps, not smoothly), slice
offsets, channel swaps, scanline multiply. → `fxlib.glitch` (`rebuilt`).

### 3.5 стилизация (stylization)
`S_HalfTone ×73 · ADBE Turbulent Displace ×31`
Logic: halftone dot screen (dot radius ∝ darkness) over a gently
turbulence-displaced image. → `fxlib.halftone` (`rebuilt`; two failed
mixing formulas are documented in the lab notes — verify visually, always).

### 3.6 !shake
`ADBE Turbulent Displace ×31 · ADBE Tile ×19 · Motion Blur`
Logic: animated noise displacement field, edges tiled. →
`fxlib.turbulent_shake` (`rebuilt`).

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

- `.ffx` keyframe float decoding (values + bezier tangents) — the last mile
  to numerically exact motion.
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
