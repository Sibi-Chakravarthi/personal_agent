# JARVIS — Personal AI Agent

A supercharged local AI assistant with **25+ tools**, 3-model routing, RAG knowledge base, persistent memory, and zero cloud dependency. Powered by Ollama.

## Models

| Model | Use Case | Routing |
|---|---|---|
| `qwen2.5-coder:14b` | Code, debugging, file analysis | Code keywords detected |
| `deepseek-r1:8b` | Complex reasoning, analysis, planning | Reasoning keywords detected |
| `llama3.1:8b` | General chat, quick answers | Default fallback |

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama and pull models
ollama serve
ollama pull qwen2.5-coder:14b
ollama pull deepseek-r1:8b
ollama pull llama3.1:8b

# 3. (Optional) Drop files into knowledge/ and index them
python rag/ingest.py

# 4. Run the agent
python main.py
```

---

## Tools (25+)

| Category | Tools | Description |
|---|---|---|
| **Core** | `shell`, `read_file`, `write_file`, `web_search`, `query_knowledge`, `save_memory` | Shell, files, search, RAG, memory |
| **Date & Time** | `get_datetime`, `date_math`, `countdown` | Timezones, date arithmetic, countdowns |
| **System** | `system_info`, `list_processes` | CPU, RAM, disk, battery, processes |
| **Clipboard** | `clipboard_read`, `clipboard_write` | Read/write system clipboard |
| **Notes** | `add_note`, `list_notes`, `complete_note`, `delete_note` | Persistent to-do list |
| **Calculator** | `calculate`, `convert` | Safe math eval, unit conversions |
| **Weather** | `get_weather` | Weather via wttr.in (no API key) |
| **HTTP** | `http_request` | GET/POST/PUT/DELETE any URL |
| **File Manager** | `dir_tree`, `find_files`, `file_info`, `zip_files`, `file_diff` | Tree, find, zip, diff, hash |
| **Reminders** | `set_reminder`, `list_reminders`, `cancel_reminder` | Background scheduled reminders |
| **Code Runner** | `run_python` | Sandboxed Python execution |
| **URL** | `fetch_url` | Extract readable text from URLs |

---

## CLI Commands

| Command | What it does |
|---|---|
| `/help` | Show all commands & capabilities |
| `/index` | Re-index the knowledge/ folder |
| `/memories` | View stored long-term memories |
| `/notes` | View notes & to-do list |
| `/reminders` | View scheduled reminders |
| `/system` | Show system info (CPU, RAM, disk) |
| `/weather` | Quick weather for your location |
| `/status` | Agent dashboard (models, stats) |
| `/clear` | Clear conversation (keeps memory) |
| `/model` | Preview model routing |
| `/exit` | Quit |

---

## Project Structure

```
personal_agent/
├── main.py                 # CLI entry point (colorized)
├── agent.py                # Core ReAct agent loop + auto-RAG
├── router.py               # 3-tier model routing
├── config.py               # All settings
├── requirements.txt
├── knowledge/              # Drop your files here
├── chroma_db/              # Vector store (auto-created)
├── data/                   # Persistent app data (auto-created)
│   ├── notes.json
│   └── reminders.json
├── tools/
│   ├── shell.py            # Shell, read_file, write_file
│   ├── search.py           # DuckDuckGo web search
│   ├── datetime_utils.py   # Date/time/timezone
│   ├── system_info.py      # System monitoring (psutil)
│   ├── clipboard.py        # Clipboard access
│   ├── notes.py            # Notes & to-do
│   ├── calculator.py       # Math + unit conversion
│   ├── weather.py          # Weather (wttr.in)
│   ├── http_client.py      # HTTP requests
│   ├── file_manager.py     # Tree, find, zip, diff
│   ├── scheduler.py        # Background reminders
│   ├── code_runner.py      # Python sandbox
│   └── summarizer.py       # URL text extractor
├── rag/
│   ├── ingest.py           # Index files → ChromaDB
│   └── retriever.py        # Query knowledge base
└── memory/
    └── store.py            # Persistent long-term memory
```

---

## Key Features

- **Auto-RAG**: Complex queries automatically search your knowledge base
- **3-model routing**: Best model picked per message type (code/reasoning/general)
- **Persistent memory**: Remembers facts and preferences across sessions
- **Background reminders**: Set timers that fire even during conversation
- **Zero cloud dependency**: Everything runs locally via Ollama
