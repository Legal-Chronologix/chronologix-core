# Chronologix

> Turns litigation PDFs into source-linked candidate chronology events, and flags where the record agrees, disagrees, or only has one side of the story.

---

## What it does

Chronologix ingests court filings (PDFs from CourtListener / RECAP), extracts every dated event with full page-level provenance, and groups events by date across documents to flag:

- **`conflicting`** — perspectives disagree on what happened
- **`corroborated`** — perspectives agree
- **`single_perspective`** — only one side mentions the date
- **`partial`** — multi-perspective but no clear agreement

Every candidate event keeps its source document, page number, document role, and the rules that flagged it. Nothing is silently dropped — borderline cases get a `low_confidence` status for human review.

---

## A real result

Validated on **Gipson v. U.S. Steel** (Case 2:21-cv-00071, N.D. Ind.), the pipeline surfaces a real conflict between the plaintiff's complaint and the court's opinion:

```
2020-01-22 → CONFLICTING
  Plaintiff (complaint.pdf, p.1): "...sent home from work and subsequently terminated."
  Plaintiff (complaint.pdf, p.3): "...subsequently discharged for allegedly failing to stabilize the '#2 Shear' machine."
  Court    (opinion_and_order.pdf, p.3): "USS issued a five-day suspension to plaintiff..."

  Reason: plaintiff says 'terminate' vs court says 'suspend';
          plaintiff says 'discharge' vs court says 'suspend'
```

Same date, contradicting dispositions, no case-specific tuning.

---

## Pipeline

```
CourtListener metadata
  → PDF downloader
  → page-level PDF parser
  → text cleaner + sentence splitter
  → document role classifier
  → candidate event extractor   → candidate_events.json
  → date normalizer + flagger   → flagged_events.json
```

---

## Output shape

`candidate_events.json` entries look like:

```json
{
  "event_id": "...",
  "event_text": "USS terminated plaintiff on January 23, 2020.",
  "source_doc": "123_opinion_and_order.pdf",
  "page_number": 11,
  "doc_role": "court_opinion",
  "perspective": "court",
  "quality_score": 2,
  "quality_reasons": ["event_action_signal:terminate"],
  "status": "candidate"
}
```

`flagged_events.json` groups these by normalized date:

```json
{
  "date_norm": "2020-01-22",
  "flag": "conflicting",
  "reason": "plaintiff says 'terminate' vs court says 'suspend'",
  "perspectives": ["court", "plaintiff"],
  "event_ids": ["...", "...", "..."]
}
```

---

## Status

**Beta.** Validated end-to-end on one public RECAP case (Gipson). The technical spine works; the next phase is talking to real litigation paralegals and attorneys to see if the output is useful as it stands or needs to change.

Known limitations:
- Date-grouping misses conflicts where documents date the same event differently
- Page-boundary sentence truncation can clip ~5% of events
- Public RECAP data only — no private firm document support yet

---

## Roadmap

**Now**
- Validate output with paralegals and attorneys
- Tighten verb-pair coverage based on real conflicts seen

**Next**
- Context windows (next 1–2 sentences) for nuance like disputed-settlement language
- Cross-document event matching beyond exact-date grouping
- Simple review UI for flagged groups

**Later**
- Private-firm document support (depositions, emails, medical records)
- Entity extraction and event-type classification
- Exportable chronology in attorney-ready formats

---

## Why this exists

Built after a conversation with a litigation paralegal who described their actual workflow: manually bookmarking events in PDFs, then retyping them into a timeline for the attorney. The retyping is the pain point. Chronologix is an attempt to remove that step while preserving — and improving on — what makes a paralegal-built chronology trustworthy: every event traceable to a specific page in a specific document.