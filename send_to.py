"""Send a single iMessage to specific contacts by name.

Usage:
    python send_to.py "Ciao come stai" Fede Mazza Mamma
    python send_to.py --dry-run "Test" Fede
    python send_to.py --from "iMessage;-;+39NUMBER" "Ciao" Fede

Matches each name against contact given/family/full-name (case-insensitive,
substring). Prints matches found and asks confirmation before sending.
"""
from __future__ import annotations
import argparse
import difflib
import os
import sys
import time
import unicodedata

import yaml
from rich.console import Console
from rich.table import Table

from lib.contacts import load_contacts
from lib.vcard import parse_vcf
from lib.imessage import pick_imessage_handle, normalize_phone
from lib.messenger import send
from lib.chatdb import last_outbound_status

console = Console()

NICKNAMES = {
    "mamma": ["mom", "mum", "madre", "mamy", "mami"],
    "mom": ["mamma", "madre"],
    "papà": ["dad", "papa", "padre", "babbo"],
    "papa": ["dad", "papà", "padre", "babbo"],
    "dad": ["papà", "papa", "padre", "babbo"],
    "fratello": ["bro", "brother"],
    "sorella": ["sis", "sister"],
    "nonna": ["granny", "grandma"],
    "nonno": ["grandpa", "grandad"],
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def _all_strings(c) -> list[str]:
    return [c.given, c.family, f"{c.given} {c.family}".strip(), c.org]


def find_match(contacts, query: str, fuzzy_cutoff: float = 0.7):
    """Return (hits, fuzzy_suggestions). hits = strict substring, suggestions = fuzzy."""
    q = _norm(query)
    queries = {q} | {_norm(n) for n in NICKNAMES.get(q, [])}

    hits = []
    for c in contacts:
        fields = [_norm(s) for s in _all_strings(c) if s]
        if any(qq and qq in f for qq in queries for f in fields):
            hits.append(c)
    if hits:
        return hits, []

    pool = []
    for c in contacts:
        for s in _all_strings(c):
            if s.strip():
                pool.append((_norm(s), c))
    seen = set()
    suggestions = []
    for qq in queries:
        for s, c in pool:
            if not s:
                continue
            ratio = difflib.SequenceMatcher(None, qq, s).ratio()
            if ratio >= fuzzy_cutoff and id(c) not in seen:
                seen.add(id(c))
                suggestions.append((ratio, c))
            else:
                for tok in s.split():
                    if difflib.SequenceMatcher(None, qq, tok).ratio() >= fuzzy_cutoff and id(c) not in seen:
                        seen.add(id(c))
                        suggestions.append((ratio, c))
                        break
    suggestions.sort(key=lambda x: -x[0])
    return [], [c for _, c in suggestions[:8]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message", help="Message text to send")
    ap.add_argument("names", nargs="+", help="Contact names to look up")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--from", dest="from_id", default=None)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--vcf", default=None, help="Path to .vcf file (skip macOS Contacts)")
    ap.add_argument("--yes", action="store_true", help="Skip confirmation")
    ap.add_argument("--force", action="store_true",
                    help="Skip chat.db iMessage check; use first normalized phone/email")
    ap.add_argument("--sms-fallback", action="store_true",
                    help="If iMessage fails, retry as SMS (requires iPhone Text Message Forwarding)")
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    db_path = os.path.expanduser(cfg["paths"]["chat_db"])
    phone_region = cfg["defaults"].get("phone_region", "IT")
    sender = args.from_id or cfg["defaults"].get("from_id") or None

    if args.vcf:
        console.print(f"[bold]Loading contacts from {args.vcf}...[/bold]")
        contacts = parse_vcf(args.vcf)
    else:
        console.print("[bold]Loading contacts from macOS Contacts...[/bold]")
        contacts = load_contacts()
    console.print(f"  {len(contacts)} total")

    resolved = []
    for query in args.names:
        hits, suggestions = find_match(contacts, query)
        if not hits and suggestions:
            console.print(f"[yellow]'{query}': no exact match. Fuzzy suggestions:[/yellow]")
            for i, c in enumerate(suggestions):
                console.print(f"  [{i}] {c.full_name} — phones={c.phones} emails={c.emails}")
            choice = input(f"Pick index for '{query}' (or empty to skip): ").strip()
            if not choice:
                continue
            try:
                c = suggestions[int(choice)]
            except (ValueError, IndexError):
                console.print(f"[red]Invalid choice, skip '{query}'[/red]")
                continue
        elif not hits:
            console.print(f"[red]'{query}': no match[/red]")
            continue
        elif len(hits) > 1:
            console.print(f"[yellow]'{query}': {len(hits)} matches:[/yellow]")
            for i, c in enumerate(hits):
                console.print(f"  [{i}] {c.full_name} — phones={c.phones} emails={c.emails}")
            choice = input(f"Pick index for '{query}' (or empty to skip): ").strip()
            if not choice:
                continue
            try:
                c = hits[int(choice)]
            except (ValueError, IndexError):
                console.print(f"[red]Invalid choice, skip '{query}'[/red]")
                continue
        else:
            c = hits[0]

        handle, htype = None, "none"
        if args.force:
            for raw in c.phones:
                e164 = normalize_phone(raw, phone_region)
                if e164:
                    handle, htype = e164, "phone (forced)"
                    break
            if not handle and c.emails:
                handle, htype = c.emails[0].strip().lower(), "email (forced)"
        else:
            handle, htype = pick_imessage_handle(c.phones, c.emails, db_path, phone_region)
        if not handle:
            console.print(f"[red]'{query}' ({c.full_name}): no iMessage handle (use --force to override)[/red]")
            continue
        if any(r[2] == handle for r in resolved):
            console.print(f"[yellow]'{query}' ({c.full_name}): duplicate of already-resolved handle {handle}, skip[/yellow]")
            continue
        resolved.append((query, c, handle, htype))

    if not resolved:
        console.print("[red]No contacts resolved.[/red]")
        sys.exit(1)

    table = Table(title="Will send")
    table.add_column("Query")
    table.add_column("Contact")
    table.add_column("Handle")
    table.add_column("Type")
    for q, c, h, t in resolved:
        table.add_row(q, c.full_name, h, t)
    console.print(table)
    console.print(f"[bold]Message:[/bold] {args.message!r}")
    console.print(f"[bold]Sender:[/bold] {sender or 'Mac default'}")
    console.print(f"[bold]Dry-run:[/bold] {args.dry_run}")

    if not args.yes and not args.dry_run:
        ans = input(f"\nSend to {len(resolved)} contacts? [y/N]: ").strip().lower()
        if ans != "y":
            console.print("Aborted.")
            sys.exit(0)

    ok_count = 0
    fail_count = 0
    for q, c, h, t in resolved:
        ok = send(h, args.message, dry_run=args.dry_run, from_id=sender)
        if not ok:
            console.print(f"[red]✗ AppleScript error iMessage[/red] {c.full_name} ({h})")
            if args.sms_fallback and not args.dry_run:
                ok2 = send(h, args.message, dry_run=False, service="SMS")
                if ok2:
                    console.print(f"[green]✓ sent as SMS fallback[/green] {c.full_name} ({h})")
                    ok_count += 1
                else:
                    console.print(f"[red]✗ SMS fallback also failed[/red] {c.full_name} ({h})")
                    fail_count += 1
            else:
                fail_count += 1
            time.sleep(2)
            continue

        if args.dry_run:
            console.print(f"[green]✓[/green] {c.full_name} ({h})")
            ok_count += 1
            time.sleep(1)
            continue

        if args.force and not args.sms_fallback:
            console.print(f"[green]✓ sent (forced, no delivery verify)[/green] {c.full_name} ({h})")
            ok_count += 1
            time.sleep(2)
            continue

        time.sleep(5)
        status = last_outbound_status(h, db_path)
        if status is None:
            console.print(f"[yellow]?[/yellow] {c.full_name} ({h}) — no record in chat.db yet")
            ok_count += 1
        elif status["error"] != 0:
            console.print(f"[red]✗ iMessage failed[/red] {c.full_name} ({h}) — error={status['error']}")
            if args.sms_fallback:
                ok2 = send(h, args.message, dry_run=False, service="SMS")
                if ok2:
                    console.print(f"[green]✓ sent as SMS fallback[/green] {c.full_name} ({h})")
                    ok_count += 1
                else:
                    console.print(f"[red]✗ SMS fallback also failed[/red] {c.full_name} ({h})")
                    fail_count += 1
            else:
                fail_count += 1
        elif status["is_delivered"]:
            console.print(f"[green]✓ delivered iMessage[/green] {c.full_name} ({h})")
            ok_count += 1
        elif status["is_sent"]:
            console.print(f"[yellow]✓ sent iMessage (not yet delivered)[/yellow] {c.full_name} ({h})")
            ok_count += 1
        else:
            console.print(f"[yellow]? pending[/yellow] {c.full_name} ({h})")
            ok_count += 1
        time.sleep(2)

    console.print(f"\n[bold]Done: ok={ok_count} fail={fail_count} / total={len(resolved)}[/bold]")


if __name__ == "__main__":
    main()
