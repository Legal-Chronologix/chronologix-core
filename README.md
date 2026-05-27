# Chronologix

> A provenance legal-tech MVP that turns litigation PDFs into source-linked candidate chronology events and prepares the foundation for missing and conflicting event review.

---

## Overview

Chronologix is not trying to model every litigation chronology workflow — at least not yet.

The current MVP starts with one small employment-dispute RECAP case, **Gipson v. United States Steel Corporation**, to prove the technical spine end-to-end:

- CourtListener / RECAP document ingestion
- Available document filtering
- PDF downloading
- Page-level PDF parsing
- Source-preserving extracted text
- Rule-based text cleaning and sentence splitting
- Document role inference
- Candidate event extraction
- Candidate quality scoring

**The goal right now is not perfect legal event understanding.** The goal is to produce a reviewable, source-linked chronology draft where every candidate event keeps its source document and page number.

---

## Current Pipeline

```
CourtListener available_docs.json
  → CourtListener document mapper
  → Generic Document objects
  → PDFParser
  → extracted_text/*.json
  → document_role_classifier
  → sentence_splitter
  → candidate_events_extractor
  → candidate_events.json
```

---

## Current Output Shape

Each candidate event in `candidate_events.json` currently includes:

```json
{
  "event_id": "...",
  "doc_id": "...",
  "event_text": "USS terminated plaintiff on January 23, 2020.",
  "source_doc": "123_opinion_and_order_and_terminate_civil_case.pdf",
  "page_number": 11,
  "doc_role": "court_opinion",
  "perspective": "court",
  "doc_role_confidence": "medium",
  "doc_role_signals": ["opinion and order"],
  "quality_score": 2,
  "quality_reasons": ["event_action_signal"],
  "status": "candidate"
}
```

---

## Product Direction

Chronologix is moving toward a **chronology readiness tool**, not just a timeline extractor.

The long-term goal is to help litigation teams answer:

> *Is this chronology complete, trustworthy, source-linked, and ready for attorney review?*

---

## Roadmap

### Done

- [x] Define Chronologix use case: source-linked chronology readiness
- [x] Use CourtListener / RECAP as first data source
- [x] Build CourtListener client for RECAP metadata
- [x] Handle pagination and basic rate limits
- [x] Filter available RECAP documents
- [x] Save available document metadata to `available_docs.json`
- [x] Download available PDFs for the Gipson MVP case
- [x] Add generic file downloader
- [x] Add CourtListener-specific downloader
- [x] Add generic `Document` model
- [x] Add CourtListener document mapper from metadata to `Document`
- [x] Build PDF parser
- [x] Parse PDFs into page-level JSON
- [x] Preserve document metadata in parsed text JSON
- [x] Save extracted text to `data/court_listener/gipson/extracted_text/`
- [x] Add text cleaner for PDF artifacts and spacing
- [x] Add sentence splitter for date-containing sentences
- [x] Protect abbreviations such as `Mr.`, `No.`, `U.S.`, and middle initials
- [x] Remove common citation/court-reference noise for extraction
- [x] Add document role classifier using filename, metadata, and first-page text
- [x] Add candidate event extractor
- [x] Generate `candidate_events.json`
- [x] Add quality scoring for candidate events
- [x] Mark candidates as `candidate`, `low_confidence`, or `likely_artifact`
- [x] Add tests for downloader, parser, cleaner, sentence splitter, and candidate extraction helpers
- [x] Add `main.py` workflow runner from parsed PDFs to candidate events

---

### Current Focus

- [ ] Review `candidate_events.json` quality for Gipson
- [ ] Tune obvious artifact handling without overfitting to one case
- [ ] Keep source document, page number, document role, perspective, and quality status for every candidate event
- [ ] Freeze candidate extraction once output is good enough for review
- [ ] Start date extraction and normalization

---

### Next

- [ ] Add `date_extractor.py`
- [ ] Extract raw date strings from candidate event text
- [ ] Normalize dates with `dateparser`
- [ ] Add fields: `date_raw`, `normalized_date`, `date_confidence`
- [ ] Sort candidate events into a chronology table
- [ ] Export chronology as JSON and CSV
- [ ] Add simple duplicate / near-duplicate grouping
- [ ] Add first review flags: `needs_review`, `likely_artifact`, `low_confidence`, `possible_duplicate`

---

### Later

- [ ] Add readiness flags for missing or conflicting events
- [ ] Compare complaint events vs court opinion/order events
- [ ] Flag possible date conflicts, such as suspension vs termination dates
- [ ] Add section/header detection
- [ ] Add event type classification
- [ ] Add entity extraction with spaCy
- [ ] Add optional LLM layer for event rewriting or grouping
- [ ] Add temporary upload/session flow for user-provided PDFs
- [ ] Build simple review UI
- [ ] Support exportable/printable chronology output