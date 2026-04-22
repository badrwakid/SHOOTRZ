import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve paths once: backend/utils/config.py -> backend/ and SHOOTRZ/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_SHOOTRZ_DIR = _BACKEND_DIR.parent

# Load env files so values in backend/.env win over SHOOTRZ/.env and over empty
# shell variables (default dotenv override=False leaves empty GEMINI_API_KEY set
# in the OS and ignores the file — override=True fixes that).
for path in (_SHOOTRZ_DIR / ".env", _BACKEND_DIR / ".env"):
	if path.is_file():
		load_dotenv(path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip() or None
GEMINI_MODEL = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "60"))
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))

