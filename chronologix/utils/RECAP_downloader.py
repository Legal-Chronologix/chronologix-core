import mimetypes
import os
from pathlib import Path

import requests

def guess_extension(response, fallback=".bin"):
    """
    Try to infer the file extension from the HTTP response.

    Example:
    - Content-Type: application/pdf -> .pdf
    - Content-Type: text/csv -> .csv
    - Content-Type: image/png -> .png

    If the server does not provide a useful Content-Type,
    return the fallback extension instead.
    """
    content_type = response.headers.get("content-type", "").split(";")[0].strip()

    extension = mimetypes.guess_extension(content_type)

    if extension:
        return extension

    return fallback


def download_file(
    filename,
    url,
    output_dir=None,
    extension=None,
    timeout=30,
    headers=None,
):
    """
    Download a file from a URL and save it locally.

    This function is source-agnostic:
    it can download files from CourtListener, S3, or any other URL.

    Args:
        filename: Name to save the file as, without extension.
        url: Full download URL.
        output_dir: Folder where the file should be saved.
        extension: Optional file extension. If not provided, infer from response.
        timeout: Request timeout in seconds.
        headers: Optional request headers, useful for authenticated downloads.

    Returns:
        Path to the saved file if download succeeds, otherwise None.
    """
    if output_dir is None:
        raise FileNotFoundError("Please provide path for output_dir")
    
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, headers=headers, timeout=timeout)

    if not response.ok:
        print("Request failed")
        print("Status:", response.status_code)
        print(response.text[:300])
        return None

    if extension is None:
        extension = guess_extension(response)

    if not extension.startswith("."):
        extension = "." + extension

    output_path = output_dir / f"{filename}{extension}"

    with open(output_path, "wb") as file:
        file.write(response.content)

    print("Saved:", output_path)
    return output_path



import re


def slugify_filename(text: str) -> str:
    """
    Convert a document title into a safe filename slug.

    Example:
    "Amended Document - NOT Motion"
    -> "amended_document_not_motion"
    """
    text = text.lower().strip()

    # Replace any group of non-letter/number characters with underscore
    text = re.sub(r"[^a-z0-9]+", "_", text)

    # Remove leading/trailing underscores
    text = text.strip("_")

    return text

##----------Uncomment this section for quick test ------------------
# if __name__ == "__main__":
#     from chronologix.configs.court_listener import COURTLISTENER_FILE_STORAGE_URL

#     DEFAULT_OUTPUT_DIR = Path("./data/downloads")
#     PDF_DIR = "./data/court_listener/gipson/pdfs"
#     os.makedirs(PDF_DIR, exist_ok=True)

#     filepath_local = ("recap/gov.uscourts.innd.106288/gov.uscourts.innd.",
#                        "106288.123.0.pdf", )

#     download_url = urljoin(COURTLISTENER_FILE_STORAGE_URL, filepath_local)

#     download_file(
#         filename="123_opinion_and_order",
#         url=download_url,
#         output_dir="./data/court_listener/gipson/pdfs",
#         extension=".pdf",
#     )
