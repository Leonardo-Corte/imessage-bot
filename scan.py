"""Scan macOS Contacts → filter → preview.csv."""
from __future__ import annotations
import csv
import os
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from lib.contacts import load_contacts
from lib.vcard import parse_vcf
from lib.filter import build_pattern, matches
from lib.chatdb import get_messages_with
from lib.language import detect_language
from lib.name import extract_first_name
from lib.imessage import pick_imessage_handle

app = typer.Typer(add_completion=False)
console = Console()


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


@app.command()
def main(
    config: str = typer.Option("config.yaml", help="Config file"),
    out: Optional[str] = typer.Option(None, help="Output CSV path (overrides config)"),
    vcf: Optional[str] = typer.Option(None, help="Path to .vcf file (skip macOS Contacts)"),
):
    cfg = load_config(config)
    out_path = Path(out or cfg["paths"]["preview_csv"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    db_path = os.path.expanduser(cfg["paths"]["chat_db"])
    pattern = build_pattern(cfg["filter"]["keywords"])
    templates = cfg["templates"]
    default_lang = cfg["defaults"]["language"]
    phone_region = cfg["defaults"].get("phone_region", "IT")
    skip_cold = cfg["safety"]["skip_cold_contacts"]
    min_past = cfg["safety"]["min_past_messages"]

    if vcf:
        console.print(f"[bold]Loading contacts from {vcf}...[/bold]")
        contacts = parse_vcf(vcf)
    else:
        console.print("[bold]Loading macOS Contacts...[/bold]")
        contacts = load_contacts()
    console.print(f"  {len(contacts)} total")

    matched = [c for c in contacts if matches(pattern, c.given, c.family, c.org)]
    console.print(f"  {len(matched)} match NY filter")

    rows = []
    summary = {"sent_eligible": 0, "skip_no_imessage": 0, "skip_cold": 0}

    for c in matched:
        handle, htype = pick_imessage_handle(c.phones, c.emails, db_path, phone_region)
        first = extract_first_name(c.given, c.family)
        skip_reason = ""
        past_count = 0
        lang = default_lang
        message = ""

        if not handle:
            skip_reason = "no_imessage"
            summary["skip_no_imessage"] += 1
        else:
            past = get_messages_with(handle, db_path)
            past_count = len(past)
            lang = detect_language([p.text for p in past], default_lang)
            if skip_cold and past_count < min_past:
                skip_reason = "cold_contact"
                summary["skip_cold"] += 1
            else:
                message = templates[lang].format(first_name=first)
                summary["sent_eligible"] += 1

        rows.append({
            "contact_id": c.id,
            "full_name": c.full_name,
            "first_name": first,
            "handle": handle or "",
            "handle_type": htype,
            "language": lang,
            "has_imessage": "true" if handle else "false",
            "past_msg_count": past_count,
            "message": message,
            "skip_reason": skip_reason,
        })

    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "contact_id","full_name","first_name","handle","handle_type",
            "language","has_imessage","past_msg_count","message","skip_reason"])
        w.writeheader()
        w.writerows(rows)

    table = Table(title="Scan Summary")
    table.add_column("Metric"); table.add_column("Count", justify="right")
    table.add_row("Contacts total", str(len(contacts)))
    table.add_row("Matched NY filter", str(len(matched)))
    table.add_row("Eligible to send", str(summary["sent_eligible"]))
    table.add_row("Skipped: no iMessage", str(summary["skip_no_imessage"]))
    table.add_row("Skipped: cold contact", str(summary["skip_cold"]))
    console.print(table)
    console.print(f"\n[green]Wrote {out_path}[/green]")
    console.print("Review CSV, then run: python send.py")


if __name__ == "__main__":
    app()
