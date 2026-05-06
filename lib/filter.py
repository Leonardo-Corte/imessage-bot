"""Whole-word keyword filter."""
import re


def build_pattern(keywords: list[str]) -> re.Pattern:
    parts = sorted({re.escape(k) for k in keywords}, key=len, reverse=True)
    return re.compile(rf"\b(?:{'|'.join(parts)})\b", re.IGNORECASE)


def matches(pattern: re.Pattern, *fields: str) -> bool:
    haystack = " ".join(f for f in fields if f)
    return bool(pattern.search(haystack))
