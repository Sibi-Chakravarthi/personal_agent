"""
Three-tier model routing:
  qwen2.5-coder:14b   → code / debug / file tasks
  deepseek-r1:8b       → reasoning / analysis / planning / comparison
  llama3.1:8b          → general chat / quick answers / casual
"""

from config import MODELS

CODE_KEYWORDS = {
    # intent
    "code", "debug", "fix", "error", "bug", "implement", "write a", "write me",
    "refactor", "optimize", "function", "class", "script", "program",
    "algorithm", "compile", "syntax", "runtime", "traceback", "exception",
    "snippet", "codeblock", "lint", "type hint", "decorator",
    # languages & tools
    "python", "javascript", "typescript", "java", "c++", "rust", "go",
    "html", "css", "sql", "bash", "shell", "git", "docker", "api",
    "regex", "json", "yaml", "import", "library", "package", "module",
    "react", "node", "flask", "django", "fastapi", "express",
    # file actions
    "read my file", "look at my code", "check this file", "review this",
    "explain this code", "what does this do", "run this code", "execute",
}

REASONING_KEYWORDS = {
    # analysis & planning
    "analyze", "analyse", "compare", "contrast", "evaluate", "assess",
    "plan", "design", "architect", "strategy", "think through",
    "pros and cons", "trade-off", "tradeoff", "pros cons",
    "summarize", "summarise", "break down", "step by step",
    "reasoning", "logic", "deduce", "infer", "conclude",
    # complex tasks
    "research", "investigate", "deep dive", "comprehensive",
    "explain in detail", "elaborate", "thorough",
    "decision", "recommend", "suggest approach", "best way",
    "why should", "how would you", "what approach",
}

TOOL_KEYWORDS = {
    # datetime
    "time", "date", "timezone", "countdown", "calendar",
    # system
    "cpu", "ram", "memory", "disk", "battery", "processes", "system info",
    # clipboard
    "clipboard", "paste", "copied",
    # notes
    "note", "todo", "to-do", "to do", "reminder",
    # calculator
    "calculate", "math", "convert", "conversion",
    # weather
    "weather", "temperature", "forecast",
    # http
    "http request", "api call", "fetch url",
}


CREATIVE_CODE_KEYWORDS = {
    "website", "frontend", "ui", "ux", "display", "interface", "react", "html", 
    "aesthetic", "design", "css", "layout"
}

def pick_model(user_message: str) -> str:
    """Return the model name best suited for this message."""
    msg = user_message.lower()

    # Check creative coding keywords first (highest priority) -> deeply logical design needed
    for kw in CREATIVE_CODE_KEYWORDS:
        if kw in msg:
            return MODELS["reasoning"]

    # Check code keywords next
    for kw in CODE_KEYWORDS:
        if kw in msg:
            return MODELS["code"]

    # Check reasoning keywords
    for kw in REASONING_KEYWORDS:
        if kw in msg:
            return MODELS["reasoning"]

    # General model for everything else (incl tool-keywords — tools don't need big models)
    return MODELS["general"]


def label(model: str) -> str:
    if model == MODELS["code"]:
        return "💻 coder"
    if model == MODELS["reasoning"]:
        return "🧠 reasoning"
    return "💬 general"
