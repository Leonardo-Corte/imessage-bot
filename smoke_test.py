"""Smoke test: send one iMessage to a target number to verify AppleScript
pattern works on this macOS version. CRITICAL — run before any real send.

Usage:
    python smoke_test.py +393331234567
    python smoke_test.py +393331234567 --from "iMessage;-;+39SENDERNUMBER"

Run list_senders.py first to find the --from id.
"""
import argparse
import sys
from datetime import datetime
from lib.messenger import send

parser = argparse.ArgumentParser()
parser.add_argument("handle", help="recipient phone (E.164) or email")
parser.add_argument("--from", dest="from_id", default=None,
                    help='sender service id, e.g. "iMessage;-;+39NUMBER"')
args = parser.parse_args()

msg = f"iMessage bot smoke test {datetime.now().strftime('%H:%M:%S')}"
print(f"Sending from={args.from_id or 'default'} to {args.handle}: {msg!r}")
ok = send(args.handle, msg, dry_run=False, from_id=args.from_id)
print(f"Result: {'OK (returncode 0)' if ok else 'FAILED'}")
print("\nWAIT 30 sec, then check Messages.app for delivery.")
print("Returncode 0 != delivered. If wrong sender or not received, fix needed.")
