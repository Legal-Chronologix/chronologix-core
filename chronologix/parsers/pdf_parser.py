import json
import uuid
from pathlib import Path

import pymupdf

from chronologix.preprocessing.text_cleaner import clean_extracted_text
from chronologix.utils.file_downloader import slugify_filename


class PDFParser:
    """
    Parse PDF files into page-level text models.

    Responsibility:
    - read PDF files
    - extract raw text by page
    - clean extracted text
    - save extracted text models as JSON

    This class does not extract events. Event extraction should happen later
    in a separate extractor.
    """

    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_by_page(self, filepath: str | Path, filetype: str = "pdf") -> dict:
        """
        Extract text from one PDF page by page.

        Returns:
            A document model containing metadata and page-level text.
        """
        filepath = Path(filepath)
        doc = pymupdf.open(filepath, filetype=filetype)

        model = {
            "doc_id": str(uuid.uuid4()),
            "doc_name": filepath.name,
            "filepath": str(filepath),
            "filetype": filetype,
            "pages": [],
        }

        for page_number, page in enumerate(doc, start=1):
            raw_text = page.get_text()
            clean_text = clean_extracted_text(raw_text)

            page_data = {
                "page_number": page_number,
                "raw_text": raw_text,
                "clean_text": clean_text,
            }

            model["pages"].append(page_data)

        doc.close()

        return model

    def save_text_model(self, text_model: dict, output_path: str | Path) -> Path:
        """
        Save a parsed document text model as JSON.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(text_model, file, indent=2, ensure_ascii=False)

        return output_path

    def output_path_for_pdf(self, pdf_path: str | Path) -> Path:
        """
        Build a JSON output path for one PDF.

        Example:
        104_summary_judgment.pdf
        ->
        extracted_text/104_summary_judgment.json
        """
        pdf_path = Path(pdf_path)
        filename = slugify_filename(pdf_path.stem)

        return self.output_dir / f"{filename}.json"

    def parse_pdf(self, pdf_path: str | Path) -> Path:
        """
        Parse one PDF and save its extracted text model as JSON.

        Returns:
            Path to the saved JSON file.
        """
        text_model = self.extract_text_by_page(pdf_path)
        output_path = self.output_path_for_pdf(pdf_path)

        return self.save_text_model(text_model, output_path)

    def parse_directory(self, pdf_dir: str | Path) -> list[Path]:
        """
        Parse all PDF files in a directory.

        Returns:
            A list of saved JSON paths.
        """
        pdf_dir = Path(pdf_dir)
        saved_paths = []

        for pdf_path in sorted(pdf_dir.glob("*.pdf")):
            saved_path = self.parse_pdf(pdf_path)
            saved_paths.append(saved_path)
            print("Saved:", saved_path)

        return saved_paths


# if __name__ == "__main__":
#     parser = PDFParser(
#         output_dir="./data/court_listener/gipson/extracted_text"
#     )

#     saved_paths = parser.parse_directory(
#         "./data/court_listener/gipson/pdfs"
#     )

#     print("Parsed PDFs:", len(saved_paths))
