"""Read preview.csv → send via iMessage with rate limit + idempotent log."""
from __future__ import annotations
import csv
import fcntl
import json
import random
import signal
import sys
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.progress import Progress

from lib.messenger import send as imessage_send

app = typer.Typer(add_completion=False)
console = Console()

_stop = False


def _on_sigint(signum, frame):
    global _stop
    _stop = True
    console.print("\n[yellow]Ctrl-C received. Finishing current send then exit.[/yellow]")


signal.signal(signal.SIGINT, _on_sigint)


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_sent_log(path: Path) -> dict:
    if not path.exists():
        return {"entries": []}
    with path.open() as f:
        return json.load(f)


def save_sent_log(path: Path, log: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(log, f, indent=2)
    tmp.replace(path)


def in_business_hours(start: int, end: int) -> bool:
    h = datetime.now().hour
    return start <= h < end


@app.command()
def main(
    config: str = typer.Option("config.yaml"),
    csv_path: Optional[str] = typer.Option(None, "--csv"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    warmup: bool = typer.Option(False, "--warmup", help="Apply first-day cap instead of daily cap"),
    from_id: str = typer.Option("", "--from", help='Sender service id, e.g. "iMessage;-;+39NUMBER"'),
):
    cfg = load_config(config)
    rl = cfg["rate_limit"]
    csv_file = Path(csv_path or cfg["paths"]["preview_csv"])
    log_path = Path(cfg["paths"]["sent_log"])
    sender = from_id or cfg["defaults"].get("from_id", "") or None

    if not csv_file.exists():
        console.print(f"[red]CSV not found: {csv_file}[/red]")
        sys.exit(1)

    lock_path = log_path.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(lock_path, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        console.print(f"[red]Another send.py is running (lock: {lock_path}). Abort.[/red]")
        sys.exit(1)

    rows = list(csv.DictReader(csv_file.open()))
    log = load_sent_log(log_path)
    sent_ids = {e["contact_id"] for e in log["entries"] if not e.get("dry_run")}

    today = date.today().isoformat()
    sent_today = sum(
        1 for e in log["entries"]
        if e.get("sent_at", "").startswith(today) and not e.get("dry_run")
    )
    daily_cap = rl["warmup_first_day_cap"] if warmup else rl["daily_cap"]
    hourly_cap = rl["hourly_cap"]

    eligible = [
        r for r in rows
        if r["has_imessage"] == "true"
        and not r["skip_reason"]
        and r["contact_id"] not in sent_ids
        and r["message"]
    ]

    console.print(f"[bold]Eligible:[/bold] {len(eligible)} | "
                  f"sent today: {sent_today} | daily cap: {daily_cap} | "
                  f"warmup: {warmup} | dry-run: {dry_run}")
    console.print(f"[bold]Sender:[/bold] {sender or 'Mac default (first iMessage account)'}")

    if not eligible:
        console.print("[green]Nothing to send.[/green]")
        return

    console.print("[yellow]Starting in 10 sec. Ctrl-C to abort.[/yellow]")
    for i in range(10, 0, -1):
        if _stop:
            return
        time.sleep(1)

    sent_this_hour = 0
    hour_start = time.time()

    with Progress() as prog:
        task = prog.add_task("send", total=len(eligible))
        for row in eligible:
            if _stop:
                break
            if sent_today >= daily_cap:
                console.print(f"[yellow]Daily cap {daily_cap} hit. Stop.[/yellow]")
                break
            if not in_business_hours(rl["business_hours_start"], rl["business_hours_end"]):
                console.print("[yellow]Outside business hours. Stop.[/yellow]")
                break
            if sent_this_hour >= hourly_cap:
                wait = max(0, 3600 - (time.time() - hour_start))
                console.print(f"[yellow]Hourly cap. Sleep {int(wait)}s.[/yellow]")
                time.sleep(wait)
                sent_this_hour = 0
                hour_start = time.time()

            ok = imessage_send(row["handle"], row["message"], dry_run=dry_run, from_id=sender)
            if ok:
                log["entries"].append({
                    "contact_id": row["contact_id"],
                    "handle": row["handle"],
                    "sent_at": datetime.now().isoformat(timespec="seconds"),
                    "language": row["language"],
                    "from_id": sender or "default",
                    "dry_run": dry_run,
                })
                save_sent_log(log_path, log)
                sent_today += 1
                sent_this_hour += 1
            prog.advance(task)

            if _stop:
                break
            delay = random.uniform(rl["delay_min_sec"], rl["delay_max_sec"])
            time.sleep(delay)

    console.print(f"[green]Done. sent_today={sent_today}[/green]")


if __name__ == "__main__":
    app()
