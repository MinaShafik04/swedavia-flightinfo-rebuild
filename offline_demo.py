# offline_demo.py
# ---------------
# OFFLINE DEMO MODE — Swedavia FlightInfo Rebuild
#
# This module runs a full interactive demo using SAMPLE DATA ONLY.
# It does NOT connect to the internet, does NOT require an API key,
# and does NOT represent real or live flight information.
#
# Every screen clearly labels data as "[SAMPLE DATA — NOT LIVE]"
# so there is no risk of confusing it with real flight information.
#
# Features demonstrated:
#   1. Airport selection
#   2. Arrivals (with pagination)
#   3. Departures (with pagination)
#   4. Flight search by flight number
#   5. OData-style query concept (filtered from sample data)

import time
from colorama import Fore, Style

from display import (
    print_header, print_info, print_success, print_warning,
    show_arrivals, show_departures, show_flight_detail,
    show_query_results, clear_screen,
)
from airports import get_airport_name

# -------------------------------------------------------
# Sample data — clearly fictional, for demonstration only
# -------------------------------------------------------
# All times are UTC strings (same format the real API uses).
# The display layer converts them to Swedish local time, just
# like it does for real API data.

SAMPLE_DATE = "2026-10-26"

# 16 sample arrivals — enough to demonstrate TWO pages of pagination
SAMPLE_ARRIVALS = [
    {
        "flightId": "SK142",
        "flightType": "A",
        "airlineOperator": {"iata": "SK", "name": "SAS Scandinavian Airlines"},
        "locationAndTerminal": {"airportCode": "CPH"},
        "scheduledUtc": "2026-10-26T06:00:00Z",
        "estimatedUtc": "2026-10-26T06:05:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "arrivalTerminal": "5",
        "gate": "A14",
        "baggageClaimUnit": "4",
        "viaDestinations": [],
    },
    {
        "flightId": "LH784",
        "flightType": "A",
        "airlineOperator": {"iata": "LH", "name": "Lufthansa"},
        "locationAndTerminal": {"airportCode": "FRA"},
        "scheduledUtc": "2026-10-26T07:15:00Z",
        "estimatedUtc": "2026-10-26T07:30:00Z",
        "actualUtc":    "",
        "flightLegStatus": "DEL",
        "arrivalTerminal": "5",
        "gate": "F22",
        "baggageClaimUnit": "6",
        "viaDestinations": [],
    },
    {
        "flightId": "BA782",
        "flightType": "A",
        "airlineOperator": {"iata": "BA", "name": "British Airways"},
        "locationAndTerminal": {"airportCode": "LHR"},
        "scheduledUtc": "2026-10-26T08:30:00Z",
        "estimatedUtc": "2026-10-26T08:30:00Z",
        "actualUtc":    "2026-10-26T08:28:00Z",
        "flightLegStatus": "LAN",
        "arrivalTerminal": "5",
        "gate": "D7",
        "baggageClaimUnit": "2",
        "viaDestinations": [],
    },
    {
        "flightId": "AY666",
        "flightType": "A",
        "airlineOperator": {"iata": "AY", "name": "Finnair"},
        "locationAndTerminal": {"airportCode": "HEL"},
        "scheduledUtc": "2026-10-26T09:00:00Z",
        "estimatedUtc": "2026-10-26T09:00:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "arrivalTerminal": "5",
        "gate": "C3",
        "baggageClaimUnit": "1",
        "viaDestinations": [],
    },
    {
        "flightId": "FR1234",
        "flightType": "A",
        "airlineOperator": {"iata": "FR", "name": "Ryanair"},
        "locationAndTerminal": {"airportCode": "STN"},
        "scheduledUtc": "2026-10-26T09:45:00Z",
        "estimatedUtc": "2026-10-26T09:45:00Z",
        "actualUtc":    "",
        "flightLegStatus": "FPL",
        "arrivalTerminal": "2",
        "gate": "B1",
        "baggageClaimUnit": "8",
        "viaDestinations": [],
    },
    {
        "flightId": "DY456",
        "flightType": "A",
        "airlineOperator": {"iata": "DY", "name": "Norwegian"},
        "locationAndTerminal": {"airportCode": "OSL"},
        "scheduledUtc": "2026-10-26T10:10:00Z",
        "estimatedUtc": "2026-10-26T10:10:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "arrivalTerminal": "5",
        "gate": "E9",
        "baggageClaimUnit": "3",
        "viaDestinations": [],
    },
    {
        "flightId": "KL1231",
        "flightType": "A",
        "airlineOperator": {"iata": "KL", "name": "KLM"},
        "locationAndTerminal": {"airportCode": "AMS"},
        "scheduledUtc": "2026-10-26T10:55:00Z",
        "estimatedUtc": "2026-10-26T10:55:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SEQ",
        "arrivalTerminal": "5",
        "gate": "G18",
        "baggageClaimUnit": "5",
        "viaDestinations": [],
    },
    {
        "flightId": "AF1184",
        "flightType": "A",
        "airlineOperator": {"iata": "AF", "name": "Air France"},
        "locationAndTerminal": {"airportCode": "CDG"},
        "scheduledUtc": "2026-10-26T11:20:00Z",
        "estimatedUtc": "2026-10-26T11:35:00Z",
        "actualUtc":    "",
        "flightLegStatus": "DEL",
        "arrivalTerminal": "5",
        "gate": "F31",
        "baggageClaimUnit": "7",
        "viaDestinations": [],
    },
    {
        "flightId": "TK1759",
        "flightType": "A",
        "airlineOperator": {"iata": "TK", "name": "Turkish Airlines"},
        "locationAndTerminal": {"airportCode": "IST"},
        "scheduledUtc": "2026-10-26T12:00:00Z",
        "estimatedUtc": "2026-10-26T12:00:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "arrivalTerminal": "5",
        "gate": "H5",
        "baggageClaimUnit": "9",
        "viaDestinations": [],
    },
    {
        "flightId": "EW4289",
        "flightType": "A",
        "airlineOperator": {"iata": "EW", "name": "Eurowings"},
        "locationAndTerminal": {"airportCode": "DUS"},
        "scheduledUtc": "2026-10-26T12:45:00Z",
        "estimatedUtc": "2026-10-26T12:45:00Z",
        "actualUtc":    "",
        "flightLegStatus": "FLS",
        "arrivalTerminal": "5",
        "gate": "A2",
        "baggageClaimUnit": "2",
        "viaDestinations": [],
    },
    {
        "flightId": "OS551",
        "flightType": "A",
        "airlineOperator": {"iata": "OS", "name": "Austrian Airlines"},
        "locationAndTerminal": {"airportCode": "VIE"},
        "scheduledUtc": "2026-10-26T13:30:00Z",
        "estimatedUtc": "2026-10-26T13:30:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "arrivalTerminal": "5",
        "gate": "D14",
        "baggageClaimUnit": "4",
        "viaDestinations": [],
    },
    {
        "flightId": "SK1402",
        "flightType": "A",
        "airlineOperator": {"iata": "SK", "name": "SAS Scandinavian Airlines"},
        "locationAndTerminal": {"airportCode": "BGO"},
        "scheduledUtc": "2026-10-26T14:05:00Z",
        "estimatedUtc": "2026-10-26T14:05:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "arrivalTerminal": "5",
        "gate": "C11",
        "baggageClaimUnit": "3",
        "viaDestinations": [],
    },
    {
        "flightId": "W63301",
        "flightType": "A",
        "airlineOperator": {"iata": "W6", "name": "Wizz Air"},
        "locationAndTerminal": {"airportCode": "WAW"},
        "scheduledUtc": "2026-10-26T14:50:00Z",
        "estimatedUtc": "2026-10-26T15:10:00Z",
        "actualUtc":    "",
        "flightLegStatus": "DEL",
        "arrivalTerminal": "2",
        "gate": "B5",
        "baggageClaimUnit": "8",
        "viaDestinations": [],
    },
    {
        "flightId": "SN2283",
        "flightType": "A",
        "airlineOperator": {"iata": "SN", "name": "Brussels Airlines"},
        "locationAndTerminal": {"airportCode": "BRU"},
        "scheduledUtc": "2026-10-26T15:20:00Z",
        "estimatedUtc": "2026-10-26T15:20:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "arrivalTerminal": "5",
        "gate": "G2",
        "baggageClaimUnit": "5",
        "viaDestinations": [],
    },
    {
        "flightId": "IB3170",
        "flightType": "A",
        "airlineOperator": {"iata": "IB", "name": "Iberia"},
        "locationAndTerminal": {"airportCode": "MAD"},
        "scheduledUtc": "2026-10-26T16:00:00Z",
        "estimatedUtc": "2026-10-26T16:00:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "arrivalTerminal": "5",
        "gate": "F8",
        "baggageClaimUnit": "6",
        "viaDestinations": [],
    },
    {
        "flightId": "VY1830",
        "flightType": "A",
        "airlineOperator": {"iata": "VY", "name": "Vueling"},
        "locationAndTerminal": {"airportCode": "BCN"},
        "scheduledUtc": "2026-10-26T17:10:00Z",
        "estimatedUtc": "2026-10-26T17:10:00Z",
        "actualUtc":    "",
        "flightLegStatus": "CAN",
        "arrivalTerminal": "5",
        "gate": "",
        "baggageClaimUnit": "",
        "viaDestinations": [],
    },
]

# 14 sample departures — enough to demonstrate pagination
SAMPLE_DEPARTURES = [
    {
        "flightId": "SK143",
        "flightType": "D",
        "airlineOperator": {"iata": "SK", "name": "SAS Scandinavian Airlines"},
        "locationAndTerminal": {"airportCode": "CPH"},
        "scheduledUtc": "2026-10-26T06:30:00Z",
        "estimatedUtc": "2026-10-26T06:30:00Z",
        "actualUtc":    "2026-10-26T06:28:00Z",
        "flightLegStatus": "ACT",
        "departureTerminal": "5",
        "gate": "A14",
        "checkIn": "D",
        "viaDestinations": [],
    },
    {
        "flightId": "LH785",
        "flightType": "D",
        "airlineOperator": {"iata": "LH", "name": "Lufthansa"},
        "locationAndTerminal": {"airportCode": "FRA"},
        "scheduledUtc": "2026-10-26T07:45:00Z",
        "estimatedUtc": "2026-10-26T07:45:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "5",
        "gate": "F22",
        "checkIn": "E",
        "viaDestinations": [],
    },
    {
        "flightId": "BA783",
        "flightType": "D",
        "airlineOperator": {"iata": "BA", "name": "British Airways"},
        "locationAndTerminal": {"airportCode": "LHR"},
        "scheduledUtc": "2026-10-26T08:00:00Z",
        "estimatedUtc": "2026-10-26T08:00:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "5",
        "gate": "D7",
        "checkIn": "C",
        "viaDestinations": [],
    },
    {
        "flightId": "AY667",
        "flightType": "D",
        "airlineOperator": {"iata": "AY", "name": "Finnair"},
        "locationAndTerminal": {"airportCode": "HEL"},
        "scheduledUtc": "2026-10-26T09:30:00Z",
        "estimatedUtc": "2026-10-26T09:45:00Z",
        "actualUtc":    "",
        "flightLegStatus": "DEL",
        "departureTerminal": "5",
        "gate": "C3",
        "checkIn": "F",
        "viaDestinations": [],
    },
    {
        "flightId": "FR1235",
        "flightType": "D",
        "airlineOperator": {"iata": "FR", "name": "Ryanair"},
        "locationAndTerminal": {"airportCode": "STN"},
        "scheduledUtc": "2026-10-26T10:15:00Z",
        "estimatedUtc": "2026-10-26T10:15:00Z",
        "actualUtc":    "",
        "flightLegStatus": "FPL",
        "departureTerminal": "2",
        "gate": "B1",
        "checkIn": "A",
        "viaDestinations": [],
    },
    {
        "flightId": "DY457",
        "flightType": "D",
        "airlineOperator": {"iata": "DY", "name": "Norwegian"},
        "locationAndTerminal": {"airportCode": "OSL"},
        "scheduledUtc": "2026-10-26T10:45:00Z",
        "estimatedUtc": "2026-10-26T10:45:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "5",
        "gate": "E9",
        "checkIn": "G",
        "viaDestinations": [],
    },
    {
        "flightId": "KL1232",
        "flightType": "D",
        "airlineOperator": {"iata": "KL", "name": "KLM"},
        "locationAndTerminal": {"airportCode": "AMS"},
        "scheduledUtc": "2026-10-26T11:30:00Z",
        "estimatedUtc": "2026-10-26T11:30:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "5",
        "gate": "G18",
        "checkIn": "H",
        "viaDestinations": [],
    },
    {
        "flightId": "AF1185",
        "flightType": "D",
        "airlineOperator": {"iata": "AF", "name": "Air France"},
        "locationAndTerminal": {"airportCode": "CDG"},
        "scheduledUtc": "2026-10-26T12:10:00Z",
        "estimatedUtc": "2026-10-26T12:10:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "5",
        "gate": "F31",
        "checkIn": "B",
        "viaDestinations": [],
    },
    {
        "flightId": "TK1760",
        "flightType": "D",
        "airlineOperator": {"iata": "TK", "name": "Turkish Airlines"},
        "locationAndTerminal": {"airportCode": "IST"},
        "scheduledUtc": "2026-10-26T13:00:00Z",
        "estimatedUtc": "2026-10-26T13:00:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "5",
        "gate": "H5",
        "checkIn": "D",
        "viaDestinations": [],
    },
    {
        "flightId": "EW4290",
        "flightType": "D",
        "airlineOperator": {"iata": "EW", "name": "Eurowings"},
        "locationAndTerminal": {"airportCode": "DUS"},
        "scheduledUtc": "2026-10-26T13:30:00Z",
        "estimatedUtc": "2026-10-26T13:30:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SEQ",
        "departureTerminal": "5",
        "gate": "A2",
        "checkIn": "C",
        "viaDestinations": [],
    },
    {
        "flightId": "OS552",
        "flightType": "D",
        "airlineOperator": {"iata": "OS", "name": "Austrian Airlines"},
        "locationAndTerminal": {"airportCode": "VIE"},
        "scheduledUtc": "2026-10-26T14:15:00Z",
        "estimatedUtc": "2026-10-26T14:15:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "5",
        "gate": "D14",
        "checkIn": "E",
        "viaDestinations": [],
    },
    {
        "flightId": "SK1403",
        "flightType": "D",
        "airlineOperator": {"iata": "SK", "name": "SAS Scandinavian Airlines"},
        "locationAndTerminal": {"airportCode": "BGO"},
        "scheduledUtc": "2026-10-26T14:55:00Z",
        "estimatedUtc": "2026-10-26T14:55:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "5",
        "gate": "C11",
        "checkIn": "F",
        "viaDestinations": [],
    },
    {
        "flightId": "W63302",
        "flightType": "D",
        "airlineOperator": {"iata": "W6", "name": "Wizz Air"},
        "locationAndTerminal": {"airportCode": "WAW"},
        "scheduledUtc": "2026-10-26T15:40:00Z",
        "estimatedUtc": "2026-10-26T15:40:00Z",
        "actualUtc":    "",
        "flightLegStatus": "SCH",
        "departureTerminal": "2",
        "gate": "B5",
        "checkIn": "A",
        "viaDestinations": [],
    },
    {
        "flightId": "VY1831",
        "flightType": "D",
        "airlineOperator": {"iata": "VY", "name": "Vueling"},
        "locationAndTerminal": {"airportCode": "BCN"},
        "scheduledUtc": "2026-10-26T16:30:00Z",
        "estimatedUtc": "2026-10-26T16:30:00Z",
        "actualUtc":    "",
        "flightLegStatus": "CAN",
        "departureTerminal": "5",
        "gate": "",
        "checkIn": "",
        "viaDestinations": [],
    },
]

# -------------------------------------------------------
# Helper: sample data disclaimer banner
# -------------------------------------------------------

DISCLAIMER = (
    Fore.YELLOW
    + Style.BRIGHT
    + "\n  ╔══════════════════════════════════════════════════════════╗"
    + "\n  ║  ⚠  OFFLINE DEMO — SAMPLE DATA — NOT LIVE FLIGHT INFO  ⚠  ║"
    + "\n  ║     This data is fictional and for demonstration only.   ║"
    + "\n  ╚══════════════════════════════════════════════════════════╝"
    + Style.RESET_ALL
)


def _show_disclaimer():
    """Prints the sample-data disclaimer so the user is never misled."""
    print(DISCLAIMER)
    print()


def _pause(seconds: float = 1.5):
    time.sleep(seconds)


def _announce(step: int, total: int, description: str):
    """Prints a numbered step banner."""
    print()
    print(Fore.MAGENTA + f"  ─── OFFLINE DEMO STEP {step}/{total}: {description} ───" + Style.RESET_ALL)
    print()
    _pause(1.0)


# -------------------------------------------------------
# Interactive sub-features
# -------------------------------------------------------

def _offline_airport_selection():
    """
    Demonstrates airport selection using the real airport list.
    No API call is made — just shows the selection UI.
    Returns the chosen IATA code.
    """
    from airports import AIRPORTS, AIRPORT_CODES

    _show_disclaimer()
    print_header("OFFLINE DEMO — Airport Selection")
    print()
    print("  All Swedavia airports are listed below.")
    print("  In the real application the same list is shown and your")
    print("  choice determines which airport's flights are fetched.")
    print()

    codes = AIRPORT_CODES
    for i in range(0, len(codes), 2):
        left_code  = codes[i]
        left_name  = get_airport_name(left_code)
        left_str   = f"  {Fore.YELLOW}{left_code}{Style.RESET_ALL} — {left_name:<35}"
        if i + 1 < len(codes):
            right_code = codes[i + 1]
            right_name = get_airport_name(right_code)
            right_str  = f"{Fore.YELLOW}{right_code}{Style.RESET_ALL} — {right_name}"
            print(left_str + right_str)
        else:
            print(left_str)

    print()
    print(Fore.CYAN + "  (Offline demo will use ARN — Stockholm Arlanda Airport)" + Style.RESET_ALL)
    print()
    _pause(2.0)
    return "ARN"


def _offline_arrivals(airport: str):
    """
    Shows sample arrivals data with full pagination so the user
    can see the page-by-page navigation in action.
    """
    _show_disclaimer()
    print_info(f"Loading sample arrivals for {airport} — {get_airport_name(airport)} ...")
    _pause(1.0)

    # show_arrivals already paginates at PAGE_SIZE=12 rows,
    # so 16 sample flights means 2 pages — pagination is demonstrated.
    show_arrivals(SAMPLE_ARRIVALS, airport, SAMPLE_DATE + " [SAMPLE]")


def _offline_departures(airport: str):
    """
    Shows sample departures data with full pagination.
    14 flights → 2 pages.
    """
    _show_disclaimer()
    print_info(f"Loading sample departures for {airport} — {get_airport_name(airport)} ...")
    _pause(1.0)

    show_departures(SAMPLE_DEPARTURES, airport, SAMPLE_DATE + " [SAMPLE]")


def _offline_search():
    """
    Demonstrates flight search using sample data.
    Lets the user type a real flight number to see it found — or not found.
    """
    _show_disclaimer()
    print_header("OFFLINE DEMO — Search Flight [SAMPLE DATA]")
    print()
    print("  Available sample flight numbers to try:")
    all_ids = sorted(
        set(f["flightId"] for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES)
    )

    # Print in columns of 4
    for i in range(0, len(all_ids), 4):
        chunk = all_ids[i : i + 4]
        print("    " + "   ".join(f"{Fore.YELLOW}{fid:<8}{Style.RESET_ALL}" for fid in chunk))

    print()
    flight_id = input(
        Fore.YELLOW + "  Enter a flight number to search (or press Enter for SK142): "
        + Style.RESET_ALL
    ).strip().upper()

    if not flight_id:
        flight_id = "SK142"

    print()
    print_info(f"Searching sample data for flight: {flight_id}")
    _pause(0.8)

    # Search all sample data
    matches = [
        f for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES
        if f.get("flightId", "").upper() == flight_id
    ]

    if matches:
        print_success(f"Found {len(matches)} match(es) for {flight_id} [SAMPLE DATA]:")
        for flight in matches:
            ft = flight.get("flightType", "A")
            show_flight_detail(flight, ft)
    else:
        print_warning(
            f"Flight '{flight_id}' not found in the sample dataset.\n"
            "  Try one of the flight numbers listed above."
        )


def _offline_odata_demo():
    """
    Demonstrates the OData query concept by filtering sample data
    in Python. Shows what the real OData endpoint does, but locally.
    """
    _show_disclaimer()
    print_header("OFFLINE DEMO — OData-Style Query [SAMPLE DATA]")
    print()
    print("  In the real application the OData query is sent to the")
    print("  Swedavia API. Here we filter the sample data locally")
    print("  to show how the feature works.")
    print()

    print("  Choose a sample query:")
    print(f"    {Fore.YELLOW}1{Style.RESET_ALL}. Show all delayed flights")
    print(f"    {Fore.YELLOW}2{Style.RESET_ALL}. Show all cancelled flights")
    print(f"    {Fore.YELLOW}3{Style.RESET_ALL}. Show SAS flights only")
    print(f"    {Fore.YELLOW}4{Style.RESET_ALL}. Show arrivals from London Heathrow (LHR)")
    print(f"    {Fore.YELLOW}5{Style.RESET_ALL}. Show all departures")
    print()

    choice = input(
        Fore.YELLOW + "  Enter choice (1–5, or press Enter for 1): "
        + Style.RESET_ALL
    ).strip()

    if choice not in ("1", "2", "3", "4", "5"):
        choice = "1"

    all_flights = SAMPLE_ARRIVALS + SAMPLE_DEPARTURES

    if choice == "1":
        label  = "Delayed flights  [flightLegStatus eq 'DEL'] [SAMPLE DATA]"
        result = [f for f in all_flights if f.get("flightLegStatus") == "DEL"]
    elif choice == "2":
        label  = "Cancelled flights  [flightLegStatus eq 'CAN'] [SAMPLE DATA]"
        result = [f for f in all_flights if f.get("flightLegStatus") == "CAN"]
    elif choice == "3":
        label  = "SAS flights  [airlineOperator/iata eq 'SK'] [SAMPLE DATA]"
        result = [
            f for f in all_flights
            if isinstance(f.get("airlineOperator"), dict)
            and f["airlineOperator"].get("iata") == "SK"
        ]
    elif choice == "4":
        label  = "Arrivals from LHR  [flightType eq 'A' and locationCode eq 'LHR'] [SAMPLE DATA]"
        result = [
            f for f in SAMPLE_ARRIVALS
            if isinstance(f.get("locationAndTerminal"), dict)
            and f["locationAndTerminal"].get("airportCode") == "LHR"
        ]
    else:
        label  = "All departures  [flightType eq 'D'] [SAMPLE DATA]"
        result = [f for f in all_flights if f.get("flightType") == "D"]

    print()
    _pause(0.8)
    show_query_results(result, label)


# -------------------------------------------------------
# Main offline demo entry point
# -------------------------------------------------------

def run_offline_demo():
    """
    Runs the complete offline demo interactively.
    The user can navigate through each feature step by step.
    No API key or internet connection is required.
    """
    clear_screen()

    print()
    print(Fore.YELLOW + Style.BRIGHT
          + "  ╔══════════════════════════════════════════════════════════╗" + Style.RESET_ALL)
    print(Fore.YELLOW + Style.BRIGHT
          + "  ║    ✈  SWEDAVIA FLIGHTINFO — OFFLINE DEMO MODE  ✈       ║" + Style.RESET_ALL)
    print(Fore.YELLOW + Style.BRIGHT
          + "  ║  No API key required. All data is SAMPLE DATA only.    ║" + Style.RESET_ALL)
    print(Fore.YELLOW + Style.BRIGHT
          + "  ╚══════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    print()
    print_info("This offline demo showcases the application's features")
    print_info("using fictional sample flights. Times are converted to")
    print_info("Swedish local time exactly as the live application does.")
    print()
    print(Fore.WHITE
          + "  ┌──────────────────────────────────────────────┐\n"
          + "  │         OFFLINE DEMO MENU                    │\n"
          + "  ├──────────────────────────────────────────────┤\n"
          + "  │  1. 🌍  Airport Selection                    │\n"
          + "  │  2. ✈   Arrivals          (with pagination)  │\n"
          + "  │  3. ✈   Departures        (with pagination)  │\n"
          + "  │  4. 🔍  Search Flight                        │\n"
          + "  │  5. 🔎  OData-Style Query                    │\n"
          + "  │  6. ▶   Run Full Auto-Walkthrough            │\n"
          + "  │                                              │\n"
          + "  │  0. ↩   Return to Main Menu                  │\n"
          + "  └──────────────────────────────────────────────┘")
    print()

    airport = "ARN"  # Default airport for the offline demo

    while True:
        choice = input(
            Fore.YELLOW + "  Offline Demo — choose (0–6): " + Style.RESET_ALL
        ).strip()

        if choice == "1":
            airport = _offline_airport_selection()
        elif choice == "2":
            _offline_arrivals(airport)
        elif choice == "3":
            _offline_departures(airport)
        elif choice == "4":
            _offline_search()
        elif choice == "5":
            _offline_odata_demo()
        elif choice == "6":
            _run_auto_walkthrough(airport)
        elif choice == "0":
            print_info("Returning to main menu...")
            return
        else:
            print_warning("Please enter a number between 0 and 6.")

        # Re-show the menu after each action
        print()
        print(Fore.WHITE
              + "  ┌──────────────────────────────────────────────┐\n"
              + "  │         OFFLINE DEMO MENU                    │\n"
              + "  ├──────────────────────────────────────────────┤\n"
              + "  │  1. 🌍  Airport Selection                    │\n"
              + "  │  2. ✈   Arrivals          (with pagination)  │\n"
              + "  │  3. ✈   Departures        (with pagination)  │\n"
              + "  │  4. 🔍  Search Flight                        │\n"
              + "  │  5. 🔎  OData-Style Query                    │\n"
              + "  │  6. ▶   Run Full Auto-Walkthrough            │\n"
              + "  │                                              │\n"
              + "  │  0. ↩   Return to Main Menu                  │\n"
              + "  └──────────────────────────────────────────────┘")
        print()


def _run_auto_walkthrough(airport: str):
    """
    Automatically steps through every offline demo feature
    with short pauses — useful for screen recording / presentations.
    """
    clear_screen()
    total = 5

    print(DISCLAIMER)
    print_header("OFFLINE DEMO — Auto Walkthrough")
    print_info("Automatically demonstrating all features with sample data.")
    print_info("No API key or internet required.")
    print()
    print(Fore.YELLOW + "  Starting in 3 seconds..." + Style.RESET_ALL)
    _pause(3.0)

    # Step 1: Airport selection
    _announce(1, total, "Airport Selection")
    _offline_airport_selection()
    _pause(1.5)

    # Step 2: Arrivals
    _announce(2, total, f"Arrivals at {airport} — {get_airport_name(airport)} [SAMPLE DATA]")
    _show_disclaimer()
    print_info("Displaying sample arrivals (16 flights → 2 pages of pagination)...")
    _pause(1.0)
    # Show only first page automatically; user can press Enter to see page 2
    show_arrivals(SAMPLE_ARRIVALS, airport, SAMPLE_DATE + " [SAMPLE]")
    _pause(1.5)

    # Step 3: Departures
    _announce(3, total, f"Departures from {airport} — {get_airport_name(airport)} [SAMPLE DATA]")
    _show_disclaimer()
    print_info("Displaying sample departures (14 flights → 2 pages of pagination)...")
    _pause(1.0)
    show_departures(SAMPLE_DEPARTURES, airport, SAMPLE_DATE + " [SAMPLE]")
    _pause(1.5)

    # Step 4: Flight search
    _announce(4, total, "Search Flight — SK142 [SAMPLE DATA]")
    _show_disclaimer()
    print_info("Searching sample data for flight SK142...")
    _pause(1.0)
    matches = [f for f in SAMPLE_ARRIVALS if f.get("flightId") == "SK142"]
    if matches:
        print_success(f"Found {len(matches)} match(es) for SK142 [SAMPLE DATA]:")
        show_flight_detail(matches[0], "A")
    _pause(1.5)

    # Step 5: OData-style query
    _announce(5, total, "OData-Style Query — Delayed flights [SAMPLE DATA]")
    _show_disclaimer()
    delayed = [f for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES if f.get("flightLegStatus") == "DEL"]
    label = "Delayed flights [flightLegStatus eq 'DEL'] [SAMPLE DATA]"
    print_info(f"Filtering sample data: {label}")
    _pause(1.0)
    show_query_results(delayed, label)
    _pause(1.5)

    # Summary
    print()
    print(Fore.MAGENTA + "  ─── AUTO WALKTHROUGH COMPLETE ───" + Style.RESET_ALL)
    print()
    print_success("All offline demo features have been shown!")
    print()
    features_shown = [
        "✔  Airport selection   — listed all 10 Swedavia airports",
        "✔  Arrivals            — 16 sample flights, 2 pages pagination",
        "✔  Departures          — 14 sample flights, 2 pages pagination",
        "✔  Search Flight       — found SK142 in sample data",
        "✔  OData-style query   — filtered delayed flights",
        "✔  Time conversion     — all UTC times shown in Swedish local time",
    ]
    for f in features_shown:
        print(Fore.GREEN + f"     {f}" + Style.RESET_ALL)
    print()
    print(DISCLAIMER)
    print()
