"""
gipson_workflow.py

Local demo workflow for the Gipson MVP case.

This is intentionally case-specific for now.
Later, this can become a generic case workflow that receives paths from
a CLI, config file, or upload session.
"""

from typing import Any

from chronologix.tools.extractors.candidate_events_extractor import (
    build_candidate_events,
)
from chronologix.tools.parsers.pdf_parser import PDFParser
from chronologix.tools.review.readiness_flags import flag_candidate_events_file
from chronologix.sources.court_listener.document_mapper import (
    load_documents_from_available_docs,
)
from chronologix.workflow.base import WorkflowStep


class LoadCourtListenerDocumentsStep(WorkflowStep):
    """
    Load CourtListener metadata and convert it into generic Document objects.
    """

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        documents = load_documents_from_available_docs(
            available_docs_path=context["available_docs_path"],
            pdf_dir=context["pdf_dir"],
        )

        context["documents"] = documents
        print(f"Loaded {len(documents)} documents.")

        return context


class ParsePDFsStep(WorkflowStep):
    """
    Parse PDFs into page-level extracted_text JSON files.
    """

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        parser = PDFParser(output_dir=context["extracted_text_dir"])

        parsed_paths = parser.parse_documents(context["documents"])

        context["parsed_paths"] = parsed_paths
        print(f"Parsed {len(parsed_paths)} PDFs.")

        return context


class BuildCandidateEventsStep(WorkflowStep):
    """
    Build source-linked candidate event sentences.
    """

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        events = build_candidate_events(
            input_dir=context["extracted_text_dir"],
            output_path=context["candidate_events_path"],
        )

        context["candidate_events"] = events
        print(f"Candidate events: {len(events)}")

        return context


class FlagReadinessStep(WorkflowStep):
    """
    Normalize dates, group events by date, and create review/readiness flags.
    """

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        flagged_events = flag_candidate_events_file(
            input_path=context["candidate_events_path"],
            output_path=context["flagged_events_path"],
        )

        context["flagged_events"] = flagged_events

        return context