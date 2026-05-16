from unittest.mock import Mock

from chronologix.parsers.pdf_parser import extract_text_by_page


def test_extract_text_by_page(monkeypatch, tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"fake pdf content")

    fake_page_1 = Mock()
    fake_page_1.get_text.return_value = "Page one text"

    fake_page_2 = Mock()
    fake_page_2.get_text.return_value = "Page two text"

    fake_doc = Mock()
    fake_doc.__iter__ = Mock(return_value=iter([fake_page_1, fake_page_2]))
    fake_doc.close = Mock()

    mock_open = Mock(return_value=fake_doc)

    mock_clean = Mock(side_effect=lambda text: f"cleaned: {text}")

    monkeypatch.setattr(
        "chronologix.parsers.pdf_parser.pymupdf.open",
        mock_open,
    )
    monkeypatch.setattr(
        "chronologix.parsers.pdf_parser.clean_extracted_text",
        mock_clean,
    )

    result = extract_text_by_page(pdf_path)

    assert result["doc_name"] == "sample.pdf"
    assert result["filepath"] == str(pdf_path)
    assert result["filetype"] == "pdf"
    assert "doc_id" in result

    assert result["pages"] == [
        {
            "page_number": 1,
            "raw_text": "Page one text",
            "clean_text": "cleaned: Page one text",
        },
        {
            "page_number": 2,
            "raw_text": "Page two text",
            "clean_text": "cleaned: Page two text",
        },
    ]

    mock_open.assert_called_once_with(pdf_path, filetype="pdf")
    assert mock_clean.call_count == 2
    fake_doc.close.assert_called_once()
