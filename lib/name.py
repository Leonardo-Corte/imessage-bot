"""First-name extraction stripping NY-style tags."""
import re

_TAG_PATTERN = re.compile(r"\b(?:NYC|NY|New|York|City|Newyork)\b", re.IGNORECASE)


def extract_first_name(given: str, family: str = "") -> str:
    """Strip NY tags from given+family, return first remaining token.
    Fallback to given, then family, then 'amico'."""
    raw = f"{given} {family}".strip()
    cleaned = _TAG_PATTERN.sub(" ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned:
        return cleaned.split()[0]
    if given.strip():
        return given.strip().split()[0]
    if family.strip():
        return family.strip().split()[0]
    return "amico"
