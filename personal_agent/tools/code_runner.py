"""Run Python code snippets in a subprocess sandbox with timeout."""

import subprocess
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import CODE_RUNNER_TIMEOUT


def run_python(code: str) -> str:
    """
    Execute a Python code snippet in a subprocess.
    Safer than raw shell — isolated subprocess with timeout.
    """
    if not code.strip():
        return "[ERROR] No code provided."

    # Write to a temp file
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=CODE_RUNNER_TIMEOUT,
            cwd=tempfile.gettempdir(),
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        lines = [f"🐍 Python Execution (exit code: {result.returncode})", "─" * 40]

        if stdout:
            lines.append(f"stdout:\n{stdout}")
        if stderr:
            lines.append(f"stderr:\n{stderr}")
        if not stdout and not stderr:
            lines.append("(no output)")

        return "\n".join(lines)

    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Code exceeded {CODE_RUNNER_TIMEOUT}s limit."
    except Exception as e:
        return f"[ERROR] {e}"
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
