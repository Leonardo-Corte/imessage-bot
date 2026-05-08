"""All-in-one entry point: filter contacts by keywords, preview, confirm, send.

Usage:
    python bot.py nyc
    python bot.py nyc "new york" ny "new york city"
    python bot.py "pasta eater hk" "pasta night hk" --msg "ciao!"
    python bot.py nyc --vcf /path/to/contacts.vcf
    python bot.py nyc --dry-run
    python bot.py nyc --skip-cold       # skip contacts with no past iMessage
    python bot.py nyc -y                 # skip y/N prompt
"""
from __future__ import annotations
import os
import random
import time
from typing import List, Optional

import typer
import yaml
from rich.console import Console

from lib.contacts import load_contacts
from lib.vcard import parse_vcf
from lib.filter import build_pattern, matches
from lib.chatdb import get_messages_with
from lib.imessage import pick_imessage_handle
from lib.messenger import send as imessage_send

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    keywords: List[str] = typer.Argument(..., help="Keywords (matched in name/family/org)"),
    message: str = typer.Option("ciao come stai?", "--msg", "-m", help="Message text"),
    vcf: Optional[str] = typer.Option(None, "--vcf", help="Use .vcf file instead of macOS Contacts"),
    from_id: Optional[str] = typer.Option(None, "--from", help="Sender service id"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip y/N confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only, no send"),
    skip_cold: bool = typer.Option(False, "--skip-cold", help="Skip contacts with no past iMessage"),
    config: str = typer.Option("config.yaml", help="Config file"),
):
    cfg = yaml.safe_load(open(config))
    rl = cfg["rate_limit"]
    db_path = os.path.expanduser(cfg["paths"]["chat_db"])
    phone_region = cfg["defaults"].get("phone_region", "IT")
    sender = from_id or cfg["defaults"].get("from_id") or None

    if vcf:
        console.print(f"[bold]Loading contacts from {vcf}[/bold]")
        contacts = parse_vcf(vcf)
    else:
        console.print("[bold]Loading macOS Contacts[/bold]")
        contacts = load_contacts()
    console.print(f"  {len(contacts)} total")

    pattern = build_pattern(keywords)
    matched = [c for c in contacts if matches(pattern, c.given, c.family, c.org)]
    console.print(f"  {len(matched)} match keywords: {keywords}")

    eligible = []
    skip_no_imessage = 0
    skip_cold_count = 0
    for c in matched:
        handle, _ = pick_imessage_handle(c.phones, c.emails, db_path, phone_region)
        if not handle:
            skip_no_imessage += 1
            continue
        if skip_cold:
            past = get_messages_with(handle, db_path)
            if len(past) < 1:
                skip_cold_count += 1
                continue
        eligible.append((c, handle))

    console.print(f"\n[bold]Eligible:[/bold] {len(eligible)}")
    console.print(f"[bold]Skipped (no iMessage):[/bold] {skip_no_imessage}")
    if skip_cold:
        console.print(f"[bold]Skipped (cold contact):[/bold] {skip_cold_count}")

    if not eligible:
        console.print("[red]Nothing to send.[/red]")
        return

    console.print("\n[bold]Contacts to message:[/bold]")
    for c, h in eligible:
        console.print(f"  - {c.full_name}  ({h})")

    console.print(f"\n[bold]Message:[/bold]  {message!r}")
    console.print(f"[bold]Sender:[/bold]   {sender or 'Mac default account'}")
    console.print(f"[bold]Total:[/bold]    {len(eligible)}")

    if dry_run:
        console.print("\n[yellow]DRY RUN — no messages will be sent[/yellow]")
        return

    if not yes:
        ans = input("\nProceed with send? (y/N): ").strip().lower()
        if ans != "y":
            console.print("[red]Aborted.[/red]")
            return

    sent = 0
    failed = 0
    for c, h in eligible:
        ok = imessage_send(h, message, dry_run=False, from_id=sender)
        if ok:
            sent += 1
            console.print(f"  [OK]   {c.full_name}")
        else:
            failed += 1
            console.print(f"  [FAIL] {c.full_name}")
        delay = random.uniform(rl["delay_min_sec"], rl["delay_max_sec"])
        time.sleep(delay)

    console.print(f"\n[green]Done. Sent: {sent} | Failed: {failed} | Total: {len(eligible)}[/green]")


if __name__ == "__main__":
    app()
