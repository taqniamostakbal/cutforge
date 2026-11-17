# FFX-RAY — decode notes

## RIFX container
`.ffx` = big-endian RIFF (`RIFX`), form type `FaFX`. Effects are LIST
chunks containing an `fnam` (name in a `Utf8` chunk). Property streams
are built from `pdnm` (popup/enum label lists), `tdmn` (40B headers),
`pard` records (148B each) and `tdsb` LISTs (the keyframe streams,
~212–832B blocks — not yet decoded).

## pard record (148 bytes) — layout cracked 2026-11-17

Verified against `smooth shake.ffx` (6 effects: BCC Lens Blur OBS ×2,
Curves, Transform ×2, S_BlurMotion):

- `[16:44]` — property name, plain ASCII, null-terminated: `Anchor
  Point`, `Position`, `Scale Height`, `Scale Width`, `Skew`,
  `Skew Axis`, `Rotation`, `Opacity`, `Shutter Angle`, `Sampling`,
  `Channel:`, `Curves`. A record with code 9 and no name is a group
  terminator.
- `[12:16]` — a small code (2, 3, 4, 6, 7, 9, 11, 15 observed). NOT
  the name length (it reads 6 for the 12-char `Anchor Point`) —
  likely a property subtype; semantics still open.
- The first record of each effect is all-zero except shared trailer
  constants at `[84]=225.0`, `[128]=-1`, `[136]=15.0` — a stream
  header, identical across effects.
- **Tail values are big-endian 16.16 fixed point** (int32 / 65536),
  read at offsets 124–147. Confirmations:
  - Opacity → 100, 100, 100, 1 (default 100)
  - Skew / Skew Axis / Rotation → −70, 70, −70, 70, 1 (range ±70)
  - Shutter Angle → 360, 360 (and a trailing 2)
  - Scale Height/Width → …, 30000, −200, 200, **100**, 1 (default 100)
- Mid-record slots `[48]`, `[56:76]` carry per-type flags and, for
  spatial properties, values in the same fixed point (`Anchor Point`
  shows 0.5, 0.5 and 50, 50). Exact slot semantics per property type
  are the next step.

## Keyframe streams — container + encoding cracked 2026-11-17

Each animated property is a `LIST` block (form `tdbs`, ~212–276B)
inside the effect's stream section, containing:

- `tdsb` (4B) — stream marker
- `tdsn` → `Utf8` — the property's display name (e.g. `Compare Mode`)
- **`tdb4` (~124B) — the keyframe data.** Values are **big-endian
  float64**: a static property shows its value as repeated `1.0`
  doubles (`3f f0 00 00 00 00 00 00`). A short header precedes the
  doubles; a flags word (`00 00 00 04 04 …`) follows them.
- `cdat` (40B) — companion data, also led by a float64.

Note: shake presets carry much of their motion in **expressions**
(plain text inside the file — the inertial-bounce expression was
extracted verbatim earlier) plus wiggle controls, not in keyframes.
The decoder must harvest all three sources: static pard values,
tdb4 keyframes, expression text.

## Still open
- Exact per-keyframe field layout inside `tdb4` (time slot, tangent
  slots, flags) — next: diff blocks whose values are known to differ.
- Slot semantics at [48] and [56:76] per property type.
- The 8 presets still in Telegram Web cache (glass, toxic, bubble,
  cartoonish, reels, effect.2, Puddle Impact, test) — parked by the
  owner's order 2026-11-17; nothing is lost, they remain in the channel.
