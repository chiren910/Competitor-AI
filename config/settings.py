# config/settings.py
import os
from dotenv import load_dotenv

# Load environment variables from .env once, for the whole application.
load_dotenv()

# --- API keys / credentials -------------------------------------------------
# Read once here and import everywhere else (single source of truth).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

# --- Application settings ---------------------------------------------------
# Default model used by the LLM processor.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

# Server port for the FastAPI app.
APP_PORT = int(os.getenv("APP_PORT", "4545"))
