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

- `[12:16]` — property name length N (big-endian int32)
- `[16:16+N]` — property name, plain ASCII: `Anchor Point`,
  `Position`, `Scale Height`, `Scale Width`, `Skew`, `Skew Axis`,
  `Rotation`, `Opacity`, `Shutter Angle`, `Sampling`, `Channel:`,
  `Curves`. A record with N=9 and no name is a group terminator.
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

## Still open
- `tdsb` keyframe streams: times, values, bezier tangents.
- Slot semantics at [48] and [56:76] per property type.
- The 8 presets still in Telegram Web cache (glass, toxic, bubble,
  cartoonish, reels, effect.2, Puddle Impact, test) — parked by the
  owner's order 2026-11-17; nothing is lost, they remain in the channel.
