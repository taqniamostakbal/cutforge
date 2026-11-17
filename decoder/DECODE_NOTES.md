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

## Keyframes — FOUND in `ldat` (2026-11-17)

`tdb4` turned out to be a fixed 124B stream-defaults record (sequence
`[0.0001, 1, 1, 1, 1, 0…]` everywhere), not keyframes. The real
keyframe data lives in **`ldat`** chunks, each preceded by an
**`lhd3`** header (52B):

- `lhd3` int32 fields: `[2]` = keyframe count, `[3]` = stream kind,
  `[4]` = record size in bytes, `[7]` = 4 × `[3]`.
  Verified: count × record size == `ldat` size, every time.
- `ldat` = count records of float64 (big-endian).
- 1-D record = 48B = 6 doubles. Working layout, cross-checked on
  dozens of streams in all 7 presets on disk:
  - `[0]` always 0.0 (reserved)
  - `[1]` **the value** (120→100 blur decay; 41→33; 104→381.6;
    Position X 961→429 — 961 ≈ centre of a 1920 frame)
  - `[5]` **the keyframe time in seconds** (0.0 → 0.1667 progressions)
  - `[2]`, `[4]` tangent value-offsets (can be huge: ±1207, −2848)
  - `[3]` tangent time-offset (0.1667 / 0.3333 / 0.5 / 1.0)
- Multi-dim records: 104B (13 doubles, kind 3), 128B (16 doubles,
  kind 2 in shake 25 — carries 960/961 position constants), 64B
  (8 doubles). Their per-dimension interleave is the next micro-step.

## Still open
- Per-dimension interleave inside 104B/128B records.
- Slot semantics at [48] and [56:76] per property type.
- The 8 presets still in Telegram Web cache (glass, toxic, bubble,
  cartoonish, reels, effect.2, Puddle Impact, test) — parked by the
  owner's order 2026-11-17; nothing is lost, they remain in the channel.
