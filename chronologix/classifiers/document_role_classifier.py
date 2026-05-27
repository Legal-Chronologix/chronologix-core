import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentRoleResult:
    role: str
    perspective: str
    confidence: str
    matched_signals: list[str]


ROLE_RULES = [
    {
        "role": "court_opinion",
        "perspective": "court",
        "signals": [
            "opinion and order",
            "opinion & order",
            "for the reasons set forth below",
            "enter final judgment",
            "motions for summary judgment are granted",
        ],
    },
    {
        "role": "court_recommendation",
        "perspective": "court",
        "signals": [
            "report and recommendation",
            "report and recommendations",
            "findings, report and recommendation",
            "magistrate judge",
        ],
    },
    {
        "role": "motion_summary_judgment",
        "perspective": "party",
        "signals": [
            "motion for summary judgment",
            "moves for summary judgment",
            "summary judgment",
            "wherefore, defendant",
        ],
    },
    {
        "role": "admin_disclosure",
        "perspective": "admin",
        "signals": [
            "corporate disclosure statement",
            "federal rule of civil procedure 7.1",
            "no insurance carrier",
        ],
    },
    {
        "role": "complaint",
        "perspective": "plaintiff",
        "signals": [
            "complaint",
            "factual allegations",
            "wherefore, the plaintiff requests",
        ],
    },
    {
        "role": "court_order",
        "perspective": "court",
        "signals": [
            "order",
            "so ordered",
            "the court adopts",
            "the court orders",
        ],
    },
]


def get_first_pages_text(text_model: dict, max_pages: int = 2) -> str:
    pages = text_model.get("pages", [])[:max_pages]

    return " ".join(
        page.get("clean_text", "")
        for page in pages
    )


def get_metadata_text(text_model: dict) -> str:
    metadata = text_model.get("metadata", {})

    return " ".join(
        str(value)
        for value in metadata.values()
        if value is not None
    )


def infer_document_role(text_model: dict) -> DocumentRoleResult:
    """
    Infer document role from filename, metadata, and extracted text.

    This is source-agnostic. CourtListener metadata helps when available,
    but user-uploaded PDFs can still be classified using first-page text.
    """
    doc_name = text_model.get("doc_name", "")

    combined_text = " ".join(
        [
            doc_name,
            get_metadata_text(text_model),
            get_first_pages_text(text_model),
        ]
    ).lower()

    best_rule = None
    best_signals = []

    for rule in ROLE_RULES:
        matched_signals = [
            signal
            for signal in rule["signals"]
            if signal in combined_text
        ]

        if len(matched_signals) > len(best_signals):
            best_rule = rule
            best_signals = matched_signals

    if best_rule is None:
        return DocumentRoleResult(
            role="unknown",
            perspective="unknown",
            confidence="low",
            matched_signals=[],
        )

    confidence = "high" if len(best_signals) >= 2 else "medium"

    return DocumentRoleResult(
        role=best_rule["role"],
        perspective=best_rule["perspective"],
        confidence=confidence,
        matched_signals=best_signals,
    )


def infer_role_from_json_file(json_path: str | Path) -> DocumentRoleResult:
    json_path = Path(json_path)
    text_model = json.loads(json_path.read_text(encoding="utf-8"))

    return infer_document_role(text_model)


def infer_roles_from_directory(input_dir: str | Path) -> list[dict]:
    input_dir = Path(input_dir)
    results = []

    for json_path in sorted(input_dir.glob("*.json")):
        role_result = infer_role_from_json_file(json_path)

        results.append(
            {
                "file": json_path.name,
                "role": role_result.role,
                "perspective": role_result.perspective,
                "confidence": role_result.confidence,
                "matched_signals": role_result.matched_signals,
            }
        )

    return results


# if __name__ == "__main__":
#     input_dir = Path("data/court_listener/gipson/extracted_text")

#     results = infer_roles_from_directory(input_dir)

#     for result in results:
#         print("-----")
#         print("file:", result["file"])
#         print("role:", result["role"])
#         print("perspective:", result["perspective"])
#         print("confidence:", result["confidence"])
#         print("signals:", result["matched_signals"])
