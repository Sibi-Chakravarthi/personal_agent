"""Raw HTTP client — GET, POST, PUT, DELETE any URL."""

import json
import requests


def http_request(args: dict) -> str:
    """
    Make an HTTP request.
    args: {method: str, url: str, headers?: dict, body?: str|dict, timeout?: int}
    """
    method = args.get("method", "GET").upper()
    url = args.get("url", "")
    headers = args.get("headers", {})
    body = args.get("body", None)
    timeout = int(args.get("timeout", 15))

    if not url:
        return "[ERROR] URL is required."

    try:
        kwargs = {"headers": headers, "timeout": timeout}

        if body:
            if isinstance(body, dict):
                kwargs["json"] = body
                headers.setdefault("Content-Type", "application/json")
            else:
                kwargs["data"] = body

        resp = requests.request(method, url, **kwargs)

        # Build response summary
        lines = [
            f"🌐 {method} {url}",
            f"   Status: {resp.status_code} {resp.reason}",
            f"   Time  : {resp.elapsed.total_seconds():.2f}s",
            f"   Size  : {len(resp.content)} bytes",
            "",
        ]

        # Response headers
        lines.append("   Headers:")
        for k, v in list(resp.headers.items())[:10]:
            lines.append(f"     {k}: {v}")

        # Body (truncated)
        body_text = resp.text
        if len(body_text) > 2000:
            body_text = body_text[:2000] + "\n... (truncated)"

        lines.append(f"\n   Body:\n{body_text}")

        return "\n".join(lines)

    except requests.exceptions.Timeout:
        return f"[TIMEOUT] Request to {url} exceeded {timeout}s"
    except requests.exceptions.ConnectionError:
        return f"[ERROR] Could not connect to {url}"
    except Exception as e:
        return f"[HTTP ERROR] {e}"
