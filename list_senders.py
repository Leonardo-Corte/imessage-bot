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

cur = conn.execute("PRAGMA table_info(chat)")
cols = {row[1] for row in cur.fetchall()}

select_cols = []
where_clauses = []
group_cols = []
for c in ("account_login", "service_name", "account"):
    if c in cols:
        select_cols.append(c)
        group_cols.append(c)
        if c in ("account_login", "account"):
            where_clauses.append(f"{c} IS NOT NULL")

if not select_cols:
    raise SystemExit("chat table has no account columns. Unsupported macOS schema.")

select_sql = ", ".join(select_cols)
where_sql = " OR ".join(where_clauses) if where_clauses else "1=1"
group_sql = ", ".join(group_cols)

query = f"""
    SELECT {select_sql}, COUNT(*) as n
    FROM chat
    WHERE {where_sql}
    GROUP BY {group_sql}
    ORDER BY n DESC
"""
cur = conn.execute(query)
rows = cur.fetchall()
conn.close()

if not rows:
    print("No iMessage accounts found in chat.db.")
    print("Open Messages.app and ensure you are logged in to iMessage.")
    raise SystemExit(1)

print("Available iMessage sender accounts on this Mac:\n")
for row in rows:
    n = row[-1]
    values = row[:-1]
    for col, val in zip(select_cols, values):
        print(f"  {col}: {val}")
    print(f"  used in {n} chats")
    print()

print("Use 'account_login' (or 'account' if present) value as --from")
print('Example: python smoke_test.py +39TUONUMERO --from "<account_login_value>"')
print("\nSe c'è solo un account: puoi omettere --from, usa Mac default.")
