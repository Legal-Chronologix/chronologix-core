from unittest.mock import Mock

from chronologix.utils.RECAP_downloader import download_file, guess_extension


def test_guess_extension_from_pdf_content_type():
    response = Mock()
    response.headers = {"content-type": "application/pdf"}

    extension = guess_extension(response)

    assert extension == ".pdf"


def test_guess_extension_with_charset():
    response = Mock()
    response.headers = {"content-type": "text/plain; charset=utf-8"}

    extension = guess_extension(response)

    assert extension == ".txt"


def test_guess_extension_fallback_when_missing_content_type():
    response = Mock()
    response.headers = {}

    extension = guess_extension(response)

    assert extension == ".bin"


def test_download_file_saves_content(tmp_path, monkeypatch):
    fake_response = Mock()
    fake_response.ok = True
    fake_response.content = b"%PDF fake pdf content"
    fake_response.headers = {"content-type": "application/pdf"}

    mock_get = Mock(return_value=fake_response)

    monkeypatch.setattr(
        "chronologix.utils.file_downloader.requests.get",
        mock_get,
    )

    output_path = download_file(
        filename="test_document",
        url="https://example.com/test.pdf",
        output_dir=tmp_path,
        extension=".pdf",
    )
    assert output_path == tmp_path / "test_document.pdf"
    assert output_path.exists()
    assert output_path.read_bytes() == b"%PDF fake pdf content"

    mock_get.assert_called_once_with(
        "https://example.com/test.pdf",
        headers=None,
        timeout=30,
    )


def test_download_file_returns_none_on_failed_request(tmp_path, monkeypatch):
    fake_response = Mock()
    fake_response.ok = False
    fake_response.status_code = 404
    fake_response.text = "Not found"

    mock_get = Mock(return_value=fake_response)

    monkeypatch.setattr(
        "chronologix.utils.file_downloader.requests.get",
        mock_get,
    )

    output_path = download_file(
        filename="missing_document",
        url="https://example.com/missing.pdf",
        output_dir=tmp_path,
        extension=".pdf",
    )

    assert output_path is None
    assert not (tmp_path / "missing_document.pdf").exists()
