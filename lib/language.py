"""Language detection from past messages."""
from __future__ import annotations


_IT_HINTS = {"ciao", "sono", "come", "stai", "grazie", "prego", "domani",
             "oggi", "bene", "che", "non", "sì", "anche", "però", "perché"}
_EN_HINTS = {"hi", "hey", "the", "how", "you", "thanks", "tomorrow", "today",
             "good", "what", "not", "yes", "also", "but", "because"}


def detect_language(texts: list[str], default: str = "it") -> str:
    """Return 'it' or 'en' based on hint-word frequency. Default if unclear."""
    if not texts:
        return default
    blob = " ".join(t.lower() for t in texts if t)
    tokens = set(blob.split())
    it = len(tokens & _IT_HINTS)
    en = len(tokens & _EN_HINTS)
    if it == 0 and en == 0:
        return default
    if it > en:
        return "it"
    if en > it:
        return "en"
    return default
