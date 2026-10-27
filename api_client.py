# api_client.py
# -------------
# Handles ALL communication with the Swedavia FlightInfo API v2.
# No API keys are written here — they are loaded from the .env file.
#
# Official API base URL: https://api.swedavia.se/flightinfo/v2
# Authentication:        Ocp-Apim-Subscription-Key header

import os
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

BASE_URL = "https://api.swedavia.se/flightinfo/v2"

# Read the API key from the environment (set in your .env file)
API_KEY = os.getenv("SWEDAVIA_API_KEY", "")


def _get_api_key() -> str:
    """Retrieves the API key from environment, falling back to module level."""
    return os.getenv("SWEDAVIA_API_KEY", "") or API_KEY


def _get_headers() -> dict:
    """
    Returns the HTTP headers required by the Swedavia API.
    The subscription key is loaded from the .env file, never hardcoded.
    """
    return {
        "Ocp-Apim-Subscription-Key": _get_api_key(),
        "Accept": "application/json",
    }


def _make_request(url: str, params: dict = None) -> dict | None:
    """
    Internal helper that sends a GET request to the given URL.

    Returns:
        A Python dictionary containing the parsed JSON response,
        or None if the request failed.

    This function handles common HTTP errors so that other parts
    of the app do not need to worry about networking details.
    """
    if not _get_api_key():
        print(
            "\n[ERROR] No API key found. "
            "Please create a .env file with your SWEDAVIA_API_KEY.\n"
            "See .env.example for the required format.\n"
        )
        return None

    try:
        response = requests.get(
            url,
            headers=_get_headers(),
            params=params,
            timeout=15,  # Give up if no response within 15 seconds
        )

        # Raise an exception for HTTP errors (4xx, 5xx)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        print(
            "\n[ERROR] Could not connect to the Swedavia API.\n"
            "Please check your internet connection.\n"
        )
    except requests.exceptions.Timeout:
        print(
            "\n[ERROR] The request timed out after 15 seconds.\n"
            "The Swedavia API may be slow or unavailable.\n"
        )
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            print(
                "\n[ERROR 401] Unauthorized. Your API key is invalid or missing.\n"
                "Check your SWEDAVIA_API_KEY in the .env file.\n"
            )
        elif status_code == 403:
            print(
                "\n[ERROR 403] Forbidden. You do not have access to this resource.\n"
            )
        elif status_code == 404:
            print(
                "\n[ERROR 404] Not found. The requested resource does not exist.\n"
            )
        elif status_code == 429:
            print(
                "\n[ERROR 429] Too many requests. You have exceeded your API quota.\n"
                "Please wait before making more requests.\n"
            )
        else:
            print(f"\n[ERROR {status_code}] HTTP error: {e}\n")
    except requests.exceptions.JSONDecodeError:
        print("\n[ERROR] The API returned a response that could not be read as JSON.\n")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}\n")

    return None


# -------------------------------------------------------
# Public API functions
# -------------------------------------------------------

def get_arrivals(airport_iata: str, date_str: str) -> list:
    """
    Fetches arriving flights for the given airport and date.

    Args:
        airport_iata: 3-letter IATA code, e.g. "ARN"
        date_str:     Date in YYYY-MM-DD format (UTC)

    Returns:
        A list of flight dictionaries, or an empty list on failure.
    """
    url = f"{BASE_URL}/{airport_iata.upper()}/arrivals/{date_str}"
    data = _make_request(url)

    if data is None:
        return []

    # The API wraps flights inside a "flights" key
    return data.get("flights", [])


def get_departures(airport_iata: str, date_str: str) -> list:
    """
    Fetches departing flights for the given airport and date.

    Args:
        airport_iata: 3-letter IATA code, e.g. "ARN"
        date_str:     Date in YYYY-MM-DD format (UTC)

    Returns:
        A list of flight dictionaries, or an empty list on failure.
    """
    url = f"{BASE_URL}/{airport_iata.upper()}/departures/{date_str}"
    data = _make_request(url)

    if data is None:
        return []

    return data.get("flights", [])


def search_flight(airport_iata: str, date_str: str, flight_id: str,
                  flight_type: str = "A") -> list:
    """
    Searches for a specific flight using the OData query endpoint.

    The Swedavia API does not have a dedicated "search by flight number"
    endpoint, so we use the /query endpoint with OData filters.

    Args:
        airport_iata: 3-letter IATA code, e.g. "ARN"
        date_str:     Date in YYYY-MM-DD format
        flight_id:    Flight number, e.g. "SK142"
        flight_type:  "A" for arrival, "D" for departure

    Returns:
        A list of matching flight dictionaries.
    """
    # Build the OData filter string
    odata_filter = (
        f"airport eq '{airport_iata.upper()}' and "
        f"scheduled eq '{date_str}' and "
        f"flightType eq '{flight_type}' and "
        f"flightId eq '{flight_id.upper()}'"
    )

    url = f"{BASE_URL}/query"
    data = _make_request(url, params={"filter": odata_filter})

    if data is None:
        return []

    return data.get("flights", [])


def run_odata_query(odata_filter: str) -> list:
    """
    Sends a raw OData filter query to the /query endpoint.

    This is the "advanced query" feature that lets users write
    their own OData filter expressions.

    Supported OData fields (from the official API documentation):
        airport      — 3-letter IATA code   e.g. airport eq 'ARN'
        flightType   — 'A' or 'D'           e.g. flightType eq 'A'
        scheduled    — date YYYY-MM-DD       e.g. scheduled eq '2026-10-26'
        flightId     — flight number         e.g. flightId eq 'SK142'

    Supported OData operators:
        eq           — equals
        and          — combine conditions

    Returns:
        A list of flight dictionaries, or an empty list on failure.
    """
    url = f"{BASE_URL}/query"
    data = _make_request(url, params={"filter": odata_filter})

    if data is None:
        return []

    return data.get("flights", [])


def check_heartbeat(airport_iata: str = "ARN") -> bool:
    """
    Checks whether the Swedavia API is reachable by fetching
    today's arrivals for a known airport. If the request succeeds
    (even if there are zero flights), the API is considered online.

    We use the arrivals endpoint because the API does not document
    a dedicated health/ping endpoint. This is the safest real
    documented endpoint to use for a connectivity check.

    Args:
        airport_iata: Airport to use for the test (default: ARN)

    Returns:
        True if the API responded successfully, False otherwise.
    """
    from time_utils import today_utc

    url = f"{BASE_URL}/{airport_iata.upper()}/arrivals/{today_utc()}"

    try:
        response = requests.get(
            url,
            headers=_get_headers(),
            timeout=10,
        )
        # Any 2xx response means the API is reachable
        return response.status_code == 200

    except Exception:
        return False
