#!/usr/bin/env python3
"""
Personal AI Agent — CLI interface
Run: python main.py

Commands:
  /help         Show all commands
  /index        Re-index your knowledge/ folder
  /memories     Show stored memories
  /notes        Show your notes & to-do list
  /reminders    Show pending reminders
  /system       Show system info (CPU, RAM, disk, battery)
  /weather      Quick weather check
  /status       Agent dashboard — models, memory, knowledge stats
  /clear        Clear conversation history (keeps long-term memory)
  /model        Preview model routing for next message
  /exit         Quit
"""

import sys
import os

# ── Colors (ANSI) ─────────────────────────────────────────────────────────────
C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"
C_DIM    = "\033[2m"
C_CYAN   = "\033[36m"
C_GREEN  = "\033[32m"
C_YELLOW = "\033[33m"
C_RED    = "\033[31m"
C_BLUE   = "\033[34m"
C_MAGENTA= "\033[35m"

def _c(text, color):
    return f"{color}{text}{C_RESET}"

# ── Startup check ─────────────────────────────────────────────────────────────
try:
    import requests
    resp = requests.get("http://localhost:11434/api/tags", timeout=3)
    models = [m["name"] for m in resp.json().get("models", [])]
except Exception:
    print(f"\n{_c('[ERROR]', C_RED)} Ollama is not running. Start it with: {_c('ollama serve', C_CYAN)}\n")
    sys.exit(1)

print(f"""
{_c('╔══════════════════════════════════════════════════════╗', C_CYAN)}
{_c('║', C_CYAN)}  🤖  {_c('JARVIS — Personal AI Agent', C_BOLD)}                    {_c('║', C_CYAN)}
{_c('╠══════════════════════════════════════════════════════╣', C_CYAN)}
{_c('║', C_CYAN)}  {_c('25+ tools', C_GREEN)} • {_c('3 models', C_YELLOW)} • {_c('RAG knowledge', C_BLUE)} • {_c('memory', C_MAGENTA)}   {_c('║', C_CYAN)}
{_c('╚══════════════════════════════════════════════════════╝', C_CYAN)}
  Models: {_c(', '.join(models) or 'none detected', C_DIM)}
  Type {_c('/help', C_CYAN)} for commands, {_c('/exit', C_RED)} to quit.
""")

from agent import run_agent
from rag.ingest import ingest
from memory.store import list_memories
from router import pick_model, label
from tools.system_info import system_info
from tools.weather import get_weather
from tools.notes import list_notes
from tools.scheduler import list_reminders

history: list[dict] = []


def show_help():
    print(f"""
{_c('COMMANDS', C_BOLD)}
{_c('─' * 45, C_DIM)}
  {_c('/help', C_CYAN)}        Show this message
  {_c('/index', C_CYAN)}       Re-index files in knowledge/ folder
  {_c('/memories', C_CYAN)}    View stored long-term memories
  {_c('/notes', C_CYAN)}       View your notes & to-do list
  {_c('/reminders', C_CYAN)}   View scheduled reminders
  {_c('/system', C_CYAN)}      Show system info (CPU, RAM, disk)
  {_c('/weather', C_CYAN)}     Quick weather for your location
  {_c('/status', C_CYAN)}      Agent dashboard
  {_c('/clear', C_CYAN)}       Clear conversation (keeps memory)
  {_c('/model', C_CYAN)}       Preview model routing
  {_c('/exit', C_RED)}        Quit

{_c('CAPABILITIES', C_BOLD)}
{_c('─' * 45, C_DIM)}
  💻 Shell commands, file read/write
  🔍 Web search (DuckDuckGo)
  📚 RAG knowledge base (auto-injected)
  🧠 Long-term memory across sessions
  📝 Notes & to-do lists
  ⏰ Background reminders
  🌤️  Weather lookups
  🔢 Calculator & unit conversions
  📋 Clipboard read/write
  🖥️  System monitoring
  🌐 HTTP client (API testing)
  📁 File manager (tree, find, zip, diff)
  🐍 Python code runner (sandboxed)
  🔗 URL content fetcher
""")


def show_status():
    """Show a dashboard of agent state."""
    from config import MODELS, CHROMA_DIR

    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)

        mem_count = 0
        kb_count = 0
        try:
            mem_col = client.get_collection("agent_memory")
            mem_count = mem_col.count()
        except Exception:
            pass
        try:
            kb_col = client.get_collection("knowledge")
            kb_count = kb_col.count()
        except Exception:
            pass
    except Exception:
        mem_count = "?"
        kb_count = "?"

    # Count notes
    from tools.notes import _load as load_notes
    notes = load_notes()
    pending = sum(1 for n in notes if not n.get("done"))

    # Count reminders
    from tools.scheduler import _load as load_reminders
    rems = load_reminders()
    active_rems = sum(1 for r in rems if not r.get("fired"))

    print(f"""
{_c('AGENT DASHBOARD', C_BOLD)}
{_c('─' * 45, C_DIM)}
  {_c('Models', C_CYAN)}
    💻 Code      : {_c(MODELS['code'], C_GREEN)}
    🧠 Reasoning : {_c(MODELS['reasoning'], C_GREEN)}
    💬 General   : {_c(MODELS['general'], C_GREEN)}

  {_c('Data', C_YELLOW)}
    📚 Knowledge chunks : {kb_count}
    🧠 Stored memories  : {mem_count}
    📝 Pending notes    : {pending}
    ⏰ Active reminders : {active_rems}

  {_c('Session', C_MAGENTA)}
    💬 History turns    : {len(history) // 2}
""")


def main():
    global history

    while True:
        try:
            user_input = input(f"{_c('You:', C_GREEN)} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{_c('Bye! 👋', C_CYAN)}")
            break

        if not user_input:
            continue

        # ── Commands ──────────────────────────────────────────────────────────
        cmd = user_input.lower()

        if cmd in {"/exit", "/quit", "exit", "quit"}:
            print(f"{_c('Bye! 👋', C_CYAN)}")
            break

        if cmd == "/help":
            show_help()
            continue

        if cmd == "/index":
            print(f"{_c('Indexing knowledge/ directory...', C_YELLOW)}")
            ingest()
            continue

        if cmd == "/memories":
            print(list_memories())
            continue

        if cmd == "/notes":
            print(list_notes())
            continue

        if cmd == "/reminders":
            print(list_reminders())
            continue

        if cmd == "/system":
            print(system_info())
            continue

        if cmd == "/weather":
            print(get_weather("auto"))
            continue

        if cmd == "/status":
            show_status()
            continue

        if cmd == "/clear":
            history = []
            print(f"{_c('[Conversation cleared. Long-term memory intact.]', C_YELLOW)}\n")
            continue

        if cmd == "/model":
            m = pick_model("(next message will be judged here)")
            print(f"  Routing to: {label(m)} — {_c(m, C_GREEN)}\n")
            continue

        # ── Agent ─────────────────────────────────────────────────────────────
        try:
            answer, history = run_agent(user_input, history, verbose=True)
            print(f"\n{_c('Assistant:', C_CYAN)} {answer}\n")
        except requests.exceptions.ConnectionError:
            print(f"{_c('[ERROR]', C_RED)} Lost connection to Ollama. Is it still running?\n")
        except Exception as e:
            print(f"{_c('[ERROR]', C_RED)} {e}\n")


if __name__ == "__main__":
    main()
