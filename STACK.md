# CutForge stack — vetted 2026-11-17

Every item below was checked live (repo, license, price) before adoption.
Rule: take the method, never install blind. Licenses verified per item.

## Already in our hands (proven in this project)
| Tool | Role | License | Status |
|---|---|---|---|
| FFmpeg | export/conversion backbone | LGPL/GPL builds | IN USE daily |
| Blender 5.3 | true-3D chapters | GPL | INSTALLED + Cycles proven (~5s/frame) |
| Whisper (Workers AI) | subtitles/transcription | cloud free tier | IN USE (Bolm fix424) |

## Adopted as doctrine / reference
| Item | What we take | License | Note |
|---|---|---|---|
| LottieFiles/motion-design-skill | timing/easing/Disney-12 doctrine for the playbook | MIT | REAL, official, verified on GitHub |
| GSAP | easing canon + timeline thinking | FREE incl. bonus plugins (Webflow, 2025) | claim in the viral post is TRUE |
| Motion (motiondivision) | spring physics reference | MIT | web UI motion, not video |
| Remotion + remotion-dev/skills | code-video architecture reference | Remotion: free for individuals and teams of 3 or fewer; company license beyond that. Skills repo has NO license file: read and learn, do not copy wholesale | owner is solo, so Remotion itself is free for him |
| Anatomy (wheresryan22) | explainer-figure method for the faceless series | MIT | REAL; slow by design; figures, not editing |

## Measured with our own code (the tool's job, our implementation)
| Job | Tool in the post | What we did |
|---|---|---|
| Beat detection | librosa (ISC) | Spectral-flux tracker in numpy. Reference promo measured 2026-11-17: about 172 BPM, beat period 0.348s, 27 onsets in 16.17s. The presets' 0.1667s cadence sits on the same grid (half of 0.3333s). librosa itself can be installed later if heavier analysis is needed. |

## Web-3D shelf (for the Studio UI, when needed)
Three.js (MIT), react-three-rapier (MIT), react-postprocessing,
three.quarks (MIT), Tweakpane (MIT), Lottie-web: all real. They serve
interactive web scenes, not the render pipeline.

## Rejected / corrected claims from the viral post
- "Blender is built into Muse from the start" — FALSE. Blender is a
  separate ~407MB program; we installed it ourselves on this machine.
- "Openverse API: free sound search, no key" — OUTDATED. The anonymous
  call failed in our test on 2026-11-17; in practice a free account
  token is required.
- anatomy-reveal via TypingMind — a third-party marketplace port for a
  different product; the original is wheresryan22/anatomy above. Skip.
- Hairline (lucasmarkes, MIT) — REAL but it is website line-figure
  decoration, not motion/video tooling. Not adopted.
- Manim (MIT) — real and excellent for math/diagram explainers; parked
  until the explainer series needs it.
