# fallback.py — Gemini 2.5 Flash fallback (answer-only)
from __future__ import annotations
import os, re
from typing import Optional

try:
    from llama_index.core import Settings
except Exception:
    Settings = None


def _clean(s: str) -> str:
    """Strip tags/labels and template echoes; return plain answer."""
    if not s:
        return ""
    # Remove XML/HTML-like tags and odd separators
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("▃", " ")
    # Drop common label echoes
    s = re.sub(r"(?i)\b(question|evidence|final answer|answer|output)\s*:\s*", " ", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # If it still looks like instructions, blank it so caller can fallback again
    if re.search(r"(?i)answer in \d|medically accurate sentences|respond without citations|select the answer", s):
        return ""
    return s


class FallbackModel:
    """
    Gemini-only fallback. Fast and simple: relies on Settings.llm configured in app.py.
    """

    def __init__(self):
        provider = os.getenv("FALLBACK_PROVIDER", "gemini").lower()
        model_id = os.getenv("FALLBACK_MODEL_ID", "gemini-2.5-flash")
        if provider != "gemini":
            raise RuntimeError(
                f"FALLBACK_PROVIDER={provider} not supported in this build. "
                "Set FALLBACK_PROVIDER=gemini in your .env"
            )
        if Settings is None or getattr(Settings, "llm", None) is None:
            raise RuntimeError(
                "Gemini Settings.llm is not configured. In app.py set: "
                "Settings.llm = Gemini(model='gemini-2.5-flash', api_key=GOOGLE_API_KEY)"
            )
        self.max_tokens = int(os.getenv("FALLBACK_MAX_TOKENS", "128"))
        self.temperature = float(os.getenv("FALLBACK_TEMPERATURE", "0.2"))
        self.model_id = model_id  # kept for logging if you want

    def generate(self, question: str, role: str = "general") -> str:
        """
        Return a concise, citation-free medical answer in 2–3 sentences (answer-only).
        """
        # Minimal instruction to discourage echo
        prompt = (
            "Answer concisely (2–4 sentences). Use medically sound language. "
            "Do NOT include citations or labels. If uncertain, say so briefly.\n"
            f"Question: {question}\n"
            "Answer:"
        )

        try:
            out = Settings.llm.complete(prompt)
            text = _clean(getattr(out, "text", "") or str(out))
            if not text:
                # Retry once with an even simpler prompt if it echoed instructions
                out2 = Settings.llm.complete(f"{question}\n\nAnswer in 2–4 sentences, no citations:")
                text = _clean(getattr(out2, "text", "") or str(out2))
        except Exception:
            text = ""

        return text or "I'm sorry—I can't provide a reliable medical answer right now."
