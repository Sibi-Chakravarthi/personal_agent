"""
Core agent loop — ReAct style with tool use.
Includes simple-query bypass and auto-RAG injection.
"""

import json
import re
import requests

from config import OLLAMA_BASE, MAX_AGENT_STEPS, MODELS
from router import pick_model, label
from tools.shell import run_shell, read_file, write_file
from tools.search import web_search
from tools.datetime_utils import get_datetime, date_math, countdown
from tools.system_info import system_info, list_processes
from tools.clipboard import clipboard_read, clipboard_write
from tools.notes import add_note, list_notes, complete_note, delete_note
from tools.calculator import calculate, convert
from tools.weather import get_weather
from tools.http_client import http_request
from tools.file_manager import dir_tree, find_files, file_info, zip_files, file_diff
from tools.scheduler import set_reminder, list_reminders, cancel_reminder
from tools.code_runner import run_python
from tools.summarizer import fetch_url
from tools.project_builder import write_files_batch, create_directory, open_in_browser
from rag.retriever import query_knowledge
from memory.store import save_memory, recall_memories

# ── Tool registry ─────────────────────────────────────────────────────────────

TOOLS = {
    # --- Core ---
    "shell":              lambda args: run_shell(args.get("command", "")),
    "read_file":          lambda args: read_file(args.get("path", "")),
    "write_file":         lambda args: write_file(args.get("path", ""), args.get("content", "")),
    "web_search":         lambda args: web_search(args.get("query", "")),
    "query_knowledge":    lambda args: query_knowledge(args.get("question", "")),
    "save_memory":        lambda args: save_memory(args.get("text", ""), args.get("tags", [])) or "[Memory saved]",

    # --- Project Builder (new) ---
    "delegate_to_coder":  lambda args: run_agent(
        user_input=f"You are a headless execution sub-agent. Fulfill this spec EXACTLY: {args.get('instructions', '')}",
        history=[], 
        verbose=False,
        force_model=MODELS["code"],
        is_sub_agent=True
    )[0],
    "write_files_batch":  lambda args: write_files_batch(args),
    "create_directory":   lambda args: create_directory(args),
    "open_in_browser":    lambda args: open_in_browser(args),

    # --- Date & Time ---
    "get_datetime":       get_datetime,
    "date_math":          date_math,
    "countdown":          countdown,

    # --- System ---
    "system_info":        lambda args=None: system_info(),
    "list_processes":     list_processes,

    # --- Clipboard ---
    "clipboard_read":     lambda args=None: clipboard_read(),
    "clipboard_write":    clipboard_write,

    # --- Notes & To-do ---
    "add_note":           lambda args: add_note(args.get("text", ""), args.get("tags", [])),
    "list_notes":         lambda args=None: list_notes(args.get("tag") if args else None),
    "complete_note":      complete_note,
    "delete_note":        delete_note,

    # --- Calculator ---
    "calculate":          lambda args: calculate(args.get("expression", "")),
    "convert":            convert,

    # --- Weather ---
    "get_weather":        lambda args: get_weather(args.get("location", "auto")),

    # --- HTTP Client ---
    "http_request":       http_request,

    # --- File Manager ---
    "dir_tree":           dir_tree,
    "find_files":         find_files,
    "file_info":          file_info,
    "zip_files":          zip_files,
    "file_diff":          file_diff,

    # --- Scheduler ---
    "set_reminder":       set_reminder,
    "list_reminders":     lambda args=None: list_reminders(),
    "cancel_reminder":    cancel_reminder,

    # --- Code Runner ---
    "run_python":         lambda args: run_python(args.get("code", "")),

    # --- URL/Summarizer ---
    "fetch_url":          lambda args: fetch_url(args.get("url", "")),
}

# ── Prompts ───────────────────────────────────────────────────────────────────

TOOL_DESCRIPTIONS = """\
You have access to tools. ONLY use a tool when you genuinely need it.
For casual conversation, greetings, or questions you already know the answer to,
just reply with {"answer": "..."} immediately — do NOT call any tools.

CRITICAL RULES — READ CAREFULLY:
1. Call ONLY ONE tool at a time — the SINGLE tool that answers the question.
2. After receiving a tool result, you MUST include all useful info in {"answer": "..."}.
3. Do NOT call multiple tools when one is enough.
4. Do NOT write files unless the user explicitly asks to save/write/create a file.
5. Do NOT run shell commands unless explicitly asked.
6. Do NOT search the web unless explicitly asked for current/external info.
7. Respond with ONLY a single JSON object per turn — no prose, no markdown outside JSON.

AVAILABLE TOOLS (call one at a time):
━━━ Core ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "shell",             "args": {"command": "ls -la"}}
  {"tool": "read_file",         "args": {"path": "path/to/file.py"}}
  {"tool": "write_file",        "args": {"path": "out.py", "content": "..."}}
  {"tool": "web_search",        "args": {"query": "search terms"}}
  {"tool": "query_knowledge",   "args": {"question": "what does X do?"}}
  {"tool": "save_memory",       "args": {"text": "User prefers tabs", "tags": ["pref"]}}

━━━ Project Builder ━━━━━━━━━━━━━━━━━━
  {"tool": "delegate_to_coder", "args": {"instructions": "Detailed spec of exact files to create and how they should look"}}
  {"tool": "write_files_batch", "args": {"base_dir": "D:\\\\path", "files": {"file.html": "..."}}}
  {"tool": "create_directory",  "args": {"path": "D:\\\\NewFolder"}}
  {"tool": "open_in_browser",   "args": {"target": "D:\\\\index.html"}}

━━━ Date & Time ━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "get_datetime",      "args": {}}
  {"tool": "date_math",         "args": {"days": 45}}
  {"tool": "countdown",         "args": {"target": "2025-12-31"}}

━━━ System Info ━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "system_info",       "args": {}}
  {"tool": "list_processes",    "args": {"count": 10}}

━━━ Clipboard ━━━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "clipboard_read",    "args": {}}
  {"tool": "clipboard_write",   "args": {"text": "..."}}

━━━ Notes & To-do ━━━━━━━━━━━━━━━━━━━━
  {"tool": "add_note",          "args": {"text": "buy groceries", "tags": ["personal"]}}
  {"tool": "list_notes",        "args": {}}
  {"tool": "complete_note",     "args": {"id": 1}}
  {"tool": "delete_note",       "args": {"id": 1}}

━━━ Calculator ━━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "calculate",         "args": {"expression": "sqrt(144) + 2**8"}}
  {"tool": "convert",           "args": {"value": 100, "from": "km", "to": "mi"}}

━━━ Weather ━━━━━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "get_weather",       "args": {"location": "London"}}

━━━ HTTP Client ━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "http_request",      "args": {"method": "GET", "url": "https://..."}}

━━━ File Manager ━━━━━━━━━━━━━━━━━━━━━
  {"tool": "dir_tree",          "args": {"path": ".", "max_depth": 3}}
  {"tool": "find_files",        "args": {"path": ".", "pattern": ".py"}}
  {"tool": "file_info",         "args": {"path": "file.txt"}}
  {"tool": "zip_files",         "args": {"files": ["a.py", "b.py"], "output": "out.zip"}}
  {"tool": "file_diff",         "args": {"file_a": "old.py", "file_b": "new.py"}}

━━━ Reminders ━━━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "set_reminder",      "args": {"message": "push code", "minutes": 30}}
  {"tool": "list_reminders",    "args": {}}
  {"tool": "cancel_reminder",   "args": {"id": 1}}

━━━ Code Runner ━━━━━━━━━━━━━━━━━━━━━━
  {"tool": "run_python",        "args": {"code": "print(2+2)"}}

━━━ URL / Summarizer ━━━━━━━━━━━━━━━━━
  {"tool": "fetch_url",         "args": {"url": "https://..."}}

FINAL ANSWER (always end with this):
  {"answer": "your response here — MUST include the actual data/result"}

RESPONSE FORMAT — MANDATORY:
Your ENTIRE response must be a single JSON object. Nothing else.
No markdown. No "Step 1". No "###". No explanations outside JSON.
JUST the JSON: either {"tool": "...", "args": {...}} or {"answer": "..."}.
"""

SYSTEM_PROMPT = """\
You are Panda — a powerful personal AI assistant for a developer. Be sharp, concise, direct.
You are running LOCALLY on the user's machine with FULL file system access via your tools.
Do NOT refuse to create files or directories. You have `write_files_batch`, `write_file`, `shell` for this.

MOST IMPORTANT RULE: When a user asks a simple question that needs ONE tool, call ONLY that
one tool, then IMMEDIATELY answer with the result. Do NOT chain unnecessary extra tools.

After receiving a tool result, ALWAYS include the actual data in your answer.
Never give vague responses like "here you go" — show the numbers, time, info, etc.

""" + TOOL_DESCRIPTIONS

CHAT_SYSTEM_PROMPT = """\
You are Panda — a personal AI assistant for a developer. Be sharp, concise, and direct.
Answer conversationally. No fluff. You're helpful, witty, and efficient.
"""

# ── Simple query detection ────────────────────────────────────────────────────

SIMPLE_PATTERNS = [
    r"^(yo+|hey+|hi+|hello+|sup|what'?s up|howdy|hiya)[.!?]*$",
    r"^(thanks?|ty|thx|thank you)[.!?]*$",
    r"^(who are you|what are you|what can you do)[?]?$",
    r"^(ok|okay|got it|cool|nice|great|sure)[.!?]*$",
    r"^(yes|no|nah|yeah|yep|nope)[.!?]*$",
    r"^(good morning|good evening|good night|gm|gn)[.!?]*$",
    r"^(bye|goodbye|see ya|later|cya)[.!?]*$",
]

# Any of these words in the message means it's NOT a simple query —
# even if it's short, it likely needs a tool.
_TOOL_SIGNALS = {
    "file", "run", "search", "code", "fix", "read", "write",
    "find", "show", "list", "install", "error", "debug",
    "explain", "help", "what", "how", "why", "check",
    "save", "create", "store", "put", "folder", "dir",
    "script", "function", "class", "generate", "make",
    "time", "date", "weather", "note", "remind", "calculate",
    "clipboard", "system", "process", "convert", "fetch",
    "zip", "diff", "tree", "http", "request", "open",
    "build", "website", "site", "app", "project", "directory",
    "delete", "remove", "rename", "move", "copy", "deploy",
}

def _is_simple_query(text: str) -> bool:
    t = text.strip().lower()
    # Match explicit casual patterns
    for pat in SIMPLE_PATTERNS:
        if re.match(pat, t, re.IGNORECASE):
            return True
    # Short message with no tool-triggering words → treat as simple chat
    if len(t.split()) <= 3 and not any(s in t for s in _TOOL_SIGNALS):
        return True
    return False

# ── Ollama call ───────────────────────────────────────────────────────────────

def _chat(messages: list[dict], model: str) -> str:
    resp = requests.post(
        f"{OLLAMA_BASE}/api/chat",
        json={"model": model, "messages": messages, "stream": False},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def _extract_jsons(text: str) -> list[dict]:
    """Extract ALL valid JSON objects from the text."""
    text = text.strip()
    # Strip <think> blocks (deepseek-r1 style)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if cleaned:
        text = cleaned

    # Try whole thing first
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return [obj]
    except json.JSONDecodeError:
        pass

    # Find ALL {...} blocks
    candidates = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    obj = json.loads(text[start:i+1])
                    if isinstance(obj, dict):
                        candidates.append(obj)
                except json.JSONDecodeError:
                    pass
                start = None

    return candidates


def _normalize(parsed_list: list[dict]) -> list[dict]:
    """Normalize a list of parsed actions."""
    out = []
    for parsed in parsed_list:
        tool = parsed.get("tool", "")
        if tool in {"answer", "final_answer", "respond", "reply"}:
            args = parsed.get("args", {})
            text = (
                args.get("text") or args.get("message") or
                args.get("response") or args.get("content") or str(args)
            )
            out.append({"answer": text})
        elif "answer" in parsed or "tool" in parsed:
            out.append(parsed)
    return out


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_print(msg: str):
    """Safely print text that may contain emojis/unicode."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))


# ── Main agent entry point ────────────────────────────────────────────────────

def run_agent(
    user_input: str,
    history: list[dict],
    verbose: bool = True,
    force_model: str = None,
    is_sub_agent: bool = False,
) -> tuple[str, list[dict]]:

    model = force_model if force_model else pick_model(user_input)

    if verbose:
        prefix = "  [sub-agent]" if is_sub_agent else ""
        _safe_print(f"\n{prefix}  [using {label(model)} — {model}]")

    # ── Fast path: simple chat ────────────────────────────────────────────────
    if not is_sub_agent and _is_simple_query(user_input):
        memories = recall_memories(user_input)
        sys_msg = CHAT_SYSTEM_PROMPT
        if memories:
            sys_msg += f"\n\n{memories}"
        messages = [{"role": "system", "content": sys_msg}] + history
        messages.append({"role": "user", "content": user_input})
        answer = _chat(messages, model)
        history = history + [
            {"role": "user",      "content": user_input},
            {"role": "assistant", "content": answer},
        ]
        return answer, history

    # ── Agent loop ────────────────────────────────────────────────────────────
    memories = recall_memories(user_input)
    system = SYSTEM_PROMPT
    
    if is_sub_agent:
        system += """
[SUB-AGENT CODER MODE]
You are the execution coder sub-agent. Your ONLY job is to write code accurately.
1. Use `write_files_batch` to create the ENTIRE project from the instructions. Do NOT write files one by one.
2. Implement the design spec perfectly: vibrant colors, glassmorphism, responsive grid, animations.
3. DO NOT call `delegate_to_coder`.
"""
    else:
        system += """
[ARCHITECT MODE]
When the user requests a complex project, website, app, or UI:
1. Act as the Master Architect. Do NOT write the raw files yourself.
2. Use `delegate_to_coder` to spawn a coder sub-agent.
3. Pass a brilliant, deeply descriptive aesthetic spec in the `instructions`: mandate vibrant gradients, modern fonts, glassmorphism, and micro-interactions. Specify what files to make.
"""

    if memories:
        system += f"\n\n[Relevant memories:]\n{memories}"

    # Auto-RAG: inject knowledge context for complex queries
    rag_context = query_knowledge(user_input, n_results=3)
    if rag_context and "[" not in rag_context[:5]:
        system += f"\n\n[Relevant knowledge from your files:]\n{rag_context}"

    messages = [{"role": "system", "content": system}] + history
    messages.append({"role": "user", "content": user_input})

    for step in range(MAX_AGENT_STEPS):
        raw = _chat(messages, model)
        actions = _normalize(_extract_jsons(raw))

        if not actions:
            # No JSON found — treat as plain answer
            history = history + [
                {"role": "user",      "content": user_input},
                {"role": "assistant", "content": raw},
            ]
            return raw, history

        results = []
        final_answer = None

        for parsed in actions:
            if "answer" in parsed:
                final_answer = parsed["answer"]
                break

            if "tool" in parsed:
                tool_name = parsed["tool"]
                args = parsed.get("args", {})

                if verbose:
                    prefix = "  [sub-agent]" if is_sub_agent else ""
                    # Truncate huge args for display
                    display_args = _truncate_args_display(args)
                    _safe_print(f"{prefix}  [step {step+1}] {tool_name}({display_args})")

                if tool_name not in TOOLS:
                    res_str = f"[ERROR] Unknown tool '{tool_name}'. Valid tools: {sorted(TOOLS.keys())}"
                else:
                    try:
                        res_str = str(TOOLS[tool_name](args))
                    except Exception as e:
                        res_str = f"[TOOL ERROR] {type(e).__name__}: {e}"

                results.append(f"Result for {tool_name}:\n{res_str}")

        if final_answer:
            save_memory(
                f"User: {user_input[:120]} | Assistant: {final_answer[:200]}",
                tags=["exchange"],
            )
            history = history + [
                {"role": "user",      "content": user_input},
                {"role": "assistant", "content": final_answer},
            ]
            return final_answer, history

        # Feed all tool results back to LLM
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": "Tool results:\n" + "\n\n".join(results) + "\n\nNow give your final {\"answer\": \"...\"}.",
        })

    fallback = "Hit step limit. Try breaking your request into smaller parts."
    return fallback, history


def _truncate_args_display(args: dict, max_len: int = 120) -> str:
    """Truncate large args (e.g. file contents) for readable console output."""
    try:
        s = json.dumps(args, ensure_ascii=False)
        if len(s) > max_len:
            return s[:max_len] + "... }"
        return s
    except Exception:
        return str(args)[:max_len]
