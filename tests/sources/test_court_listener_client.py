from unittest.mock import Mock

from chronologix.sources.court_listener.client import CourtListenerClient


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
