"""Run shell commands with a timeout and basic safety check."""

import subprocess
from config import SHELL_TIMEOUT

# Commands that are too dangerous to run automatically
BLOCKED = {"rm -rf /", "mkfs", "dd if=", ":(){:|:&};:", "shutdown", "reboot"}

def run_shell(command: str) -> str:
    """
    Execute a shell command and return combined stdout + stderr.
    Returns an error string instead of raising on failure.
    """
    cmd_lower = command.strip().lower()
    for blocked in BLOCKED:
        if blocked in cmd_lower:
            return f"[BLOCKED] Refused to run dangerous command: {command}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=SHELL_TIMEOUT,
        )
        out = result.stdout.strip()
        err = result.stderr.strip()

        if out and err:
            return f"{out}\n[stderr]: {err}"
        return out or err or "(no output)"

    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Command exceeded {SHELL_TIMEOUT}s: {command}"
    except Exception as e:
        return f"[ERROR] {e}"


def read_file(path: str) -> str:
    """Read a file from disk."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return f"[ERROR] File not found: {path}"
    except Exception as e:
        return f"[ERROR] {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file. Auto-creates parent directories."""
    try:
        import os
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[OK] Written to {path}"
    except Exception as e:
        return f"[ERROR] {e}"
