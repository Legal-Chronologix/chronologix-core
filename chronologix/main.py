from pathlib import Path

from chronologix.extractors.candidate_events_extractor import build_candidate_events
from chronologix.parsers.pdf_parser import PDFParser
from chronologix.sources.court_listener.document_mapper import (
    load_documents_from_available_docs,
)


CASE_DIR = Path("data/court_listener/gipson")
AVAILABLE_DOCS_PATH = CASE_DIR / "available_docs.json"
PDF_DIR = CASE_DIR / "pdfs"
EXTRACTED_TEXT_DIR = CASE_DIR / "extracted_text"
CANDIDATE_EVENTS_PATH = CASE_DIR / "candidate_events.json"


def run_gipson_pipeline() -> None:
    """
    Run the current Chronologix MVP pipeline for the Gipson case.

    Workflow:
    1. Load CourtListener available document metadata.
    2. Convert metadata into generic Document objects.
    3. Parse PDFs into page-level extracted-text JSON.
    4. Extract source-linked candidate events.
    """
    print("Loading CourtListener document metadata...")
    documents = load_documents_from_available_docs(
        available_docs_path=AVAILABLE_DOCS_PATH,
        pdf_dir=PDF_DIR,
    )

    print(f"Loaded {len(documents)} documents.")

    print("\nParsing PDFs...")
    parser = PDFParser(output_dir=EXTRACTED_TEXT_DIR)
    parsed_paths = parser.parse_documents(documents)

    print(f"Parsed {len(parsed_paths)} PDFs.")

    print("\nBuilding candidate events...")
    events = build_candidate_events(
        input_dir=EXTRACTED_TEXT_DIR,
        output_path=CANDIDATE_EVENTS_PATH,
    )

    print("\nDone.")
    print(f"Extracted text directory: {EXTRACTED_TEXT_DIR}")
    print(f"Candidate events path: {CANDIDATE_EVENTS_PATH}")
    print(f"Candidate events count: {len(events)}")


if __name__ == "__main__":
    run_gipson_pipeline()