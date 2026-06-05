from pathlib import Path
from typing import Any

from chronologix.workflow.base import Workflow
from chronologix.steps.demo_gipson_case_steps import LoadCourtListenerDocumentsStep, ParsePDFsStep, BuildCandidateEventsStep, FlagReadinessStep

def build_gipson_context() -> dict[str, Any]:
    """
    Build path config for the local Gipson demo case.
    """
    case_dir = Path("data/court_listener/gipson")

    return {
        "case_dir": case_dir,
        "available_docs_path": case_dir / "available_docs.json",
        "pdf_dir": case_dir / "pdfs",
        "extracted_text_dir": case_dir / "extracted_text",
        "candidate_events_path": case_dir / "candidate_events.json",
        "flagged_events_path": case_dir / "flagged_events.json",
    }


def build_gipson_workflow() -> Workflow:
    """
    Build the current Gipson MVP workflow.
    """
    return Workflow(
        steps=[
            LoadCourtListenerDocumentsStep(),
            ParsePDFsStep(),
            BuildCandidateEventsStep(),
            FlagReadinessStep(),
        ]
    )


def run_gipson_workflow() -> dict[str, Any]:
    """
    Run the full local Gipson demo workflow.
    """
    context = build_gipson_context()
    workflow = build_gipson_workflow()

    return workflow.run(context)


# if __name__ == "__main__":
#     run_gipson_workflow()