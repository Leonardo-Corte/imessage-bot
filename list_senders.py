"""List iMessage sender accounts on this Mac by reading chat.db.
Use the printed value as --from id in smoke_test.py / send.py.
Requires Full Disk Access for Terminal."""
import os
import sqlite3
from pathlib import Path

db = Path(os.path.expanduser("~/Library/Messages/chat.db"))
if not db.exists():
    raise SystemExit(f"chat.db not found: {db}")

try:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
except sqlite3.OperationalError:
    raise SystemExit("chat.db not readable. Grant Full Disk Access to Terminal.")

cur = conn.execute("""
    SELECT account_login, service_name, account, COUNT(*) as n
    FROM chat
    WHERE account_login IS NOT NULL OR account IS NOT NULL
    GROUP BY account_login, service_name, account
    ORDER BY n DESC
""")
rows = cur.fetchall()
conn.close()

if not rows:
    print("No iMessage accounts found in chat.db.")
    print("Open Messages.app and ensure you are logged in to iMessage.")
    raise SystemExit(1)

print("Available iMessage sender accounts on this Mac:\n")
for login, svc, account, n in rows:
    print(f"  account_login: {login}")
    print(f"  service_name:  {svc}")
    print(f"  account:       {account}")
    print(f"  used in {n} chats")
    print()

print("Use 'account_login' OR 'account' value as --from")
print('Example: python smoke_test.py +39TUONUMERO --from "<account_login_value>"')
print("\nSe c'è solo un account: puoi omettere --from, usa Mac default.")
