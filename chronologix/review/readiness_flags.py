"""
readiness_flags.py

Review/readiness flagging for candidate chronology events.

This module takes candidate events, enriches them with normalized dates,
groups them by date, and creates review flags.

Flags:
- corroborated
- conflicting
- single_perspective
- partial

These are not legal conclusions. They are review aids.
"""

import json
from collections import defaultdict
from pathlib import Path

from chronologix.extractors.date_extractor import enrich_event_with_date


SIGNAL_PREFIX = "event_action_signal:"

OPPOSING_VERB_PAIRS = [
    ("terminate", "suspend"),
    ("discharge", "suspend"),
    ("grant", "deny"),
    ("accept", "reject"),
    ("adopt", "reject"),
    ("permit", "bar"),
    ("dismiss", "reinstate"),
]

REFERENCE_PHRASE_PREFIXES = (
    "prior to ",
    "following ",
    "year following ",
    "in year following ",
    "as of ",
    "by ",
    "before ",
    "after ",
    "since ",
)


def extract_action_verbs(quality_reasons: list[str]) -> set[str]:
    """
    Pull action verb names out of quality_reasons.

    >>> extract_action_verbs(["event_action_signal:terminate,suspend"])
    {'suspend', 'terminate'}
    >>> extract_action_verbs(["legal_event_signal:eeoc"])
    set()
    """
    verbs = set()

    for reason in quality_reasons:
        if not reason.startswith(SIGNAL_PREFIX):
            continue

        verbs_str = reason[len(SIGNAL_PREFIX):]

        verbs.update(
            verb.strip()
            for verb in verbs_str.split(",")
            if verb.strip()
        )

    return verbs


def find_verb_conflicts(
    verbs_a: set[str],
    verbs_b: set[str],
) -> list[tuple[str, str]]:
    """
    Return opposing verb pairs across two verb sets.

    >>> find_verb_conflicts({"terminate"}, {"suspend"})
    [('terminate', 'suspend')]
    >>> find_verb_conflicts({"suspend"}, {"terminate"})
    [('suspend', 'terminate')]
    >>> find_verb_conflicts({"file"}, {"issue"})
    []
    """
    conflicts = []

    for verb_x, verb_y in OPPOSING_VERB_PAIRS:
        if verb_x in verbs_a and verb_y in verbs_b:
            conflicts.append((verb_x, verb_y))
        elif verb_y in verbs_a and verb_x in verbs_b:
            conflicts.append((verb_y, verb_x))

    return conflicts


def is_date_reference_only(event_text: str) -> bool:
    """
    Detect sentences that reference a date without describing an event
    directly on that date.

    >>> is_date_reference_only("Prior to January 22, 2020, USW knew...")
    True
    >>> is_date_reference_only("On January 22, 2020, USS issued a suspension.")
    False
    """
    return event_text.strip().lower().startswith(REFERENCE_PHRASE_PREFIXES)


def should_include_event_for_review(event: dict) -> bool:
    """
    Decide whether an event should be included in readiness flagging.

    We skip likely artifacts and reference-only date mentions.
    """
    if event.get("status") == "likely_artifact":
        return False

    if event.get("date_norm") is None:
        return False

    if is_date_reference_only(event.get("event_text", "")):
        return False

    return True


def group_events_by_date(events: list[dict]) -> dict[str, list[dict]]:
    """
    Group events by normalized date.
    """
    groups = defaultdict(list)

    for event in events:
        groups[event["date_norm"]].append(event)

    return groups


def flag_date_group(date_norm: str, events: list[dict]) -> dict:
    """
    Decide the review flag for one normalized date group.
    """
    by_perspective: dict[str, list[dict]] = defaultdict(list)

    for event in events:
        perspective = event.get("perspective", "unknown")
        by_perspective[perspective].append(event)

    perspectives = sorted(by_perspective.keys())

    if len(perspectives) <= 1:
        perspective = perspectives[0] if perspectives else "unknown"

        return {
            "date_norm": date_norm,
            "flag": "single_perspective",
            "reason": (
                f"All {len(events)} event(s) on this date come from "
                f"perspective '{perspective}'. No cross-perspective "
                f"corroboration possible."
            ),
            "perspectives": perspectives,
            "event_ids": [event["event_id"] for event in events],
        }

    verbs_by_perspective = {}

    for perspective, perspective_events in by_perspective.items():
        verbs = set()

        for event in perspective_events:
            verbs.update(
                extract_action_verbs(event.get("quality_reasons", []))
            )

        verbs_by_perspective[perspective] = verbs

    all_conflicts = []
    perspective_list = list(verbs_by_perspective.keys())

    for i, p1 in enumerate(perspective_list):
        for p2 in perspective_list[i + 1:]:
            conflicts = find_verb_conflicts(
                verbs_by_perspective[p1],
                verbs_by_perspective[p2],
            )

            for verb1, verb2 in conflicts:
                all_conflicts.append((p1, p2, verb1, verb2))

    if all_conflicts:
        details = "; ".join(
            f"{p1} says '{verb1}' vs {p2} says '{verb2}'"
            for p1, p2, verb1, verb2 in all_conflicts
        )

        return {
            "date_norm": date_norm,
            "flag": "conflicting",
            "reason": f"Perspective disagreement on decision verbs: {details}",
            "perspectives": perspectives,
            "event_ids": [event["event_id"] for event in events],
        }

    shared_verbs = set.intersection(
        *verbs_by_perspective.values()
    ) if verbs_by_perspective else set()

    if shared_verbs:
        return {
            "date_norm": date_norm,
            "flag": "corroborated",
            "reason": (
                "Multiple perspectives share action verb(s): "
                f"{', '.join(sorted(shared_verbs))}"
            ),
            "perspectives": perspectives,
            "event_ids": [event["event_id"] for event in events],
        }

    return {
        "date_norm": date_norm,
        "flag": "partial",
        "reason": (
            "Multiple perspectives reference this date, but they do not "
            "share or contradict action verbs. These may be unrelated "
            "events sharing a date or passing references."
        ),
        "perspectives": perspectives,
        "event_ids": [event["event_id"] for event in events],
    }


def flag_events(events: list[dict]) -> dict:
    """
    Enrich events with dates, filter obvious non-review items, group by date,
    and create readiness flags.
    """
    enriched_events = []
    review_events = []

    skipped_no_date = 0
    skipped_reference_only = 0
    skipped_artifact = 0

    for event in events:
        enriched = enrich_event_with_date(event)
        enriched_events.append(enriched)

        if enriched.get("date_norm") is None:
            skipped_no_date += 1
            continue

        if enriched.get("status") == "likely_artifact":
            skipped_artifact += 1
            continue

        if is_date_reference_only(enriched.get("event_text", "")):
            skipped_reference_only += 1
            continue

        review_events.append(enriched)

    groups = group_events_by_date(review_events)

    flagged_groups = [
        flag_date_group(date_norm, group_events)
        for date_norm, group_events in sorted(groups.items())
    ]

    flag_counts = defaultdict(int)

    for group in flagged_groups:
        flag_counts[group["flag"]] += 1

    return {
        "summary": {
            "total_events_in": len(events),
            "events_with_dates": sum(
                1
                for event in enriched_events
                if event.get("date_norm") is not None
            ),
            "review_events": len(review_events),
            "skipped_no_date": skipped_no_date,
            "skipped_artifact": skipped_artifact,
            "skipped_reference_only": skipped_reference_only,
            "date_groups": len(flagged_groups),
            "flag_counts": dict(flag_counts),
        },
        "events": enriched_events,
        "groups": flagged_groups,
    }


def flag_candidate_events_file(
    input_path: str | Path,
    output_path: str | Path,
) -> dict:
    """
    Load candidate_events.json, generate readiness flags, and write output.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    events = json.loads(input_path.read_text(encoding="utf-8"))
    result = flag_events(events)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Review events: {result['summary']['review_events']}")
    print(f"Date groups: {result['summary']['date_groups']}")
    print(f"Flag counts: {result['summary']['flag_counts']}")
    print(f"Skipped no date: {result['summary']['skipped_no_date']}")
    print(f"Skipped artifacts: {result['summary']['skipped_artifact']}")
    print(
        "Skipped reference-only: "
        f"{result['summary']['skipped_reference_only']}"
    )
    print(f"Wrote {output_path}")

    return result


# if __name__ == "__main__":
#     flag_candidate_events_file(
#         input_path="data/court_listener/gipson/candidate_events.json",
#         output_path="data/court_listener/gipson/flagged_events.json",
#     )