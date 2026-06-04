from pathlib import Path

from chronologix.steps.extractors.candidate_events_extractor import build_candidate_events
from chronologix.steps.parsers.pdf_parser import PDFParser
from chronologix.steps.review.readiness_flags import flag_candidate_events_file
from chronologix.sources.court_listener.document_mapper import (
    load_documents_from_available_docs,
)


CASE_DIR = Path("data/court_listener/gipson")
AVAILABLE_DOCS_PATH = CASE_DIR / "available_docs.json"
PDF_DIR = CASE_DIR / "pdfs"
EXTRACTED_TEXT_DIR = CASE_DIR / "extracted_text"
CANDIDATE_EVENTS_PATH = CASE_DIR / "candidate_events.json"
FLAGGED_EVENTS_PATH = CASE_DIR / "flagged_events.json"


def run_gipson_pipeline() -> None:
    """
    Run the current Chronologix MVP pipeline for the Gipson case.

    This is a local/demo workflow, not the final production workflow.

    Pipeline:
    1. Load CourtListener metadata from available_docs.json.
    2. Convert CourtListener metadata into generic Document objects.
    3. Parse PDFs into page-level extracted_text JSON.
    4. Extract source-linked candidate event sentences.
    5. Add readiness/review flags grouped by normalized date.
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
    print(f"Candidate events: {len(events)}")

    print("\nFlagging readiness groups...")
    flag_candidate_events_file(
        input_path=CANDIDATE_EVENTS_PATH,
        output_path=FLAGGED_EVENTS_PATH,
    )

    print("\nDone.")


if __name__ == "__main__":
    run_gipson_pipeline()