"""Clipboard integration — read/write the system clipboard."""

try:
    import pyperclip
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


def clipboard_read() -> str:
    """Read the current clipboard contents."""
    if not _AVAILABLE:
        return "[ERROR] Install pyperclip: pip install pyperclip"
    try:
        text = pyperclip.paste()
        if not text:
            return "📋 Clipboard is empty."
        return f"📋 Clipboard contents:\n{text}"
    except Exception as e:
        return f"[ERROR] {e}"


def clipboard_write(args: dict) -> str:
    """Write text to the clipboard. args: {text: str}"""
    if not _AVAILABLE:
        return "[ERROR] Install pyperclip: pip install pyperclip"
    try:
        text = args.get("text", "")
        pyperclip.copy(text)
        preview = text[:80] + "..." if len(text) > 80 else text
        return f"📋 Copied to clipboard: {preview}"
    except Exception as e:
        return f"[ERROR] {e}"
