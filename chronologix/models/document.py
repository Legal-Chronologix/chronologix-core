from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4


@dataclass
class Document:
    doc_name: str
    filepath: Path
    source: str
    filetype: str = "pdf"
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    source_doc_id: str | None = None
    metadata: dict = field(default_factory=dict)
