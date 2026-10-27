# main.py
# -------
# Entry point for the Swedavia FlightInfo Rebuild terminal application.
#
# Run this file to start the application:
#   python main.py
#
# This file builds the main menu and routes user choices to the
# correct functions in other modules.

import sys
from colorama import Fore, Style, init as colorama_init

from airports import AIRPORTS, AIRPORT_CODES, get_airport_name, is_valid_airport
from api_client import (
    get_arrivals, get_departures,
    search_flight, run_odata_query, check_heartbeat,
)
from display import (
    clear_screen, print_header, print_info, print_success,
    print_warning, print_error, show_arrivals, show_departures,
    show_flight_detail, show_query_results,
)
from time_utils import today_utc, is_valid_date

# Initialize colorama (required on Windows)
colorama_init(autoreset=True)

# -------------------------------------------------------
# Application banner
# -------------------------------------------------------

APP_TITLE = "Swedavia FlightInfo Rebuild"
APP_VERSION = "1.0"


def print_banner():
    """Prints the application title banner."""
    clear_screen()
    print()
    print(Fore.CYAN + Style.BRIGHT + "  ╔══════════════════════════════════════════════════════╗")
    print(Fore.CYAN + Style.BRIGHT + "  ║        ✈  SWEDAVIA FLIGHTINFO REBUILD  ✈            ║")
    print(Fore.CYAN + Style.BRIGHT + "  ║           Terminal Application  v1.0                ║")
    print(Fore.CYAN + Style.BRIGHT + "  ╚══════════════════════════════════════════════════════╝")
    print()


# -------------------------------------------------------
# Input helpers
# -------------------------------------------------------

def ask_airport(current_airport: str) -> str:
    """
    Asks the user to choose a Swedavia airport.
    Returns the selected IATA code (uppercase).

    If the user just presses Enter, the current airport is kept.
    """
    print_header("AIRPORT SELECTION")
    print()
    print("  Supported Swedavia airports:")
    print()

    # Display airports in a two-column layout
    codes = AIRPORT_CODES
    for i in range(0, len(codes), 2):
        left_code = codes[i]
        left_name = get_airport_name(left_code)
        left_str = f"  {Fore.YELLOW}{left_code}{Style.RESET_ALL} — {left_name:<35}"

        if i + 1 < len(codes):
            right_code = codes[i + 1]
            right_name = get_airport_name(right_code)
            right_str = f"{Fore.YELLOW}{right_code}{Style.RESET_ALL} — {right_name}"
            print(left_str + right_str)
        else:
            print(left_str)

    print()
    print_info(f"Current airport: {current_airport} — {get_airport_name(current_airport)}")
    print()

    while True:
        raw = input(
            Fore.YELLOW + f"  Enter airport code (or press Enter to keep {current_airport}): "
            + Style.RESET_ALL
        ).strip().upper()

        if raw == "":
            return current_airport  # Keep the current selection

        if is_valid_airport(raw):
            print_success(f"Airport set to: {raw} — {get_airport_name(raw)}")
            return raw
        else:
            print_error(f"'{raw}' is not a supported Swedavia airport. Please try again.")


def ask_date(default_date: str) -> str:
    """
    Asks the user for a date in YYYY-MM-DD format.
    Returns today's UTC date if the user just presses Enter.
    """
    print()
    while True:
        raw = input(
            Fore.YELLOW + f"  Enter date (YYYY-MM-DD) or press Enter for today [{default_date}]: "
            + Style.RESET_ALL
        ).strip()

        if raw == "":
            return default_date  # Default to today

        if is_valid_date(raw):
            return raw
        else:
            print_error("Invalid date format. Please use YYYY-MM-DD (example: 2026-10-26).")


def press_enter_to_continue():
    """Waits for the user to press Enter before returning to the menu."""
    print()
    input(Fore.CYAN + "  Press Enter to return to the menu..." + Style.RESET_ALL)


# -------------------------------------------------------
# Feature handlers
# -------------------------------------------------------

def handle_arrivals(airport: str):
    """Handles the Arrivals menu option."""
    print_header("ARRIVALS")
    date_str = ask_date(today_utc())

    print()
    print_info(f"Fetching arrivals for {airport} on {date_str}...")
    flights = get_arrivals(airport, date_str)

    if not flights:
        print_warning("No arrivals data found for this airport and date.")
    else:
        show_arrivals(flights, airport, date_str)

    press_enter_to_continue()


def handle_departures(airport: str):
    """Handles the Departures menu option."""
    print_header("DEPARTURES")
    date_str = ask_date(today_utc())

    print()
    print_info(f"Fetching departures for {airport} on {date_str}...")
    flights = get_departures(airport, date_str)

    if not flights:
        print_warning("No departures data found for this airport and date.")
    else:
        show_departures(flights, airport, date_str)

    press_enter_to_continue()


def handle_search(airport: str):
    """Handles the Search Flight menu option."""
    print_header("SEARCH FLIGHT")
    print_info(f"Search for a flight at: {airport} — {get_airport_name(airport)}")
    print()

    # Get flight number
    while True:
        flight_id = input(
            Fore.YELLOW + "  Enter flight number (e.g. SK142, FR1234): "
            + Style.RESET_ALL
        ).strip().upper()

        if flight_id:
            break
        print_error("Flight number cannot be empty. Please try again.")

    # Get date
    date_str = ask_date(today_utc())

    # Ask flight type
    print()
    print("  Search in:")
    print("    1. Arrivals")
    print("    2. Departures")
    print("    3. Both")
    print()

    while True:
        choice = input(Fore.YELLOW + "  Choose (1/2/3): " + Style.RESET_ALL).strip()
        if choice in ("1", "2", "3"):
            break
        print_error("Please enter 1, 2, or 3.")

    results = []
    found_type = "A"

    if choice in ("1", "3"):
        print_info(f"Searching arrivals for flight {flight_id}...")
        arr = search_flight(airport, date_str, flight_id, flight_type="A")
        if arr:
            results = arr
            found_type = "A"

    if choice in ("2", "3") and not results:
        print_info(f"Searching departures for flight {flight_id}...")
        dep = search_flight(airport, date_str, flight_id, flight_type="D")
        if dep:
            results = dep
            found_type = "D"

    print()
    if results:
        print_success(f"Found {len(results)} result(s) for flight {flight_id}:")
        for flight in results:
            ft = flight.get("flightType", found_type)
            show_flight_detail(flight, ft)
    else:
        print_warning(
            f"No results found for flight '{flight_id}' at {airport} on {date_str}.\n"
            "  • Check that the flight number is correct (e.g. SK142, not SK 142).\n"
            "  • The flight may not operate on this date.\n"
            "  • Try a different airport or date."
        )

    press_enter_to_continue()


def handle_odata(airport: str):
    """Handles the OData Query menu option."""
    print_header("ODATA ADVANCED QUERY")
    print()
    print(Fore.WHITE + "  Write your own OData filter to search across all Swedavia airports.")
    print()
    print("  ── Supported fields ───────────────────────────────────────")
    print(f"  {Fore.YELLOW}airport{Style.RESET_ALL}      3-letter IATA code          airport eq 'ARN'")
    print(f"  {Fore.YELLOW}flightType{Style.RESET_ALL}   'A' (arrival) or 'D' (dep)  flightType eq 'A'")
    print(f"  {Fore.YELLOW}scheduled{Style.RESET_ALL}    date (YYYY-MM-DD)           scheduled eq '2026-10-26'")
    print(f"  {Fore.YELLOW}flightId{Style.RESET_ALL}     flight number               flightId eq 'SK142'")
    print()
    print("  ── Operators ───────────────────────────────────────────────")
    print(f"  {Fore.YELLOW}eq{Style.RESET_ALL}           equals")
    print(f"  {Fore.YELLOW}and{Style.RESET_ALL}          combine conditions")
    print()
    print("  ── Example queries ─────────────────────────────────────────")
    today = today_utc()
    print(f"  airport eq 'ARN' and scheduled eq '{today}' and flightType eq 'A'")
    print(f"  airport eq 'GOT' and scheduled eq '{today}' and flightType eq 'D' and flightId eq 'SK100'")
    print()
    print(Fore.CYAN + "  ────────────────────────────────────────────────────────────")
    print()

    # Show current airport as a hint
    print_info(f"Current airport (for reference): {airport}")
    print()

    odata_filter = input(
        Fore.YELLOW + "  Enter your OData filter (or press Enter to cancel): "
        + Style.RESET_ALL
    ).strip()

    if not odata_filter:
        print_info("Cancelled — returning to menu.")
        press_enter_to_continue()
        return

    print()
    print_info("Running query...")
    results = run_odata_query(odata_filter)

    if results:
        show_query_results(results, odata_filter)
    else:
        print_warning("No results returned for this query.")
        print_info(
            "Tips:\n"
            "  • Use single quotes around values: airport eq 'ARN'\n"
            "  • Check spelling of field names (case-sensitive)\n"
            "  • Make sure the date is in YYYY-MM-DD format"
        )

    press_enter_to_continue()


def handle_heartbeat(airport: str):
    """Handles the API Heartbeat menu option."""
    print_header("API HEARTBEAT — Connectivity Check")
    print()
    print_info(
        "This check uses the official arrivals endpoint to verify\n"
        "  that the Swedavia API is reachable. There is no dedicated\n"
        "  ping/health endpoint in the official documentation."
    )
    print()
    print_info(f"Testing connection using: {airport} arrivals ({today_utc()})...")
    print()

    is_online = check_heartbeat(airport)

    if is_online:
        print_success("API is ONLINE ✅")
        print_success("The Swedavia FlightInfo API v2 is reachable and responding.")
    else:
        print_warning("API is OFFLINE ❌")
        print_warning("Could not reach the Swedavia FlightInfo API.")
        print()
        print_info(
            "Possible causes:\n"
            "  • No internet connection\n"
            "  • Invalid API key in .env file\n"
            "  • Swedavia API is temporarily unavailable"
        )

    press_enter_to_continue()


def handle_demo():
    """Handles the Demo Mode menu option (live API)."""
    print_header("DEMO MODE")
    print()
    print_info("Demo mode will automatically walk through all features.")
    print_info("This uses real API calls and will take about 30–60 seconds.")
    print()

    confirm = input(
        Fore.YELLOW + "  Start demo? (y/n): " + Style.RESET_ALL
    ).strip().lower()

    if confirm == "y":
        from demo import run_demo
        run_demo()
        press_enter_to_continue()
    else:
        print_info("Demo cancelled — returning to menu.")
        press_enter_to_continue()


def handle_offline_demo():
    """
    Handles the Offline Demo menu option.
    Uses sample data only — no API key or internet required.
    """
    print_header("OFFLINE DEMO MODE")
    print()
    print_info("The offline demo uses SAMPLE DATA — no API key required.")
    print_info("All data shown is fictional and clearly labeled as such.")
    print_info("Features demonstrated: airport selection, arrivals,")
    print_info("departures, flight search, OData queries, and pagination.")
    print()

    confirm = input(
        Fore.YELLOW + "  Start offline demo? (y/n): " + Style.RESET_ALL
    ).strip().lower()

    if confirm == "y":
        from offline_demo import run_offline_demo
        run_offline_demo()
        press_enter_to_continue()
    else:
        print_info("Cancelled — returning to menu.")
        press_enter_to_continue()


# -------------------------------------------------------
# Main menu
# -------------------------------------------------------

def show_main_menu(current_airport: str):
    """Prints the main menu with the current airport shown."""
    print_banner()
    airport_label = f"{current_airport} — {get_airport_name(current_airport)}"
    print(Fore.CYAN + f"  Selected Airport: {Fore.YELLOW}{airport_label}{Style.RESET_ALL}")
    print()
    print(Fore.WHITE + "  ┌─────────────────────────────────────────┐")
    print(Fore.WHITE + "  │             MAIN MENU                   │")
    print(Fore.WHITE + "  ├─────────────────────────────────────────┤")
    print(Fore.WHITE + "  │  1. ✈  Arrivals                         │")
    print(Fore.WHITE + "  │  2. ✈  Departures                       │")
    print(Fore.WHITE + "  │  3. 🔍 Search Flight                     │")
    print(Fore.WHITE + "  │  4. 🔎 OData Advanced Query              │")
    print(Fore.WHITE + "  │  5. 📡 API Heartbeat                     │")
    print(Fore.WHITE + "  │  6. 🎬 Demo Mode          (live API)     │")
    print(Fore.WHITE + "  │  7. 🌍 Change Airport                    │")
    print(Fore.WHITE + "  │  8. 📋 Offline Demo  [SAMPLE DATA]      │")
    print(Fore.WHITE + "  │                                         │")
    print(Fore.WHITE + "  │  0. 🚪 Exit                              │")
    print(Fore.WHITE + "  └─────────────────────────────────────────┘")
    print()


def main():
    """
    Application entry point.
    Initializes the airport selection and runs the main menu loop.
    """
    # Start with Stockholm Arlanda as the default airport
    current_airport = "ARN"

    # Show airport selection on first launch
    print_banner()
    print_info("Welcome to the Swedavia FlightInfo Rebuild!")
    print_info("Let's start by selecting an airport.")
    current_airport = ask_airport(current_airport)

    # Main menu loop
    while True:
        show_main_menu(current_airport)

        choice = input(
            Fore.YELLOW + "  Enter your choice (0–8): " + Style.RESET_ALL
        ).strip()

        if choice == "1":
            handle_arrivals(current_airport)
        elif choice == "2":
            handle_departures(current_airport)
        elif choice == "3":
            handle_search(current_airport)
        elif choice == "4":
            handle_odata(current_airport)
        elif choice == "5":
            handle_heartbeat(current_airport)
        elif choice == "6":
            handle_demo()
        elif choice == "7":
            current_airport = ask_airport(current_airport)
        elif choice == "8":
            handle_offline_demo()
        elif choice == "0":
            print()
            print_success("Thank you for using Swedavia FlightInfo Rebuild. Goodbye! ✈")
            print()
            sys.exit(0)
        else:
            print_error("Invalid choice. Please enter a number between 0 and 8.")
            press_enter_to_continue()


# -------------------------------------------------------
# Run the application
# -------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print()
        print()
        print(Fore.CYAN + "  Application interrupted. Goodbye! ✈" + Style.RESET_ALL)
        print()
        sys.exit(0)
