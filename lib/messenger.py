"""AppleScript wrapper for Messages.app send."""
from __future__ import annotations
import subprocess


_SCRIPT_DEFAULT = '''
tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy "{handle}" of targetService
    send "{message}" to targetBuddy
end tell
'''

_SCRIPT_FROM = '''
tell application "Messages"
    set targetService to service id "{from_id}"
    set targetBuddy to buddy "{handle}" of targetService
    send "{message}" to targetBuddy
end tell
'''

_SCRIPT_SMS = '''
tell application "Messages"
    set targetService to 1st service whose service type = SMS
    set targetBuddy to buddy "{handle}" of targetService
    send "{message}" to targetBuddy
end tell
'''


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def send(handle: str, message: str, dry_run: bool = False, timeout: int = 30,
         from_id: str | None = None, service: str = "iMessage") -> bool:
    if service == "SMS":
        script = _SCRIPT_SMS.format(handle=_escape(handle), message=_escape(message))
    elif from_id:
        script = _SCRIPT_FROM.format(
            from_id=_escape(from_id),
            handle=_escape(handle),
            message=_escape(message),
        )
    else:
        script = _SCRIPT_DEFAULT.format(handle=_escape(handle), message=_escape(message))
    if dry_run:
        from_label = from_id or "default"
        print(f"[DRY-RUN] service={service} from={from_label} → {handle}: {message!r}")
        return True
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode != 0:
            print(f"[ERROR] send to {handle} failed: {r.stderr.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"[ERROR] send to {handle} timed out")
        return False
