#!/usr/bin/env python3
"""
Panda — Personal AI Agent CLI
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
  /export       Export conversation history to a file
  /clear        Clear conversation history (keeps long-term memory)
  /model        Preview model routing for next message
  /exit         Quit
"""

import sys
import os

# ── Colors (ANSI) ─────────────────────────────────────────────────────────────
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_DIM     = "\033[2m"
C_CYAN    = "\033[36m"
C_GREEN   = "\033[32m"
C_YELLOW  = "\033[33m"
C_RED     = "\033[31m"
C_BLUE    = "\033[34m"
C_MAGENTA = "\033[35m"

def _c(text, color):
    return f"{color}{text}{C_RESET}"

def _safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))

# ── Startup check ─────────────────────────────────────────────────────────────
try:
    import requests
    resp = requests.get("http://localhost:11434/api/tags", timeout=3)
    models = [m["name"] for m in resp.json().get("models", [])]
except Exception:
    _safe_print(
        f"\n{_c('[ERROR]', C_RED)} Ollama is not running. "
        f"Start it with: {_c('ollama serve', C_CYAN)}\n"
    )
    sys.exit(1)

_safe_print(f"""
{_c('╔══════════════════════════════════════════════════════╗', C_CYAN)}
{_c('║', C_CYAN)}  Panda — Personal AI Agent v2                       {_c('║', C_CYAN)}
{_c('╠══════════════════════════════════════════════════════╣', C_CYAN)}
{_c('║', C_CYAN)}  {_c('28+ tools', C_GREEN)} | {_c('3 models', C_YELLOW)} | {_c('RAG', C_BLUE)} | {_c('memory', C_MAGENTA)} | {_c('project builder', C_GREEN)}  {_c('║', C_CYAN)}
{_c('╚══════════════════════════════════════════════════════╝', C_CYAN)}
  Models loaded: {_c(', '.join(models) or 'none detected', C_DIM)}
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
    _safe_print(f"""
{_c('COMMANDS', C_BOLD)}
{_c('-' * 45, C_DIM)}
  {_c('/help', C_CYAN)}        Show this message
  {_c('/index', C_CYAN)}       Re-index files in knowledge/ folder
  {_c('/memories', C_CYAN)}    View stored long-term memories
  {_c('/notes', C_CYAN)}       View your notes & to-do list
  {_c('/reminders', C_CYAN)}   View scheduled reminders
  {_c('/system', C_CYAN)}      Show system info (CPU, RAM, disk)
  {_c('/weather', C_CYAN)}     Quick weather for your location
  {_c('/status', C_CYAN)}      Agent dashboard
  {_c('/export', C_CYAN)}      Export conversation to a file
  {_c('/clear', C_CYAN)}       Clear conversation (keeps memory)
  {_c('/model', C_CYAN)}       Preview model routing
  {_c('/exit', C_RED)}        Quit

{_c('CAPABILITIES', C_BOLD)}
{_c('-' * 45, C_DIM)}
  Build websites/apps  write_files_batch (all files in one shot)
  Create directories   create_directory
  Open in browser      open_in_browser
  Shell commands       run any command
  File read/write      individual files
  Web search           DuckDuckGo
  RAG knowledge base   auto-injected
  Long-term memory     across sessions
  Notes & to-do        tagged, timestamped
  Background reminders fire during conversation
  Weather              via wttr.in (no API key)
  Calculator           safe eval + unit conversion
  Clipboard            read/write
  System monitoring    CPU, RAM, disk, battery
  HTTP client          GET/POST/PUT/DELETE
  File manager         tree, find, zip, diff
  Python runner        sandboxed subprocess
  URL fetcher          readable text extraction
""")


def show_status():
    from config import MODELS, CHROMA_DIR

    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        mem_count = kb_count = 0
        try:
            mem_count = client.get_collection("agent_memory").count()
        except Exception:
            pass
        try:
            kb_count = client.get_collection("knowledge").count()
        except Exception:
            pass
    except Exception:
        mem_count = kb_count = "?"

    from tools.notes import _load as load_notes
    from tools.scheduler import _load as load_reminders

    pending_notes   = sum(1 for n in load_notes() if not n.get("done"))
    active_reminders = sum(1 for r in load_reminders() if not r.get("fired"))

    _safe_print(f"""
{_c('AGENT DASHBOARD', C_BOLD)}
{_c('-' * 45, C_DIM)}
  {_c('Models', C_CYAN)}
    Code      : {_c(MODELS['code'], C_GREEN)}
    Reasoning : {_c(MODELS['reasoning'], C_GREEN)}
    General   : {_c(MODELS['general'], C_GREEN)}

  {_c('Data', C_YELLOW)}
    Knowledge chunks : {kb_count}
    Stored memories  : {mem_count}
    Pending notes    : {pending_notes}
    Active reminders : {active_reminders}

  {_c('Session', C_MAGENTA)}
    History turns    : {len(history) // 2}
""")


def export_conversation():
    """Save the current conversation history to a timestamped text file."""
    import datetime
    if not history:
        _safe_print(f"  {_c('Nothing to export — conversation is empty.', C_YELLOW)}")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"jarvis_conversation_{timestamp}.txt"

    lines = [f"Panda Conversation Export — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "=" * 60, ""]
    for msg in history:
        role = "You" if msg["role"] == "user" else "Panda"
        lines.append(f"[{role}]")
        lines.append(msg["content"])
        lines.append("")

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        _safe_print(f"  {_c('Exported to:', C_GREEN)} {filename}  ({len(history) // 2} turns)")
    except Exception as e:
        _safe_print(f"  {_c('[ERROR]', C_RED)} Could not export: {e}")


def main():
    global history

    while True:
        try:
            user_input = input(f"{_c('You:', C_GREEN)} ").strip()
        except (EOFError, KeyboardInterrupt):
            _safe_print(f"\n{_c('Bye!', C_CYAN)}")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in {"/exit", "/quit", "exit", "quit"}:
            _safe_print(f"{_c('Bye!', C_CYAN)}")
            break

        if cmd == "/help":
            show_help()
            continue

        if cmd == "/index":
            _safe_print(f"{_c('Indexing knowledge/ ...', C_YELLOW)}")
            ingest()
            continue

        if cmd == "/memories":
            _safe_print(list_memories())
            continue

        if cmd == "/notes":
            _safe_print(list_notes())
            continue

        if cmd == "/reminders":
            _safe_print(list_reminders())
            continue

        if cmd == "/system":
            _safe_print(system_info())
            continue

        if cmd == "/weather":
            _safe_print(get_weather("auto"))
            continue

        if cmd == "/status":
            show_status()
            continue

        if cmd == "/export":
            export_conversation()
            continue

        if cmd == "/clear":
            history = []
            _safe_print(f"{_c('[Conversation cleared. Long-term memory intact.]', C_YELLOW)}\n")
            continue

        if cmd == "/model":
            m = pick_model(user_input)
            _safe_print(f"  Routing to: {label(m)} — {_c(m, C_GREEN)}\n")
            continue

        # ── Agent ─────────────────────────────────────────────────────────────
        try:
            answer, history = run_agent(user_input, history, verbose=True)
            _safe_print(f"\n{_c('Panda:', C_CYAN)} {answer}\n")
        except requests.exceptions.ConnectionError:
            _safe_print(f"{_c('[ERROR]', C_RED)} Lost connection to Ollama. Is it still running?\n")
        except Exception as e:
            _safe_print(f"{_c('[ERROR]', C_RED)} {e}\n")


if __name__ == "__main__":
    main()
