import uuid
from pathlib import Path

import pymupdf


def extract_text_by_page(filepath, filetype="pdf"):
    """
    Extract text from a PDF page by page.

    Returns a document model with:
    - document id
    - document name
    - filepath
    - pages with page number and text
    """
    filepath = Path(filepath)
    doc = pymupdf.open(filepath, filetype=filetype)

    model = {
        "doc_id": str(uuid.uuid4()),
        "doc_name": filepath.name,
        "filepath": str(filepath),
        "filetype": filetype,
        "pages": [],
    }

    for page_number, page in enumerate(doc, start=1):
        page_data = {
            "page_number": page_number,
            "text": page.get_text(),
        }

        model["pages"].append(page_data)

    doc.close()

    return model


result = extract_text_by_page(
    "./data/court_listener/gipson/pdfs/104_summary_judgment.pdf"
)

print(result["doc_name"])
print("pages:", len(result["pages"]))
print(result["pages"][0]["text"][:500])
