import requests

from chronologix.configs.court_listener import (
    COURTLISTENER_BASE_URL,
    COURTLISTENER_TOKEN,
)

headers = {
    "Authorization": f"Token {COURTLISTENER_TOKEN}",
    "Accept": "application/json",
}

docket_id = 59684707

url = f"{COURTLISTENER_BASE_URL}/dockets/{docket_id}/"

response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()

data = response.json()

important_fields = {
    "id": data.get("id"),
    "case_name": data.get("case_name"),
    "docket_number": data.get("docket_number"),
    "docket_number_core": data.get("docket_number_core"),
    "pacer_case_id": data.get("pacer_case_id"),
    "court_id": data.get("court_id"),
    "date_filed": data.get("date_filed"),
    "date_terminated": data.get("date_terminated"),
    "date_last_filing": data.get("date_last_filing"),
    "nature_of_suit": data.get("nature_of_suit"),
    "cause": data.get("cause"),
    "absolute_url": data.get("absolute_url"),
}

print(important_fields)
