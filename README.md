# CutForge

**The open editing agent.** Feed it a reference video — it measures the
style, extracts the recipes, rebuilds the edit with code and true 3D, and
verifies itself frame-by-frame against the original.

> Reference in → style extracted → rebuilt by code → pixel-verified.
> No timeline. No keyframe dragging. The numbers *are* the edit.

## Why this exists

Pro edits look like magic because their parameters are locked inside
binary preset files and paid plugins. CutForge opens them: it reads real
`.ffx` presets down to their effect stacks and embedded expressions,
recovers the actual numbers (e.g. an inertial-bounce expression with
`amp=.02, freq=2.0, decay=6.0`, extracted verbatim and re-implemented
bit-faithfully), and rebuilds every recipe as open code.

## What's inside

| Part | What it does |
|---|---|
| `instruction/INSTRUCTION.md` | The master playbook: measured style DNA of a real promo, extracted recipes, laws, roadmap |
| `analyzer/` | Measures any reference: cuts, dominant colors, motion peaks (ffprobe + frame sampling) |
| `engine/fxlib.py` | The effects library: chroma distortion, directional-blur shake, smooth shake + true bounce expression, glitch, halftone, turbulent shake |
| `engine/render2d.py` | A code-rendered 2.5D promo engine (PIL/numpy, 60 fps) |
| `engine/blender/` | True-3D chapter rebuilds in Blender (Cycles), scripted end-to-end |
| `compare/` | Pixel-diff comparator + contact sheets: the honesty machine |
| `providers/` | One model interface for **any brain**: OpenAI-compatible APIs, Anthropic, or local open models via Ollama/LM Studio |
| `recipes/` | One JSON per extracted recipe: stack, logic, parameters, status |

## Proof, not promises

- A Russian AE promo ("AFTER LIGHT", 1440p60) was dissected to the frame:
  cuts at 2.633/4.5/7.0 s, per-chapter color DNA, transition grammar.
- Its purple fly-through chapter was rebuilt in **Blender true 3D**
  (real geometry, lights, motion blur) from a Python script.
- Six production presets from the same pack were reverse-read and
  re-implemented; the rebuilt effects ship in `engine/fxlib.py` and are
  demoed side-by-side with labels.

## Connect any brain

```bash
export CUTFORGE_PROVIDER=openai        # or anthropic | ollama
export CUTFORGE_MODEL=gpt-4o-mini      # or your local model
export CUTFORGE_API_KEY=...            # not needed for ollama
python3 providers/model.py             # → FORGE ONLINE
```

The brain plans and writes scene code. The forge renders. The comparator
grades. Swap brains freely — the Instruction is the constant.

## Status labels (we grade ourselves)

- `extracted` — their numbers, recovered from the file
- `rebuilt` — our code, same logic and parameters
- `approximated` — our code, similar look, openly labeled

## Roadmap

1. `.ffx` keyframe-float decoder (values + bezier tangents) — numerically
   exact motion.
2. Analyzer → recipe auto-draft: from measured DNA to a starter recipe.
3. Blender chapter templates for every promo archetype.
4. Agent loop: plan → render → compare → correct, until diff ≈ re-encode
   noise.

## License

MIT. Recipes document *technique* (stacks, parameters, math). Original
packs, plugins and reference media are not redistributed.

---

*Forged in the open by Anas Boualem (Exploring Tech) + Rami.*
*مشروع مفتوح المصدر: وكيل مونتاج يستخرج الأسلوب من أي فيديو مرجعي ويعيد بناءه بالكود وثلاثي الأبعاد الحقيقي، مع تحقق فريم بفريم.*
