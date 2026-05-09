import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

COURTLISTENER_BASE_URL = "https://www.courtlistener.com/api/rest/v4"
COURTLISTENER_FILE_STORAGE_URL = "https://storage.courtlistener.com/"
COURTLISTENER_PDF_DIR = Path("./data/court_listener/gipson/pdfs")
COURTLISTENER_TOKEN = os.getenv("COURTLISTENER_TOKEN")


def get_courtlistener_headers():
    """
    Build request headers for CourtListener API calls.

    Raises an error only when an authenticated request is actually needed.
    This avoids breaking imports/tests that do not need the token.
    """
    if not COURTLISTENER_TOKEN:
        raise RuntimeError(
            "COURTLISTENER_TOKEN is missing. Add it to .env "
            "or export it in your shell."
        )

    return {
        "Authorization": f"Token {COURTLISTENER_TOKEN}",
        "Accept": "application/json",
    }