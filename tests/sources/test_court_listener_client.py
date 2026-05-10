from unittest.mock import Mock

from chronologix.sources import CourtListenerClient


def make_response(status_code=200, payload=None, text="", headers=None):
    response = Mock()
    response.status_code = status_code
    response.ok = 200 <= status_code < 300
    response.text = text
    response.headers = headers or {}
    response.json.return_value = payload or {}
    return response


def test_get_success(monkeypatch):
    fake_response = make_response(
        payload={
            "results": [{"id": 1}],
            "next": None,
        }
    )

    mock_get = Mock(return_value=fake_response)

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.requests.get",
        mock_get,
    )

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.get_courtlistener_headers",
        Mock(return_value={"Authorization": "Token fake-token"}),
    )

    client = CourtListenerClient()

    data = client.get(
        "/search/",
        params={"type": "rd", "q": "docket_id:59684707"},
    )

    assert data == {
        "results": [{"id": 1}],
        "next": None,
    }

    mock_get.assert_called_once_with(
        "https://www.courtlistener.com/api/rest/v4/search/",
        headers={"Authorization": "Token fake-token"},
        params={"type": "rd", "q": "docket_id:59684707"},
        timeout=30,
    )


def test_get_retries_after_rate_limit(monkeypatch):
    rate_limited_response = make_response(
        status_code=429,
        text='{"detail": "rate limited"}',
        headers={"Retry-After": "1"},
    )

    success_response = make_response(
        status_code=200,
        payload={"results": [{"id": 123}], "next": None},
    )

    mock_get = Mock(
        side_effect=[
            rate_limited_response,
            success_response,
        ]
    )

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.requests.get",
        mock_get,
    )

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.time.sleep",
        Mock(),
    )

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.get_courtlistener_headers",
        Mock(return_value={"Authorization": "Token fake-token"}),
    )

    client = CourtListenerClient()
    data = client.get("/search/")


def test_get_raises_runtime_error_on_failure(monkeypatch):
    runtime_error_response = make_response(
        status_code=500,
        text="Server error",
    )

    mock_get = Mock(return_value=runtime_error_response)
    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.requests.get",
        mock_get,
    )

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.get_courtlistener_headers",
        Mock(return_value={"Authorization": "Token fake-token"}),
    )

    client = CourtListenerClient()

    try:
        client.get("/search/")
        assert False, "Expected RuntimeError"
    except RuntimeError as error:
        assert "CourtListener request failed" in str(error)
        assert "500" in str(error)



def test_fetch_recap_documents_for_docket_single_page(monkeypatch):
    first_page = {
        "results": [
            {"id": 1, "is_available": True},
            {"id": 2, "is_available": False},
        ],
        "next": None,
    }

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.get_courtlistener_headers",
        Mock(return_value={"Authorization": "Token fake-token"}),
    )

    client = CourtListenerClient()
    client.get = Mock(return_value=first_page)
    docs = client.fetch_recap_documents_for_docket_id(59684707)
    assert docs == [
        {"id": 1, "is_available": True},
        {"id": 2, "is_available": False},
    ]

    client.get.assert_called_once_with(
        "/search/",
        params={
            "type": "rd",
            "q": "docket_id:59684707",
        },
    )


def test_fetch_recap_documents_only_available(monkeypatch):
    first_page = {
        "results": [
            {"id": 1, "is_available": True},
            {"id": 2, "is_available": False},
        ],
        "next": None,
    }

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.get_courtlistener_headers",
        Mock(return_value={"Authorization": "Token fake-token"}),
    )

    client = CourtListenerClient()
    client.get = Mock(return_value=first_page)

    docs = client.fetch_recap_documents_for_docket_id(
        docket_id=59684707,
        only_available=True,
    )

    assert docs == [
        {"id": 1, "is_available": True},
    ]


def test_fetch_recap_documents_with_pagination(monkeypatch):
    first_page = {
        "results": [{"id": 1, "is_available": True}],
        "next": "https://www.courtlistener.com/api/rest/v4/search/?cursor=abc",
    }

    second_page = {
        "results": [{"id": 2, "is_available": True}],
        "next": None,
    }

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.get_courtlistener_headers",
        Mock(return_value={"Authorization": "Token fake-token"}),
    )

    monkeypatch.setattr(
        "chronologix.sources.court_listener.client.time.sleep",
        Mock(),
    )

    client = CourtListenerClient()
    client.get = Mock(return_value=first_page)
    client.get_full_url = Mock(return_value=second_page)

    docs = client.fetch_recap_documents_for_docket_id(59684707)
    assert docs == [
        {"id": 1, "is_available": True},
        {"id": 2, "is_available": True},
    ]

    client.get_full_url.assert_called_once_with(
        "https://www.courtlistener.com/api/rest/v4/search/?cursor=abc"
    )