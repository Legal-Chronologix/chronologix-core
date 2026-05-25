# chronologix
A legal-tech MVP that extracts source-linked timelines from public litigation documents and flags missing or conflicting events.

## Note
The current MVP is not trying to model every litigation chronology workflow. It starts with one small employment-dispute RECAP case to prove the technical spine: document ingestion, PDF parsing, page-level provenance, and candidate event extraction.

## TODO

### Done

- [x] Define Chronologix use case: source-linked chronology readiness
- [x] Use CourtListener / RECAP as first data source
- [x] Build CourtListener client for RECAP metadata
- [x] Handle pagination and rate limits
- [x] Filter available documents
- [x] Download available PDFs
- [x] Add generic file downloader
- [x] Add CourtListener-specific downloader
- [x] Download Gipson MVP document packet
- [x] Start PDF parser
- [x] Extract PDF text by page
- [x] Add text cleaner
- [x] Add sentence/date extraction starter
- [x] Add tests for downloader, parser, cleaner, and sentence splitter

### Current focus

- [ ] Finish parsing all Gipson PDFs into JSON
- [ ] Save extracted text to `data/court_listener/gipson/extracted_text/`
- [ ] Create first `candidate_events.json`
- [ ] Extract date-containing sentences from `1_complaint.pdf`
- [ ] Keep source document and page number for every candidate event

### Next

- [ ] Add `date_extractor.py`
- [ ] Normalize dates with `dateparser`
- [ ] Add simple document role detection
- [ ] Add basic event fields: date, event text, source doc, page, status
- [ ] Export candidate events as CSV or JSON table

### Later

- [ ] Add readiness flags
- [ ] Add section/header detection
- [ ] Add entity extraction with spaCy
- [ ] Compare complaint events vs opinion events
- [ ] Build simple review UI