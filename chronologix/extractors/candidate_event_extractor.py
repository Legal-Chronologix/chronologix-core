"""
candidate_events_extractor.py

Step 1 of the Chronologix event pipeline.

Turns date-containing sentences into structured *candidate event* objects.
A candidate event is NOT yet a confirmed legal event and is NOT yet flagged
(corroborated / conflicting / unconfirmed). It only records:

    - the sentence text
    - where it came from (document, page)
    - the role of that document (complaint, opinion, order, ...)
    - the raw date string found inside the sentence

Date normalization (dateparser) and conflict flagging are later steps.
"""

import json
import re
import uuid
from pathlib import Path

# --- Adjust this import to match the filename of your existing extractor ---
# It must expose extract_sentences_by_dates() and REGEX_DATE_PATTERN.
from chronologix.preprocessing.sentence_splitter import extract_sentences_by_dates, REGEX_DATE_PATTERN


# Keyword -> document role. Checked in ORDER, first match wins.
# Order matters: "123_opinion_and_order..." contains both "opinion" and
# "order", and "90_order_on_report_and_recommendations" contains both
# "order" and "report_and_recommendation". The ordering below resolves
# those correctly for the Gipson file names.
DOC_ROLE_RULES = [
    ("complaint", "complaint"),
    ("opinion", "opinion"),
    ("summary_judgment", "motion_summary_judgment"),
    ("order", "order"),
    ("report_and_recommendation", "report_recommendation"),
]
DEFAULT_DOC_ROLE = "other"

# Document role -> whose account this document represents.
# This is the axis you compare across (plaintiff's story vs the record).
# It is a heuristic: a summary judgment motion can be filed by either side,
# but in the Gipson packet the one you have was filed by a defendant.
ROLE_TO_PERSPECTIVE = {
    "complaint": "plaintiff",
    "opinion": "court",
    "order": "court",
    "report_recommendation": "court",
    "motion_summary_judgment": "defendant",
    "other": "unknown",
}


def normalize_extraction_text(text: str) -> str:
    """
    Collapse PDF line breaks and repeated whitespace for extraction only.

    The original clean_text stays preserved in the parsed document JSON.
    This normalized version is only used so sentence extraction works better.

    Example:
        "On January 22, 2020 Mr. Gipson\\nwas sent home."
        ->
        "On January 22, 2020 Mr. Gipson was sent home."
    """
    if not text:
        return ""

    return " ".join(text.split())


def detect_doc_role(doc_name: str) -> str:
    """
    Guess a document role from its filename.

    First matching keyword wins.

    >>> detect_doc_role("1_complaint.pdf")
    'complaint'
    >>> detect_doc_role("123_opinion_and_order_and_terminate_civil_case.pdf")
    'opinion'
    >>> detect_doc_role("90_order_on_report_and_recommendations.pdf")
    'order'
    >>> detect_doc_role("89_report_and_recommendations.pdf")
    'report_recommendation'
    >>> detect_doc_role("118_amended_document_not_motion.pdf")
    'other'
    """
    name = doc_name.lower()

    for keyword, role in DOC_ROLE_RULES:
        if keyword in name:
            return role

    return DEFAULT_DOC_ROLE


def build_events_from_page(
    clean_text: str,
    source_doc: str,
    page_number: int,
    doc_role: str,
) -> list[dict]:
    """
    Build candidate event objects from one page of cleaned text.

    This uses sentence_splitter.extract_sentences_by_dates(), so this function
    does not directly search for dates itself.

    Each returned sentence becomes one candidate event.
    """
    events = []
    extraction_text = normalize_extraction_text(clean_text)

    date_sentences = extract_sentences_by_dates(extraction_text)

    for sentence in date_sentences:
        events.append(
            {
                "event_id": str(uuid.uuid4()),
                "event_text": sentence,
                "source_doc": source_doc,
                "page_number": page_number,
                "doc_role": doc_role,
                "perspective": ROLE_TO_PERSPECTIVE.get(doc_role, "unknown"),
                "status": "candidate",
            }
        )

    return events


def build_events_from_document(doc_json: dict) -> list[dict]:
    """
    Build all candidate events for one parsed document JSON.

    Expected parser output shape:

    {
        "doc_name": "1_complaint.pdf",
        "pages": [
            {
                "page_number": 1,
                "clean_text": "..."
            }
        ]
    }
    """
    doc_name = doc_json["doc_name"]
    doc_role = detect_doc_role(doc_name)

    events = []

    for page in doc_json.get("pages", []):
        events.extend(
            build_events_from_page(
                clean_text=page.get("clean_text", ""),
                source_doc=doc_name,
                page_number=page["page_number"],
                doc_role=doc_role,
            )
        )

    return events


def build_candidate_events(
    input_dir: str | Path,
    output_path: str | Path,
) -> list[dict]:
    """
    Load every parsed-document JSON file in input_dir, extract candidate
    events, and write one candidate_events.json file.
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    all_events = []

    for json_file in sorted(input_dir.glob("*.json")):
        doc_json = json.loads(json_file.read_text(encoding="utf-8"))
        doc_events = build_events_from_document(doc_json)

        all_events.extend(doc_events)

        print(f"{json_file.name}: {len(doc_events)} candidate events")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(all_events, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Wrote {len(all_events)} events to {output_path}")

    return all_events


if __name__ == "__main__":
    build_candidate_events(
        input_dir="data/court_listener/gipson/extracted_text",
        output_path="data/court_listener/gipson/candidate_events.json",
    )