"""Background reminder scheduler — set, list, cancel reminders."""

import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import REMINDERS_FILE

_lock = threading.Lock()
_active_threads: dict[str, threading.Timer] = {}


def _load() -> list[dict]:
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save(reminders: list[dict]):
    os.makedirs(os.path.dirname(REMINDERS_FILE), exist_ok=True)
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, indent=2, ensure_ascii=False)


def _fire_reminder(reminder_id: int, message: str):
    """Called when a reminder fires."""
    print(f"\n\n🔔 REMINDER: {message}\n")

    # Mark as fired in persistence
    with _lock:
        reminders = _load()
        for r in reminders:
            if r["id"] == reminder_id:
                r["fired"] = True
        _save(reminders)


def set_reminder(args: dict) -> str:
    """
    Set a reminder.
    args: {message: str, minutes: int}
    """
    message = args.get("message", "Reminder!")
    minutes = float(args.get("minutes", 5))
    seconds = minutes * 60

    with _lock:
        reminders = _load()
        rid = max((r["id"] for r in reminders), default=0) + 1
        reminder = {
            "id": rid,
            "message": message,
            "minutes": minutes,
            "set_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fires_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + seconds)),
            "fired": False,
        }
        reminders.append(reminder)
        _save(reminders)

    # Start background timer
    timer = threading.Timer(seconds, _fire_reminder, args=(rid, message))
    timer.daemon = True
    timer.start()
    _active_threads[rid] = timer

    return (
        f"⏰ Reminder #{rid} set!\n"
        f"   Message : {message}\n"
        f"   Fires in: {minutes} minutes ({reminder['fires_at']})"
    )


def list_reminders() -> str:
    """List all scheduled reminders."""
    reminders = _load()
    if not reminders:
        return "⏰ No reminders set."

    lines = ["⏰ REMINDERS", "─" * 40]
    pending = [r for r in reminders if not r.get("fired")]
    fired = [r for r in reminders if r.get("fired")]

    if pending:
        lines.append("  PENDING:")
        for r in pending:
            lines.append(f"    #{r['id']} | {r['message']} | fires at {r['fires_at']}")

    if fired:
        lines.append("  COMPLETED:")
        for r in fired[-5:]:  # last 5
            lines.append(f"    #{r['id']} | {r['message']} | fired at {r['fires_at']}")

    return "\n".join(lines)


def cancel_reminder(args: dict) -> str:
    """Cancel a pending reminder. args: {id: int}"""
    rid = int(args.get("id", 0))

    with _lock:
        reminders = _load()
        for r in reminders:
            if r["id"] == rid and not r.get("fired"):
                r["fired"] = True
                _save(reminders)

                # Cancel the thread if active
                timer = _active_threads.pop(rid, None)
                if timer:
                    timer.cancel()

                return f"❌ Reminder #{rid} cancelled: {r['message']}"

    return f"[ERROR] Reminder #{rid} not found or already fired."
