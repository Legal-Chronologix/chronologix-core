"""
candidate_events_extractor.py

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
import re
import uuid
from pathlib import Path

from chronologix.steps.classifiers.document_role_classifier import infer_document_role
from chronologix.steps.preprocessing.sentence_splitter import extract_sentences_by_dates

# Phrases that strongly indicate a sentence is NOT a real event:
# certificate-of-service blocks, contact info, page footers, etc.
#
# NOTE: judge-name patterns (e.g. "s/ james", "judge james") used to live
# here, but they fired on real prose like "On May 3, 2022, District Court
# Judge James T. Moody entered an Order". Judge names are now detected
# only in signature-block context. See is_signature_block().
STRONG_ARTIFACT_PHRASES = [
    "certificate of service",
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

# Patterns that indicate a sentence is a signature block.
# These are checked together: a sentence is a signature block only if it
# contains BOTH a signature marker AND a date-line marker, OR is extremely
# short and contains a signature marker. This avoids matching judge names
# that appear in regular narrative prose.
SIGNATURE_MARKERS = [
    "s/ ",
    "/s/",
]

JUDICIAL_TITLE_MARKERS = [
    "judge ",
    "magistrate judge",
    "united states district court",
]

DATE_LINE_MARKERS = [
    "date:",
    "so ordered",
    "dated:",
]

# Event-action verbs. Patterns use \b word boundaries to avoid matching
# substrings of unrelated words ("recorder", "reorder", "ordered" inside
# "in order to"). Inflection groups like (?:s|ed|ing) let one pattern
# cover filed / files / filing without false matches.
#
# Each entry is (display_name, compiled_pattern) so quality_reasons can
# show a clean label like "event_action_signal:file" instead of the raw
# regex source.
EVENT_ACTION_PATTERNS = [
    ("accept", re.compile(r"\baccept(?:s|ed|ing)?\b")),
    ("adopt", re.compile(r"\badopt(?:s|ed|ing)?\b")),
    ("appear", re.compile(r"\bappear(?:s|ed|ing|ance|ances)?\b")),
    ("assign", re.compile(r"\bassign(?:s|ed|ing|ment|ments)?\b")),
    ("award", re.compile(r"\baward(?:s|ed|ing)?\b")),
    ("bar", re.compile(r"\bbar(?:s|red|ring)?\b")),
    ("became a member", re.compile(r"\bbecame a member\b")),
    ("compel", re.compile(r"\bcompel(?:s|led|ling)?\b")),
    ("convert", re.compile(r"\bconvert(?:s|ed|ing)?\b")),
    ("deny", re.compile(r"\bden(?:y|ies|ied|ying)\b")),
    ("discharge", re.compile(r"\bdischarg(?:e|es|ed|ing)\b")),
    ("dismiss", re.compile(r"\bdismiss(?:es|ed|ing)?\b")),
    ("employ", re.compile(r"\bemploy(?:s|ed|ing|ment)?\b")),
    ("enter", re.compile(r"\benter(?:s|ed|ing)?\b")),
    ("failed to appear", re.compile(r"\bfailed to appear\b")),
    ("file", re.compile(r"\bfil(?:e|es|ed|ing)\b")),
    ("grant", re.compile(r"\bgrant(?:s|ed|ing)?\b")),
    ("hire", re.compile(r"\bhir(?:e|es|ed|ing)\b")),
    ("issue", re.compile(r"\bissu(?:e|es|ed|ing)\b")),
    ("mail", re.compile(r"\bmail(?:s|ed|ing)?\b")),
    ("order", re.compile(r"\border(?:s|ed|ing)?\b")),
    ("permit", re.compile(r"\bpermit(?:s|ted|ting)?\b")),
    ("recommend", re.compile(r"\brecommend(?:s|ed|ing|ation|ations)?\b")),
    ("receive", re.compile(r"\breceiv(?:e|es|ed|ing)\b")),
    ("reimburse", re.compile(r"\breimburs(?:e|es|ed|ing)\b")),
    ("sent home", re.compile(r"\bsent home\b")),
    ("serve", re.compile(r"\bserv(?:e|es|ed|ing)\b")),
    ("set", re.compile(r"\bset(?:s|ting)?\b")),  # "hearing set for ..."
    ("suspend", re.compile(r"\bsuspen(?:d|ds|ded|ding|sion|sions)\b")),
    ("terminate", re.compile(r"\bterminat(?:e|es|ed|ing)\b")),
    ("withdraw", re.compile(r"\bwithdr(?:aw|aws|ew|awn|awing)\b")),
]

# Legal-event nouns/concepts. Same (name, pattern) shape for the same reason.
LEGAL_EVENT_PATTERNS = [
    ("arbitration", re.compile(r"\barbitration\b")),
    ("bankruptcy", re.compile(r"\bbankruptcy\b")),
    ("charge", re.compile(r"\bcharge(?:s)?\b")),
    ("deposition", re.compile(r"\bdeposition(?:s)?\b")),
    ("discovery", re.compile(r"\bdiscovery\b")),
    ("eeoc", re.compile(r"\beeoc\b")),
    ("grievance", re.compile(r"\bgrievance(?:s)?\b")),
    ("hearing", re.compile(r"\bhearing(?:s)?\b")),
    ("judgment", re.compile(r"\bjudgment(?:s)?\b")),
    ("motion", re.compile(r"\bmotion(?:s)?\b")),
    ("order", re.compile(r"\border(?:s|ed)?\b")),
    ("recommendation", re.compile(r"\brecommendation(?:s)?\b")),
    ("right_to_sue", re.compile(r"\bright[- ]to[- ]sue\b")),
    ("sanction", re.compile(r"\bsanction(?:s)?\b")),
    ("summary_judgment", re.compile(r"\bsummary judgment\b")),
]

FRAGMENT_STARTS = (
    "with ",
    "and ",
    "or ",
    "but ",
    "at ",
    "to ",
)


def is_signature_block(text: str) -> bool:
    """
    Return True if a sentence looks like a court signature block rather
    than narrative prose.

    A signature block typically combines a date-line marker ("Date:",
    "SO ORDERED"), a signature marker ("s/ ..."), and a judicial title
    on a single line. Narrative prose mentioning a judge's name does NOT
    match because it lacks the date-line / signature markers.

    The function expects already-lowercased text.

    >>> is_signature_block("date: march 27, 2026 s/ james t. moody judge james t.")
    True
    >>> is_signature_block("so ordered. date: august 7, 2024 s/ james t. moody")
    True
    >>> is_signature_block(
    ...     "on may 3, 2022, district court judge james t. moody entered an order"
    ... )
    False
    >>> is_signature_block("judge moody adopted the recommendation on february 3, 2023")
    False
    """
    has_signature = any(marker in text for marker in SIGNATURE_MARKERS)
    has_date_line = any(marker in text for marker in DATE_LINE_MARKERS)
    has_judicial_title = any(marker in text for marker in JUDICIAL_TITLE_MARKERS)

    # Classic signature block: signature marker + date line.
    if has_signature and has_date_line:
        return True

    # Short, signature-heavy fragment: signature marker + title, no real verb.
    # Catches cases like "s/ James T. Moody JUDGE JAMES T." where the
    # sentence splitter cut off mid-block.
    if has_signature and has_judicial_title and len(text.split()) < 20:
        return True

    return False


def find_matches(text: str, patterns: list[tuple[str, re.Pattern]]) -> list[str]:
    """
    Return the display-name of every (name, pattern) entry that matches
    text. Order is preserved from the patterns list.

    >>> find_matches("plaintiff filed a charge", EVENT_ACTION_PATTERNS)
    ['file']
    >>> find_matches("court entered an order", EVENT_ACTION_PATTERNS)
    ['enter', 'order']
    """
    return [name for name, pattern in patterns if pattern.search(text)]


def score_candidate_sentence(sentence: str) -> tuple[int, list[str]]:
    """
    Score whether a date-containing sentence looks like a useful event.

    Higher score means more event-like.
    Lower score means likely footer/signature/certificate/artifact.

    This is intentionally soft. It helps review, but does not silently
    delete candidates.

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

    >>> score, reasons = score_candidate_sentence(
    ...     "On May 3, 2022, District Court Judge James T. Moody entered an "
    ...     "Order [DE 31] referring an underlying motion to dismiss."
    ... )
    >>> score >= 2
    True

    >>> score, reasons = score_candidate_sentence(
    ...     "Plaintiff contends that he engaged in statutorily protected "
    ...     "activity by filing his first EEOC charge on June 6, 2019."
    ... )
    >>> score >= 2
    True
    """
    text = sentence.strip().lower()
    score = 0
    reasons = []

    if not text:
        return -3, ["empty_sentence"]

    if is_signature_block(text):
        score -= 5
        reasons.append("signature_block")

    matched_actions = find_matches(text, EVENT_ACTION_PATTERNS)
    if matched_actions:
        score += 2
        reasons.append(f"event_action_signal:{','.join(matched_actions)}")

    matched_legal = find_matches(text, LEGAL_EVENT_PATTERNS)
    if matched_legal:
        score += 1
        reasons.append(f"legal_event_signal:{','.join(matched_legal)}")

    if any(phrase in text for phrase in STRONG_ARTIFACT_PHRASES):
        score -= 3
        reasons.append("strong_artifact_phrase")

    if any(phrase in text for phrase in WEAK_ARTIFACT_PHRASES):
        score -= 1
        reasons.append("weak_artifact_phrase")

    if text.startswith(FRAGMENT_STARTS):
        score -= 1
        reasons.append("fragment_start")

    # Very short is only suspicious if it is extremely short.
    # Example: "USS terminated plaintiff on January 23, 2020." is short
    # but useful.
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

    Uses sentence_splitter.extract_sentences_by_dates(), so this function
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
