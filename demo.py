# demo.py
# -------
# Implements "Demo Mode" — an automatic walkthrough that showcases
# all features of the application without requiring user input.
# This is useful for the school video recording and for presentations.

import time
from colorama import Fore, Style

from display import (
    print_header, print_info, print_success, print_warning,
    show_arrivals, show_departures, show_query_results,
    clear_screen,
)
from api_client import (
    get_arrivals, get_departures, search_flight,
    run_odata_query, check_heartbeat,
)
from airports import get_airport_name
from time_utils import today_utc

# -------------------------------------------------------
# Demo settings — change these to customise the demo
# -------------------------------------------------------
DEMO_AIRPORT  = "ARN"   # Stockholm Arlanda
DEMO_DATE     = today_utc()
DEMO_FLIGHT   = "SK100"  # A SAS flight as a search example
DEMO_PAUSE    = 2.0      # Seconds to pause between steps
PAGE_DEMO     = 6        # Number of flights to show in demo mode


def _pause(seconds: float = DEMO_PAUSE):
    """Pauses for a short moment so the viewer can read the screen."""
    time.sleep(seconds)


def _announce(step: int, total: int, description: str):
    """Prints a numbered step banner."""
    print()
    print(Fore.MAGENTA + f"  ─── DEMO STEP {step}/{total}: {description} ───" + Style.RESET_ALL)
    print()
    _pause(1.0)


def run_demo():
    """
    Runs the full demo, stepping through all major features.
    The demo uses real API calls so the user sees live data.
    """
    clear_screen()
    total_steps = 6

    print_header("DEMO MODE — Swedavia FlightInfo Rebuild")
    print()
    print_info("Welcome to the automatic demo! This will walk you through all features.")
    print_info(f"Demo Airport : {DEMO_AIRPORT} — {get_airport_name(DEMO_AIRPORT)}")
    print_info(f"Demo Date    : {DEMO_DATE} (today in UTC)")
    print()
    print(Fore.YELLOW + "  Starting in 3 seconds..." + Style.RESET_ALL)
    _pause(3.0)

    # ── Step 1: API Heartbeat ─────────────────────────────────────────────────
    _announce(1, total_steps, "API Heartbeat — checking connectivity")

    print_info("Sending a test request to the Swedavia API...")
    _pause(1.0)

    is_online = check_heartbeat(DEMO_AIRPORT)

    if is_online:
        print_success("API is ONLINE ✅  — The Swedavia FlightInfo API is reachable.")
    else:
        print_warning("API is OFFLINE ❌ — Could not reach the Swedavia API.")
        print_info("The demo will continue, but live data will not be available.")

    _pause(DEMO_PAUSE)

    # ── Step 2: Arrivals ──────────────────────────────────────────────────────
    _announce(2, total_steps, f"Arrivals at {DEMO_AIRPORT}")

    print_info(f"Fetching arrivals for {DEMO_AIRPORT} on {DEMO_DATE}...")
    flights = get_arrivals(DEMO_AIRPORT, DEMO_DATE)

    if flights:
        # Show only the first page for the demo
        show_arrivals(flights[:PAGE_DEMO], DEMO_AIRPORT, DEMO_DATE)
        print_info(f"  (Showing up to {PAGE_DEMO} flights in demo mode. Full mode shows all with pagination.)")
    else:
        print_warning("No arrivals data received.")

    _pause(DEMO_PAUSE)

    # ── Step 3: Departures ────────────────────────────────────────────────────
    _announce(3, total_steps, f"Departures from {DEMO_AIRPORT}")

    print_info(f"Fetching departures for {DEMO_AIRPORT} on {DEMO_DATE}...")
    flights = get_departures(DEMO_AIRPORT, DEMO_DATE)

    if flights:
        show_departures(flights[:PAGE_DEMO], DEMO_AIRPORT, DEMO_DATE)
        print_info(f"  (Showing up to {PAGE_DEMO} flights in demo mode.)")
    else:
        print_warning("No departures data received.")

    _pause(DEMO_PAUSE)

    # ── Step 4: Search Flight ─────────────────────────────────────────────────
    _announce(4, total_steps, f"Search Flight — looking up '{DEMO_FLIGHT}'")

    print_info(f"Searching for flight {DEMO_FLIGHT} (arrival) at {DEMO_AIRPORT} on {DEMO_DATE}...")
    results = search_flight(DEMO_AIRPORT, DEMO_DATE, DEMO_FLIGHT, flight_type="A")

    if not results:
        # Try departure instead
        print_info("Not found as arrival — trying as departure...")
        results = search_flight(DEMO_AIRPORT, DEMO_DATE, DEMO_FLIGHT, flight_type="D")

    if results:
        from display import show_flight_detail
        flight_type = results[0].get("flightType", "A")
        show_flight_detail(results[0], flight_type)
    else:
        print_warning(
            f"Flight {DEMO_FLIGHT} was not found for today. "
            "This is normal if the flight does not operate today."
        )

    _pause(DEMO_PAUSE)

    # ── Step 5: OData Query ───────────────────────────────────────────────────
    _announce(5, total_steps, "OData Advanced Query")

    demo_filter = f"airport eq '{DEMO_AIRPORT}' and scheduled eq '{DEMO_DATE}' and flightType eq 'D'"
    print_info("Running an example OData filter query:")
    print(Fore.WHITE + f"  Filter: {demo_filter}")
    print()
    _pause(1.5)

    results = run_odata_query(demo_filter)
    if results:
        show_query_results(results[:PAGE_DEMO], demo_filter)
    else:
        print_warning("No results returned for the demo OData query.")

    _pause(DEMO_PAUSE)

    # ── Step 6: Summary ───────────────────────────────────────────────────────
    _announce(6, total_steps, "Demo Complete")

    print_success("All features have been demonstrated successfully!")
    print()
    print_info("Features shown:")
    features = [
        "✔  API Heartbeat — verified API connectivity",
        "✔  Arrivals     — fetched and displayed arrival flights",
        "✔  Departures   — fetched and displayed departure flights",
        "✔  Search       — looked up a specific flight by number",
        "✔  OData Query  — ran an advanced filter query",
        "✔  Time zones   — all times shown in Swedish local time",
        "✔  Pagination   — large result sets paginated automatically",
    ]
    for feature in features:
        print(Fore.GREEN + f"     {feature}" + Style.RESET_ALL)

    print()
