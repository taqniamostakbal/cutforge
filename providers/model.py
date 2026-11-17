#!/usr/bin/env python3
"""CutForge model layer — one interface, any brain.

Dialects supported out of the box:
  * openai-compatible  — OpenAI, and most gateways / local servers that
                         speak the same chat-completions dialect
                         (LM Studio, vLLM, text-generation-webui, ...)
  * anthropic          — Claude API
  * ollama             — local open models via Ollama (no key needed)

Config (env only, never hardcode keys):
  CUTFORGE_PROVIDER   openai | anthropic | ollama        (default: openai)
  CUTFORGE_MODEL      model name                          (default: gpt-4o-mini)
  CUTFORGE_BASE_URL   API base (default per provider)
  CUTFORGE_API_KEY    key for hosted providers

The brain's job in CutForge: read instruction/INSTRUCTION.md + a recipe,
then emit scene code (engine/render2d.py style or Blender Python). The
forge renders and the comparator verifies — the brain never grades itself.
"""
import json
import os
import urllib.request

DEFAULTS = {
    "openai":    ("https://api.openai.com/v1", "gpt-4o-mini"),
    "anthropic": ("https://api.anthropic.com/v1", "claude-sonnet-4-5"),
    "ollama":    ("http://localhost:11434/v1", "llama3.1"),
}


def _cfg():
    provider = os.environ.get("CUTFORGE_PROVIDER", "openai").lower()
    base, model = DEFAULTS.get(provider, DEFAULTS["openai"])
    return (provider,
            os.environ.get("CUTFORGE_BASE_URL", base).rstrip("/"),
            os.environ.get("CUTFORGE_MODEL", model),
            os.environ.get("CUTFORGE_API_KEY", ""))


def _post(url, payload, headers):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def chat(messages, temperature=0.4):
    """messages: [{role, content}] -> assistant text."""
    provider, base, model, key = _cfg()
    if provider == "anthropic":
        sys = next((m["content"] for m in messages if m["role"] == "system"), "")
        msgs = [m for m in messages if m["role"] != "system"]
        out = _post(f"{base}/messages",
                    {"model": model, "max_tokens": 8192, "temperature": temperature,
                     "system": sys, "messages": msgs},
                    {"x-api-key": key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in out.get("content", []))
    # openai-compatible (also Ollama / LM Studio)
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    out = _post(f"{base}/chat/completions",
                {"model": model, "temperature": temperature, "messages": messages},
                headers)
    return out["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print(chat([{"role": "user", "content": "Reply with exactly: FORGE ONLINE"}]))
