"""
date_extractor.py

Extract and normalize dates from candidate event text.

This module is source-agnostic. It does not know about CourtListener,
PDFs, document roles, or conflict flags.

Input:
    event_text

Output:
    date_raw
    date_norm
"""

import re

import dateparser


DATE_REGEX = re.compile(
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?"
    r"|Dec(?:ember)?)"
    r"\s+\d{1,2},\s+\d{4}",
    flags=re.IGNORECASE,
)


def extract_date_raw(event_text: str) -> str | None:
    """
    Return the first written date string from event text.

    >>> extract_date_raw("USS hired him on October 29, 2012.")
    'October 29, 2012'
    >>> extract_date_raw("This has no date.") is None
    True
    """
    if not event_text:
        return None

    match = DATE_REGEX.search(event_text)

    if not match:
        return None

    return match.group(0)


def normalize_date_text(date_text: str | None) -> str | None:
    """
    Normalize a date string to ISO format: YYYY-MM-DD.

    >>> normalize_date_text("October 29, 2012")
    '2012-10-29'
    >>> normalize_date_text(None) is None
    True
    """
    if not date_text:
        return None

    parsed = dateparser.parse(date_text)

    if parsed is None:
        return None

    return parsed.date().isoformat()


def extract_normalized_event_date(
    event_text: str,
) -> tuple[str | None, str | None]:
    """
    Extract and normalize the first date in event_text.

    Returns:
        (date_norm, date_raw)

    >>> extract_normalized_event_date("USS hired him on October 29, 2012.")
    ('2012-10-29', 'October 29, 2012')
    >>> extract_normalized_event_date("This has no date.")
    (None, None)
    """
    date_raw = extract_date_raw(event_text)
    date_norm = normalize_date_text(date_raw)

    return date_norm, date_raw


def enrich_event_with_date(event: dict) -> dict:
    """
    Return a copy of an event with date_raw and date_norm fields added.
    """
    date_norm, date_raw = extract_normalized_event_date(
        event.get("event_text", "")
    )

    enriched = dict(event)
    enriched["date_raw"] = date_raw
    enriched["date_norm"] = date_norm
    enriched["date_status"] = "parsed" if date_norm else "missing_or_unparsed"

    return enriched