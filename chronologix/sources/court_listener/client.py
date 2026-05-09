import json
import time
from pathlib import Path

import requests

from chronologix.configs.court_listener import (
    COURTLISTENER_BASE_URL,
    get_courtlistener_headers,
)


class CourtListenerClient:
    """
    REST API client for CourtListener.

    Handles:
    - base URL
    - auth headers
    - GET requests
    - pagination
    - simple rate-limit handling
    """

    def __init__(self, base_url=COURTLISTENER_BASE_URL, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = get_courtlistener_headers()

    def get(self, path, params=None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self.get_full_url(url, params=params)

    def get_full_url(self, url, params=None):
        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=self.timeout,
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Sleeping for {retry_after} seconds...")
            time.sleep(retry_after)

            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout,
            )

        if not response.ok:
            raise RuntimeError(
                f"CourtListener request failed: "
                f"{response.status_code} {response.text[:300]}"
            )

        return response.json()

    def fetch_recap_documents_for_docket_id(self, docket_id, only_available=False):
        """
        Fetch RECAP document metadata for one docket.

        If only_available=True, keep only documents where is_available is True.
        """
        docs = []

        data = self.get(
            "/search/",
            params={
                "type": "rd",
                "q": f"docket_id:{docket_id}",
            },
        )

        page_docs = data.get("results", [])

        if only_available:
            page_docs = [
                doc for doc in page_docs
                if doc.get("is_available") is True
            ]

        docs.extend(page_docs)
        next_url = data.get("next")

        while next_url:
            time.sleep(13)

            data = self.get_full_url(next_url)
            page_docs = data.get("results", [])

            if only_available:
                page_docs = [
                    doc for doc in page_docs
                    if doc.get("is_available") is True
                ]

            docs.extend(page_docs)
            next_url = data.get("next")

            print("Fetched kept docs so far:", len(docs))

        return docs


if __name__ == "__main__":
    client = CourtListenerClient()

    docs = client.fetch_recap_documents_for_docket_id(
        docket_id=59684707,
        only_available=True,
    )

    output_path = Path("data/court_listener/gipson/available_docs.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as file:
        json.dump(docs, file, indent=2)

    print("Saved:", output_path)
    print("Available docs:", len(docs))