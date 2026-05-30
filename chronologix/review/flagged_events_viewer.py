"""
flagged_events_viewer.py

Utility for reading flagged_events.json and displaying each flagged date group
with its event sentences.

This does not create new flags. It only joins:

    groups[].event_ids
    back to
    events[].event_text
"""

import json
from pathlib import Path


def load_flagged_events(path: str | Path) -> dict:
    """
    Load flagged_events.json.
    """
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def build_event_lookup(flagged_data: dict) -> dict[str, dict]:
    """
    Build event_id -> event object lookup.

    flagged_events.json stores full events separately from groups.
    Groups only keep event_ids, so we need this lookup to show sentence text.
    """
    return {
        event["event_id"]: event
        for event in flagged_data.get("events", [])
    }


def expand_flagged_groups(flagged_data: dict) -> list[dict]:
    """
    Return groups with full event objects attached.

    Output shape:
    [
        {
            "date_norm": "...",
            "flag": "...",
            "reason": "...",
            "events": [...]
        }
    ]
    """
    event_lookup = build_event_lookup(flagged_data)

    expanded_groups = []

    for group in flagged_data.get("groups", []):
        group_events = []

        for event_id in group.get("event_ids", []):
            event = event_lookup.get(event_id)

            if event is not None:
                group_events.append(event)

        expanded_groups.append(
            {
                "date_norm": group.get("date_norm"),
                "flag": group.get("flag"),
                "reason": group.get("reason"),
                "perspectives": group.get("perspectives", []),
                "events": group_events,
            }
        )

    return expanded_groups


def print_flagged_groups_sentence_by_sentence(
    flagged_data: dict,
    include_single_perspective: bool = True,
) -> None:
    """
    Print each flagged date group with event sentences underneath.
    """
    expanded_groups = expand_flagged_groups(flagged_data)

    for group in expanded_groups:
        if not include_single_perspective and group["flag"] == "single_perspective":
            continue

        print("=" * 80)
        print(f"Date: {group['date_norm']}")
        print(f"Flag: {group['flag']}")
        print(f"Perspectives: {', '.join(group['perspectives'])}")
        print(f"Reason: {group['reason']}")
        print("-" * 80)

        for index, event in enumerate(group["events"], start=1):
            print(f"{index}. [{event.get('perspective')}] {event.get('event_text')}")
            print(
                f"   Source: {event.get('source_doc')} "
                f"p.{event.get('page_number')} | "
                f"status={event.get('status')} | "
                f"quality={event.get('quality_score')}"
            )
            print()

    print("=" * 80)


def export_flagged_groups_markdown(
    flagged_data: dict,
    output_path: str | Path,
    include_single_perspective: bool = True,
) -> Path:
    """
    Export flagged groups into a readable Markdown file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    expanded_groups = expand_flagged_groups(flagged_data)

    lines = ["# Flagged Events Review", ""]

    summary = flagged_data.get("summary", {})
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total events in: {summary.get('total_events_in')}")
    lines.append(f"- Review events: {summary.get('review_events')}")
    lines.append(f"- Date groups: {summary.get('date_groups')}")
    lines.append(f"- Flag counts: {summary.get('flag_counts')}")
    lines.append("")

    for group in expanded_groups:
        if not include_single_perspective and group["flag"] == "single_perspective":
            continue

        lines.append(f"## {group['date_norm']} — {group['flag']}")
        lines.append("")
        lines.append(f"**Reason:** {group['reason']}")
        lines.append("")
        lines.append(f"**Perspectives:** {', '.join(group['perspectives'])}")
        lines.append("")

        for index, event in enumerate(group["events"], start=1):
            lines.append(f"{index}. **[{event.get('perspective')}]** {event.get('event_text')}")
            lines.append(
                f"   - Source: `{event.get('source_doc')}`, "
                f"page {event.get('page_number')}"
            )
            lines.append(
                f"   - Status: `{event.get('status')}`, "
                f"quality: `{event.get('quality_score')}`"
            )
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    return output_path


# if __name__ == "__main__":
#     flagged_path = "data/court_listener/gipson/flagged_events.json"

#     flagged_data = load_flagged_events(flagged_path)

#     print_flagged_groups_sentence_by_sentence(
#         flagged_data,
#         include_single_perspective=True,
#     )

#     export_flagged_groups_markdown(
#         flagged_data,
#         output_path="data/court_listener/gipson/flagged_events_review.md",
#         include_single_perspective=True,
#     )