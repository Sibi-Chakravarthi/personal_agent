"""Persistent notes and to-do list — JSON-backed, tagged, timestamped."""

import json
import os
import time
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import NOTES_FILE


def _load() -> list[dict]:
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save(notes: list[dict]):
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)


def add_note(text: str, tags: list[str] = None) -> str:
    """Add a new note. Returns confirmation."""
    notes = _load()
    note = {
        "id": len(notes) + 1,
        "text": text,
        "tags": tags or [],
        "done": False,
        "created": time.strftime("%Y-%m-%d %H:%M"),
    }
    notes.append(note)
    _save(notes)
    return f"📝 Note #{note['id']} added: {text}"


def list_notes(filter_tag: str = None) -> str:
    """List all notes, optionally filtered by tag."""
    notes = _load()
    if not notes:
        return "📝 No notes yet. Use add_note to create one."

    if filter_tag:
        notes = [n for n in notes if filter_tag.lower() in [t.lower() for t in n.get("tags", [])]]
        if not notes:
            return f"📝 No notes with tag '{filter_tag}'."

    lines = ["📝 NOTES", "─" * 40]
    for n in notes:
        status = "✅" if n.get("done") else "⬜"
        tags = f" [{', '.join(n['tags'])}]" if n.get("tags") else ""
        lines.append(f"  {status} #{n['id']} {n['text']}{tags}  ({n['created']})")

    pending = sum(1 for n in notes if not n.get("done"))
    done = sum(1 for n in notes if n.get("done"))
    lines.append(f"\n  Total: {len(notes)} | Pending: {pending} | Done: {done}")
    return "\n".join(lines)


def complete_note(args: dict) -> str:
    """Mark a note as done. args: {id: int}"""
    note_id = int(args.get("id", 0))
    notes = _load()
    for n in notes:
        if n["id"] == note_id:
            n["done"] = True
            _save(notes)
            return f"✅ Note #{note_id} marked as done: {n['text']}"
    return f"[ERROR] Note #{note_id} not found."


def delete_note(args: dict) -> str:
    """Delete a note. args: {id: int}"""
    note_id = int(args.get("id", 0))
    notes = _load()
    for i, n in enumerate(notes):
        if n["id"] == note_id:
            removed = notes.pop(i)
            _save(notes)
            return f"🗑️ Deleted note #{note_id}: {removed['text']}"
    return f"[ERROR] Note #{note_id} not found."
