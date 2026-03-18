"""Advanced file operations — tree, find, zip, diff, hash, rename."""

import os
import hashlib
import zipfile
import difflib


def dir_tree(args: dict) -> str:
    """Show directory tree. args: {path: str, max_depth?: int}"""
    path = args.get("path", ".")
    max_depth = int(args.get("max_depth", 3))

    if not os.path.isdir(path):
        return f"[ERROR] Not a directory: {path}"

    lines = [f"📁 {os.path.abspath(path)}", "─" * 50]
    count = {"files": 0, "dirs": 0}

    def _walk(dir_path, prefix, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")
            return

        dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e))]
        files = [e for e in entries if not os.path.isdir(os.path.join(dir_path, e))]

        for f in files:
            fpath = os.path.join(dir_path, f)
            size = os.path.getsize(fpath)
            lines.append(f"{prefix}📄 {f}  ({_fmt_size(size)})")
            count["files"] += 1

        for d in dirs:
            lines.append(f"{prefix}📂 {d}/")
            count["dirs"] += 1
            _walk(os.path.join(dir_path, d), prefix + "  ", depth + 1)

    _walk(path, "  ", 1)
    lines.append(f"\n  {count['dirs']} directories, {count['files']} files")
    return "\n".join(lines)


def find_files(args: dict) -> str:
    """Find files matching a pattern. args: {path: str, pattern: str, max_results?: int}"""
    path = args.get("path", ".")
    pattern = args.get("pattern", "").lower()
    max_results = int(args.get("max_results", 20))

    if not os.path.isdir(path):
        return f"[ERROR] Not a directory: {path}"

    matches = []
    for root, _, files in os.walk(path):
        for f in files:
            if pattern in f.lower():
                fpath = os.path.join(root, f)
                matches.append((fpath, os.path.getsize(fpath)))
                if len(matches) >= max_results:
                    break
        if len(matches) >= max_results:
            break

    if not matches:
        return f"🔍 No files matching '{pattern}' in {path}"

    lines = [f"🔍 Found {len(matches)} files matching '{pattern}':", "─" * 50]
    for fpath, size in matches:
        lines.append(f"  {fpath}  ({_fmt_size(size)})")
    return "\n".join(lines)


def file_info(args: dict) -> str:
    """Get detailed info about a file. args: {path: str}"""
    path = args.get("path", "")
    if not os.path.exists(path):
        return f"[ERROR] File not found: {path}"

    stat = os.stat(path)
    import time
    lines = [
        f"📄 FILE INFO — {os.path.basename(path)}",
        "─" * 40,
        f"  Path     : {os.path.abspath(path)}",
        f"  Size     : {_fmt_size(stat.st_size)} ({stat.st_size:,} bytes)",
        f"  Modified : {time.ctime(stat.st_mtime)}",
        f"  Created  : {time.ctime(stat.st_ctime)}",
    ]

    # Hash for files
    if os.path.isfile(path) and stat.st_size < 100_000_000:  # < 100MB
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            lines.append(f"  SHA-256  : {h.hexdigest()}")
        except Exception:
            pass

    return "\n".join(lines)


def zip_files(args: dict) -> str:
    """Create a zip archive. args: {files: list[str], output: str}"""
    files = args.get("files", [])
    output = args.get("output", "archive.zip")

    if not files:
        return "[ERROR] No files specified."

    try:
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                if os.path.isfile(f):
                    zf.write(f, os.path.basename(f))
                elif os.path.isdir(f):
                    for root, _, fnames in os.walk(f):
                        for fname in fnames:
                            fpath = os.path.join(root, fname)
                            arcname = os.path.relpath(fpath, os.path.dirname(f))
                            zf.write(fpath, arcname)
        return f"📦 Created {output} ({_fmt_size(os.path.getsize(output))})"
    except Exception as e:
        return f"[ERROR] {e}"


def file_diff(args: dict) -> str:
    """Show diff between two files. args: {file_a: str, file_b: str}"""
    fa = args.get("file_a", "")
    fb = args.get("file_b", "")

    try:
        with open(fa, "r", encoding="utf-8", errors="ignore") as f:
            lines_a = f.readlines()
        with open(fb, "r", encoding="utf-8", errors="ignore") as f:
            lines_b = f.readlines()

        diff = difflib.unified_diff(lines_a, lines_b, fromfile=fa, tofile=fb, lineterm="")
        result = "\n".join(diff)
        if not result:
            return "✅ Files are identical."
        return f"📝 DIFF\n{'─' * 50}\n{result}"
    except FileNotFoundError as e:
        return f"[ERROR] {e}"


def _fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
