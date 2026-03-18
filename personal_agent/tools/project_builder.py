"""
Project builder — create entire multi-file projects in one shot.
This is the reliable alternative to the flaky delegate_to_coder pattern.
"""

import os


def write_files_batch(args: dict) -> str:
    """
    Create multiple files at once for a project.

    args: {
        "base_dir": "D:\\\\Testing\\\\MyProject",   # root directory
        "files": {
            "index.html": "<html>...</html>",
            "css/styles.css": "body { ... }",
            "js/script.js": "..."
        }
    }
    """
    base_dir = args.get("base_dir", ".")
    files: dict = args.get("files", {})

    if not files:
        return "[ERROR] No files provided. Pass a 'files' dict mapping relative paths to content."

    created = []
    errors = []

    for rel_path, content in files.items():
        full_path = os.path.join(base_dir, rel_path)
        try:
            os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            size = len(content.encode("utf-8"))
            created.append(f"  ✓ {rel_path}  ({_fmt(size)})")
        except Exception as e:
            errors.append(f"  ✗ {rel_path} — {e}")

    lines = [f"📁 Project created at: {os.path.abspath(base_dir)}", "─" * 50]
    lines += created
    if errors:
        lines += ["", "⚠️  Errors:"] + errors
    lines.append(f"\n  {len(created)} file(s) written, {len(errors)} failed.")
    return "\n".join(lines)


def create_directory(args: dict) -> str:
    """
    Create a directory (and any missing parents).
    args: {"path": "D:\\\\Testing\\\\MyProject"}
    """
    path = args.get("path", "")
    if not path:
        return "[ERROR] 'path' is required."
    try:
        os.makedirs(path, exist_ok=True)
        return f"📁 Directory created: {os.path.abspath(path)}"
    except Exception as e:
        return f"[ERROR] {e}"


def open_in_browser(args: dict) -> str:
    """
    Open a file or URL in the default browser.
    args: {"target": "D:\\\\Testing\\\\index.html"} or {"target": "https://example.com"}
    """
    import subprocess
    import sys

    target = args.get("target", "")
    if not target:
        return "[ERROR] 'target' (path or URL) is required."

    try:
        if sys.platform == "win32":
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])
        return f"🌐 Opened in browser: {target}"
    except Exception as e:
        return f"[ERROR] Could not open browser: {e}"


def _fmt(b: int) -> str:
    for unit in ("B", "KB", "MB"):
        if b < 1024:
            return f"{b:.0f} {unit}"
        b //= 1024
    return f"{b:.0f} GB"
