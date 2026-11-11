import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
GEMINI_FALLBACK_MODEL = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")
INDEX_DIR = Path(os.environ.get("INDEX_DIR", ROOT / "index"))

# comma-separated; lock to the GitHub Pages origin in production
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:4321").split(",") if o.strip()]

TOP_K = 5
MIN_SCORE = 0.60  # top-1 cosine below this -> refuse without calling the LLM
MAX_HISTORY_TURNS = 4
MAX_QUESTION_CHARS = 500
OFFICIAL_SITE = "https://nu.edu.pk"
