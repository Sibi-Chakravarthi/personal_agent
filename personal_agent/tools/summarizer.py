"""Fetch and extract readable text from URLs."""

import re
import requests


def fetch_url(url: str) -> str:
    """
    Fetch a URL and extract readable text content.
    Strips HTML tags and returns clean text for summarization.
    """
    if not url:
        return "[ERROR] URL is required."

    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")

        # Plain text / JSON
        if "application/json" in content_type:
            return f"🌐 {url}\n{'─' * 40}\n{resp.text[:3000]}"

        if "text/plain" in content_type:
            return f"🌐 {url}\n{'─' * 40}\n{resp.text[:3000]}"

        # HTML — strip tags
        text = resp.text
        # Remove script and style blocks
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Decode common entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&nbsp;", " ").replace("&quot;", '"')

        if len(text) > 3000:
            text = text[:3000] + "\n... (truncated)"

        return f"🌐 Content from {url}\n{'─' * 50}\n{text}"

    except requests.exceptions.Timeout:
        return f"[TIMEOUT] Could not fetch {url} within 15s."
    except requests.exceptions.ConnectionError:
        return f"[ERROR] Could not connect to {url}"
    except Exception as e:
        return f"[ERROR] {e}"
