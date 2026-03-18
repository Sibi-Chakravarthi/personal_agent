import os

# ── Ollama ────────────────────────────────────────────────────────────────────
OLLAMA_BASE = "http://localhost:11434"

MODELS = {
    "code":      "qwen2.5-coder:14b",     # coding, debugging, file analysis
    "reasoning": "deepseek-r1:8b",         # complex analysis, planning, comparison
    "general":   "llama3.1:8b",            # chat, quick questions, casual
}

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR  = os.path.join(BASE_DIR, "knowledge")
CHROMA_DIR     = os.path.join(BASE_DIR, "chroma_db")
DATA_DIR       = os.path.join(BASE_DIR, "data")         # persistent app data
NOTES_FILE     = os.path.join(DATA_DIR, "notes.json")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")

# ── RAG ───────────────────────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".cpp", ".c", ".h", ".cs",
    ".go", ".rs", ".rb", ".php",
    ".md", ".txt", ".json", ".yaml", ".yml",
    ".html", ".css", ".sh", ".pdf",
    ".sql", ".toml", ".ini", ".cfg", ".env",
    ".xml", ".csv", ".log",
}

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100

# ── Agent ─────────────────────────────────────────────────────────────────────
MAX_AGENT_STEPS     = 15
SHELL_TIMEOUT       = 30      # seconds
CODE_RUNNER_TIMEOUT = 20      # seconds for python code execution
HTTP_TIMEOUT        = 15      # default HTTP request timeout

# ── Memory ────────────────────────────────────────────────────────────────────
MAX_HISTORY_TURNS   = 20
MEMORY_RECALL_COUNT = 5

# Create data dir on import
os.makedirs(DATA_DIR, exist_ok=True)
