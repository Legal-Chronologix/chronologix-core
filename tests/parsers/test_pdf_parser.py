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

    monkeypatch.setattr(
        "chronologix.parsers.pdf_parser.pymupdf.open",
        mock_open,
    )

    result = extract_text_by_page(pdf_path)

    assert result["doc_name"] == "sample.pdf"
    assert result["filepath"] == str(pdf_path)
    assert result["filetype"] == "pdf"
    assert "doc_id" in result

    assert result["pages"] == [
        {
            "page_number": 1,
            "text": "Page one text",
        },
        {
            "page_number": 2,
            "text": "Page two text",
        },
    ]

    mock_open.assert_called_once_with(pdf_path, filetype="pdf")
    fake_doc.close.assert_called_once()
