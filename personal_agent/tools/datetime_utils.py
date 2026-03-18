"""Date, time, timezone, and calendar utilities."""

from datetime import datetime, timedelta, timezone
import time

_ZONES = {
    "utc": 0, "gmt": 0, "est": -5, "edt": -4, "cst": -6, "cdt": -5,
    "mst": -7, "mdt": -6, "pst": -8, "pdt": -7, "ist": 5.5, "jst": 9,
    "cet": 1, "eet": 2, "aest": 10, "aedt": 11, "nzst": 12,
    "bst": 1, "hkt": 8, "sgt": 8, "kst": 9,
}


def get_datetime(args: dict = None) -> str:
    """Get current date/time, optionally in a specific timezone."""
    args = args or {}
    tz_name = args.get("timezone", "").strip().lower()

    if tz_name and tz_name in _ZONES:
        offset = _ZONES[tz_name]
        h, m = int(offset), int((offset % 1) * 60)
        tz = timezone(timedelta(hours=h, minutes=m))
        now = datetime.now(tz)
        return (
            f"🕐 {now.strftime('%A, %B %d, %Y — %I:%M:%S %p')} ({tz_name.upper()})\n"
            f"   ISO: {now.isoformat()}\n"
            f"   Unix: {int(now.timestamp())}\n"
            f"   Week: {now.isocalendar()[1]}, Day of year: {now.timetuple().tm_yday}"
        )

    now = datetime.now()
    return (
        f"🕐 {now.strftime('%A, %B %d, %Y — %I:%M:%S %p')} (local)\n"
        f"   ISO: {now.isoformat()}\n"
        f"   Unix: {int(now.timestamp())}\n"
        f"   Week: {now.isocalendar()[1]}, Day of year: {now.timetuple().tm_yday}"
    )


def date_math(args: dict) -> str:
    """Add/subtract days from a date. args: {days: int, from_date?: 'YYYY-MM-DD'}"""
    days = int(args.get("days", 0))
    base_str = args.get("from_date", "")

    if base_str:
        try:
            base = datetime.strptime(base_str, "%Y-%m-%d")
        except ValueError:
            return f"[ERROR] Bad date format: {base_str}. Use YYYY-MM-DD."
    else:
        base = datetime.now()

    result = base + timedelta(days=days)
    diff_label = f"{abs(days)} days {'from now' if days >= 0 else 'ago'}"
    return (
        f"📅 {diff_label}: {result.strftime('%A, %B %d, %Y')}\n"
        f"   From: {base.strftime('%Y-%m-%d')} → To: {result.strftime('%Y-%m-%d')}"
    )


def countdown(args: dict) -> str:
    """Days until a target date. args: {target: 'YYYY-MM-DD'}"""
    target_str = args.get("target", "")
    try:
        target = datetime.strptime(target_str, "%Y-%m-%d")
    except ValueError:
        return f"[ERROR] Bad date: {target_str}. Use YYYY-MM-DD."

    delta = target - datetime.now()
    days = delta.days
    if days < 0:
        return f"⏰ That date was {abs(days)} days ago ({target_str})"
    return f"⏰ {days} days until {target.strftime('%A, %B %d, %Y')}"
