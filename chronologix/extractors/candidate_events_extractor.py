"""
candidate_events_extractor.py

Step 1 of the Chronologix event pipeline.

Turns date-containing sentences into structured candidate event objects.

A candidate event is NOT yet a confirmed legal event and is NOT yet flagged
as corroborated / conflicting / unconfirmed. It only records:

- the sentence text
- where it came from: document + page
- inferred document role
- inferred source perspective
- role inference confidence/signals
- candidate quality score/status

Date normalization, event typing, and conflict/readiness flags are later steps.
"""

import json
import uuid
from pathlib import Path

from chronologix.classifiers.document_role_classifier import infer_document_role
from chronologix.preprocessing.sentence_splitter import extract_sentences_by_dates


STRONG_ARTIFACT_PHRASES = [
    "certificate of service",
    "date:",
    "s/ james",
    "judge james",
    "united states district court",
    "usdc in/nd",
    "attorneys for defendant",
    "attorneys for plaintiff",
    "tel:",
    "fax:",
    "email:",
]

WEAK_ARTIFACT_PHRASES = [
    "respectfully submitted",
    "law department",
    "notice of this filing",
    "electronic filing system",
]

EVENT_ACTION_SIGNALS = [
    "accepted",
    "adopted",
    "appeared",
    "assigned",
    "became a member",
    "conduct discovery",
    "converted",
    "denied",
    "discharged",
    "dismissed",
    "employed",
    "failed to appear",
    "filed",
    "granted",
    "hired",
    "issued",
    "mailed",
    "ordered",
    "permitted",
    "recommended",
    "received",
    "sent home",
    "served",
    "suspended",
    "terminated",
    "was assigned",
]

LEGAL_EVENT_SIGNALS = [
    "arbitration",
    "bankruptcy",
    "charge",
    "deposition",
    "discovery",
    "eeoc",
    "grievance",
    "hearing",
    "judgment",
    "motion",
    "order",
    "recommendation",
    "right to sue",
    "right-to-sue",
    "sanction",
    "summary judgment",
]

FRAGMENT_STARTS = (
    "with ",
    "and ",
    "or ",
    "but ",
    "at ",
    "to ",
)


def score_candidate_sentence(sentence: str) -> tuple[int, list[str]]:
    """
    Score whether a date-containing sentence looks like a useful event.

    Higher score means more event-like.
    Lower score means likely footer/signature/certificate/artifact.

    This is intentionally soft. It helps review, but does not silently delete
    candidates.

    >>> score, reasons = score_candidate_sentence(
    ...     "USS terminated plaintiff on January 23, 2020."
    ... )
    >>> score >= 2
    True

    >>> score, reasons = score_candidate_sentence(
    ...     "Date: March 27, 2026 s/ James T. Moody JUDGE JAMES T."
    ... )
    >>> score < 0
    True
    """
    text = sentence.strip().lower()
    score = 0
    reasons = []

    if not text:
        return -3, ["empty_sentence"]

    if any(signal in text for signal in EVENT_ACTION_SIGNALS):
        score += 2
        reasons.append("event_action_signal")

    if any(signal in text for signal in LEGAL_EVENT_SIGNALS):
        score += 1
        reasons.append("legal_event_signal")

    if any(phrase in text for phrase in STRONG_ARTIFACT_PHRASES):
        score -= 3
        reasons.append("strong_artifact_phrase")

    if any(phrase in text for phrase in WEAK_ARTIFACT_PHRASES):
        score -= 1
        reasons.append("weak_artifact_phrase")

    if text.startswith("date:"):
        score -= 2
        reasons.append("signature_date_block")

    if text.startswith(FRAGMENT_STARTS):
        score -= 1
        reasons.append("fragment_start")

    # Very short is only suspicious if it is extremely short.
    # Example: "USS terminated plaintiff on January 23, 2020." is short but useful.
    if len(sentence.split()) < 5:
        score -= 1
        reasons.append("very_short")

    # Very long candidate sentences are often merged paragraphs.
    if len(sentence.split()) > 90:
        score -= 1
        reasons.append("very_long_possible_merge")

    return score, reasons


def get_candidate_status(score: int) -> str:
    """
    Convert quality score into review status.

    >>> get_candidate_status(2)
    'candidate'
    >>> get_candidate_status(0)
    'low_confidence'
    >>> get_candidate_status(-1)
    'likely_artifact'
    """
    if score >= 2:
        return "candidate"

    if score >= 0:
        return "low_confidence"

    return "likely_artifact"


def build_events_from_page(
    clean_text: str,
    source_doc: str,
    page_number: int,
    doc_id: str,
    doc_role: str,
    perspective: str,
    doc_role_confidence: str,
    doc_role_signals: list[str],
) -> list[dict]:
    """
    Build candidate event objects from one page of cleaned text.

    This uses sentence_splitter.extract_sentences_by_dates(), so this function
    does not directly search for dates itself.

    Each returned date-containing sentence becomes one candidate event.
    """
    events = []
    date_sentences = extract_sentences_by_dates(clean_text)

    for sentence in date_sentences:
        quality_score, quality_reasons = score_candidate_sentence(sentence)

        events.append(
            {
                "event_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "event_text": sentence,
                "source_doc": source_doc,
                "page_number": page_number,
                "doc_role": doc_role,
                "perspective": perspective,
                "doc_role_confidence": doc_role_confidence,
                "doc_role_signals": doc_role_signals,
                "quality_score": quality_score,
                "quality_reasons": quality_reasons,
                "status": get_candidate_status(quality_score),
            }
        )

    return events


def build_events_from_document(doc_json: dict) -> list[dict]:
    """
    Build all candidate events for one parsed document JSON.

    Expected parser output shape:

    {
        "doc_id": "...",
        "doc_name": "1_complaint.pdf",
        "metadata": {...},
        "pages": [
            {
                "page_number": 1,
                "clean_text": "..."
            }
        ]
    }
    """
    doc_id = doc_json.get("doc_id", "")
    doc_name = doc_json["doc_name"]

    role_result = infer_document_role(doc_json)

    events = []

    for page in doc_json.get("pages", []):
        events.extend(
            build_events_from_page(
                clean_text=page.get("clean_text", ""),
                source_doc=doc_name,
                page_number=page["page_number"],
                doc_id=doc_id,
                doc_role=role_result.role,
                perspective=role_result.perspective,
                doc_role_confidence=role_result.confidence,
                doc_role_signals=role_result.matched_signals,
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


# if __name__ == "__main__":
#     build_candidate_events(
#         input_dir="data/court_listener/gipson/extracted_text",
#         output_path="data/court_listener/gipson/candidate_events.json",
#     )