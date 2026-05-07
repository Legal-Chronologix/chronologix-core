import os

from dotenv import load_dotenv

load_dotenv()

COURTLISTENER_BASE_URL = "https://www.courtlistener.com/api/rest/v4"
COURTLISTENER_FILE_STORAGE_URL = "https://storage.courtlistener.com/"
COURTLISTENER_TOKEN = os.getenv("COURTLISTENER_TOKEN")

if not COURTLISTENER_TOKEN:
    raise RuntimeError(
        "COURTLISTENER_TOKEN is missing. Add it to .env or export it in your shell."
    )
