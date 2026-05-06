"""Minimal vCard (.vcf) parser. Returns list[Contact]."""
from __future__ import annotations
from pathlib import Path
from .contacts import Contact


def _unfold(text: str) -> list[str]:
    """vCard line-folding: lines starting with space/tab continue previous line."""
    out = []
    for line in text.splitlines():
        if line.startswith((" ", "\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def _parse_field(line: str) -> tuple[str, dict, str]:
    """Split FIELDNAME;PARAM=val:VALUE into (name, params, value)."""
    if ":" not in line:
        return "", {}, ""
    head, value = line.split(":", 1)
    parts = head.split(";")
    name = parts[0].upper()
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.upper()] = v
        else:
            params[p.upper()] = ""
    return name, params, value


def parse_vcf(path: str | Path) -> list[Contact]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = _unfold(text)

    contacts: list[Contact] = []
    cur: dict | None = None
    idx = 0

    for raw in lines:
        line = raw.rstrip("\r")
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("BEGIN:VCARD"):
            cur = {"given": "", "family": "", "org": "", "phones": [], "emails": [], "fn": ""}
            continue
        if upper.startswith("END:VCARD"):
            if cur is not None:
                given = cur["given"]
                family = cur["family"]
                if not given and not family and cur["fn"]:
                    parts = cur["fn"].split(None, 1)
                    given = parts[0]
                    family = parts[1] if len(parts) > 1 else ""
                contacts.append(Contact(
                    id=f"vcf-{idx}",
                    given=given,
                    family=family,
                    org=cur["org"],
                    phones=cur["phones"],
                    emails=cur["emails"],
                ))
                idx += 1
                cur = None
            continue
        if cur is None:
            continue

        name, _params, value = _parse_field(line)
        if name == "N":
            n_parts = value.split(";")
            cur["family"] = n_parts[0] if len(n_parts) > 0 else ""
            cur["given"] = n_parts[1] if len(n_parts) > 1 else ""
        elif name == "FN":
            cur["fn"] = value
        elif name == "ORG":
            cur["org"] = value.split(";")[0]
        elif name == "TEL":
            v = value.strip()
            if v:
                cur["phones"].append(v)
        elif name == "EMAIL":
            v = value.strip()
            if v:
                cur["emails"].append(v)

    return contacts
