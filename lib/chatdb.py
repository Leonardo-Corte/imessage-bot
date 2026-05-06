"""Read-only access to ~/Library/Messages/chat.db."""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from dataclasses import dataclass


@dataclass
class PastMessage:
    text: str
    is_from_me: bool
    date: int


def _open(db_path: str | Path) -> sqlite3.Connection:
    p = Path(os.path.expanduser(str(db_path)))
    if not p.exists():
        raise FileNotFoundError(f"chat.db not found: {p}")
    try:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    except sqlite3.OperationalError as e:
        raise PermissionError(
            "chat.db not readable. Grant Full Disk Access to Terminal in "
            "System Settings → Privacy & Security → Full Disk Access."
        ) from e
    return conn


def get_messages_with(handle_id: str, db_path: str = "~/Library/Messages/chat.db",
                      limit: int = 30) -> list[PastMessage]:
    """Fetch last N text messages exchanged with handle (phone or email).
    Skips messages where text is NULL (modern attributedBody-only entries)."""
    conn = _open(db_path)
    try:
        cur = conn.execute(
            """
            SELECT m.text, m.is_from_me, m.date
            FROM message m
            JOIN handle h ON m.handle_id = h.ROWID
            WHERE h.id = ?
              AND m.text IS NOT NULL
              AND m.text != ''
            ORDER BY m.date DESC
            LIMIT ?
            """,
            (handle_id, limit),
        )
        return [PastMessage(text=r[0], is_from_me=bool(r[1]), date=r[2]) for r in cur]
    finally:
        conn.close()


def has_imessage_handle(handle_id: str,
                        db_path: str = "~/Library/Messages/chat.db") -> bool:
    """True if handle exists in chat.db with iMessage service."""
    conn = _open(db_path)
    try:
        cur = conn.execute(
            "SELECT 1 FROM handle WHERE id = ? AND service = 'iMessage' LIMIT 1",
            (handle_id,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def last_outbound_status(handle_id: str,
                         db_path: str = "~/Library/Messages/chat.db") -> dict | None:
    """Return last outbound message status for handle. Keys:
    error (int, 0 = no error), is_delivered (int), is_sent (int), date (int).
    None if not found."""
    conn = _open(db_path)
    try:
        cur = conn.execute(
            """
            SELECT m.error, m.is_delivered, m.is_sent, m.date, m.is_from_me
            FROM message m
            JOIN handle h ON m.handle_id = h.ROWID
            WHERE h.id = ? AND m.is_from_me = 1
            ORDER BY m.date DESC
            LIMIT 1
            """,
            (handle_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "error": row[0],
            "is_delivered": row[1],
            "is_sent": row[2],
            "date": row[3],
        }
    finally:
        conn.close()
