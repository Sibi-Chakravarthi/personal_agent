"""Web search — uses the ddgs package (renamed from duckduckgo_search)."""

try:
    from ddgs import DDGS
    _AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        _AVAILABLE = True
    except ImportError:
        _AVAILABLE = False


def web_search(query: str, max_results: int = 5) -> str:
    if not _AVAILABLE:
        return "[ERROR] Install search: pip install ddgs"
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"**{r['title']}**\n{r['href']}\n{r['body']}\n")
        return "\n---\n".join(results) if results else "No results found."
    except Exception as e:
        return f"[SEARCH ERROR] {e}"
