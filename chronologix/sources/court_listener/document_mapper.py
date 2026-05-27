import json
from pathlib import Path

from chronologix.models.document import Document
from chronologix.utils.file_downloader import slugify_filename


def build_pdf_filename(doc: dict) -> str:
    """
    Build the expected downloaded PDF filename from CourtListener metadata.

    This should match the naming logic used by your downloader.
    """
    document_number = doc.get("document_number")
    short_description = doc.get("short_description") or "document"

    filename = f"{document_number}_{slugify_filename(short_description)}.pdf"

    return filename


def courtlistener_doc_to_document(
    doc: dict,
    pdf_dir: str | Path,
) -> Document:
    """
    Convert one CourtListener RECAP document metadata object into
    Chronologix's generic Document model.
    """
    pdf_dir = Path(pdf_dir)
    pdf_filename = build_pdf_filename(doc)
    pdf_path = pdf_dir / pdf_filename

    return Document(
        doc_name=pdf_filename,
        filepath=pdf_path,
        source="court_listener",
        filetype="pdf",
        source_doc_id=str(doc.get("id")),
        metadata={
            "courtlistener_id": doc.get("id"),
            "docket_id": doc.get("docket_id"),
            "docket_entry_id": doc.get("docket_entry_id"),
            "document_number": doc.get("document_number"),
            "entry_number": doc.get("entry_number"),
            "entry_date_filed": doc.get("entry_date_filed"),
            "document_type": doc.get("document_type"),
            "short_description": doc.get("short_description"),
            "description": doc.get("description"),
            "page_count": doc.get("page_count"),
            "absolute_url": doc.get("absolute_url"),
            "filepath_local": doc.get("filepath_local"),
            "pacer_doc_id": doc.get("pacer_doc_id"),
            "cites": doc.get("cites", []),
            "is_available": doc.get("is_available"),
        },
    )


def load_documents_from_available_docs(
    available_docs_path: str | Path,
    pdf_dir: str | Path,
) -> list[Document]:
    """
    Load available_docs.json and convert each metadata object into Document.
    """
    available_docs_path = Path(available_docs_path)

    docs = json.loads(available_docs_path.read_text(encoding="utf-8"))

    return [
        courtlistener_doc_to_document(doc, pdf_dir)
        for doc in docs
    ]
