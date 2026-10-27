# display.py
# ----------
# Handles all output formatting for the terminal application.
# This file uses:
#   - colorama: for colored terminal text
#   - tabulate:  for drawing neat tables
#
# Keeping display logic in its own file makes it easy to update
# how things look without touching the business logic.

import os
from tabulate import tabulate
from colorama import Fore, Style, init as colorama_init

from time_utils import utc_string_to_swedish, utc_string_to_swedish_full
from airports import get_airport_name
import flight_utils

# Initialize colorama (required on Windows to enable ANSI color codes)
colorama_init(autoreset=True)

# -------------------------------------------------------
# Constants
# -------------------------------------------------------

PAGE_SIZE = 12  # Number of flights shown per page

# Human-readable labels for flight status codes
STATUS_LABELS = flight_utils.STATUS_LABELS

# Color coding by status
STATUS_COLORS = {
    "SCH": Fore.WHITE,
    "FPL": Fore.CYAN,
    "FLS": Fore.CYAN,
    "SEQ": Fore.CYAN,
    "ACT": Fore.GREEN,
    "CAN": Fore.RED,
    "LAN": Fore.GREEN,
    "RER": Fore.YELLOW,
    "DIV": Fore.YELLOW,
    "DEL": Fore.YELLOW,
}


# -------------------------------------------------------
# Helper functions
# -------------------------------------------------------

def clear_screen():
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str):
    """Prints a styled section header."""
    width = 60
    print()
    print(Fore.CYAN + "=" * width)
    print(Fore.CYAN + f"  ✈  {title}")
    print(Fore.CYAN + "=" * width)


def print_success(message: str):
    """Prints a success message in green."""
    print(Fore.GREEN + f"  ✔  {message}" + Style.RESET_ALL)


def print_warning(message: str):
    """Prints a warning message in yellow."""
    print(Fore.YELLOW + f"  ⚠  {message}" + Style.RESET_ALL)


def print_error(message: str):
    """Prints an error message in red."""
    print(Fore.RED + f"  ✖  {message}" + Style.RESET_ALL)


def print_info(message: str):
    """Prints an informational message in cyan."""
    print(Fore.CYAN + f"  ℹ  {message}" + Style.RESET_ALL)


def colorize_status(status_code: str) -> str:
    """
    Returns the human-readable status label colored by status type.
    For example, "CAN" becomes a red "Cancelled".
    """
    label = STATUS_LABELS.get(status_code, status_code)
    color = STATUS_COLORS.get(status_code, Fore.WHITE)
    return color + label + Style.RESET_ALL


def _get_status_code(flight: dict) -> str:
    """Extracts flight status code supporting both live API and offline demo structures."""
    return flight_utils.get_status_code(flight)


def _get_airline(flight: dict) -> str:
    """Extracts the airline code or name."""
    info = flight_utils.get_airline_info(flight)
    return info["iata"] if info["iata"] else (info["icao"] if info["icao"] else info["name"])


def _get_via_destinations(flight: dict) -> str:
    """Returns a comma-separated list of intermediate stops."""
    return ", ".join(flight_utils.get_via_destinations(flight))


def _format_arrivals_row(flight: dict) -> list:
    """
    Converts a single arrivals flight dictionary into a table row.
    Columns: Flight | From | Airline | Scheduled | Actual/Est | Status | Terminal | Gate
    """
    norm = flight_utils.normalize_flight(flight, flight_type="A")
    status_code = norm["status_code"]

    # Effective time: actual if available, else estimated, else scheduled
    displayed_time = norm["actual_time"] if norm["actual_time"] != "--:--" else norm["estimated_time"]

    return [
        norm["flight_id"],
        norm["location_display"],
        norm["airline_iata"] or norm["airline_name"],
        norm["scheduled_time"],
        displayed_time,
        colorize_status(status_code),
        norm["terminal"],
        norm["gate"],
    ]


def _format_departures_row(flight: dict) -> list:
    """
    Converts a single departures flight dictionary into a table row.
    Columns: Flight | To | Airline | Scheduled | Actual/Est | Status | Terminal | Gate
    """
    norm = flight_utils.normalize_flight(flight, flight_type="D")
    status_code = norm["status_code"]

    displayed_time = norm["actual_time"] if norm["actual_time"] != "--:--" else norm["estimated_time"]

    return [
        norm["flight_id"],
        norm["location_display"],
        norm["airline_iata"] or norm["airline_name"],
        norm["scheduled_time"],
        displayed_time,
        colorize_status(status_code),
        norm["terminal"],
        norm["gate"],
    ]


# -------------------------------------------------------
# Paginated table display
# -------------------------------------------------------

def _paginate(rows: list, headers: list, title: str):
    """Displays a list of rows as a table with pagination."""
    total = len(rows)
    if total == 0:
        print_warning("No flights found.")
        return

    page = 0
    while True:
        start = page * PAGE_SIZE
        end   = start + PAGE_SIZE
        page_rows = rows[start:end]

        print_header(title)
        print(Fore.WHITE + tabulate(page_rows, headers=headers, tablefmt="rounded_outline"))
        print()
        print_info(
            f"Showing {start + 1}–{min(end, total)} of {total} flights"
        )

        if end >= total:
            break

        print()
        user_input = input(
            Fore.YELLOW + "  Press Enter for next page, or type 'q' to go back: "
            + Style.RESET_ALL
        ).strip().lower()

        if user_input == "q":
            break

        page += 1


# -------------------------------------------------------
# Public display functions
# -------------------------------------------------------

def show_arrivals(flights: list, airport_iata: str, date_str: str):
    """Displays a paginated table of arriving flights."""
    airport_name = get_airport_name(airport_iata)
    title = f"ARRIVALS — {airport_name} ({airport_iata})  |  {date_str} (Swedish time)"

    headers = ["Flight", "From", "Airline", "Scheduled", "Actual/Est", "Status", "Terminal", "Gate"]
    rows = [_format_arrivals_row(f) for f in flights]
    _paginate(rows, headers, title)


def show_departures(flights: list, airport_iata: str, date_str: str):
    """Displays a paginated table of departing flights."""
    airport_name = get_airport_name(airport_iata)
    title = f"DEPARTURES — {airport_name} ({airport_iata})  |  {date_str} (Swedish time)"

    headers = ["Flight", "To", "Airline", "Scheduled", "Actual/Est", "Status", "Terminal", "Gate"]
    rows = [_format_departures_row(f) for f in flights]
    _paginate(rows, headers, title)


def show_flight_detail(flight: dict, flight_type: str = "A"):
    """
    Displays detailed information about a single flight.
    flight_type: "A" for arrival, "D" for departure.
    """
    norm = flight_utils.normalize_flight(flight, flight_type=flight_type)
    print_header(f"FLIGHT DETAIL — {norm['flight_id'] or 'Unknown'}")

    via = ", ".join(flight_utils.get_via_destinations(flight))

    rows = [
        ["Flight Number",  norm["flight_id"] or "N/A"],
        ["Airline",        norm["airline_display"]],
        ["Type",           norm["flight_type_label"]],
        ["" + ("From" if norm["flight_type"] == "A" else "To"), norm["location_display"]],
        ["Via",            via if via else "Direct"],
        ["Scheduled",      norm["scheduled_datetime"]],
        ["Estimated",      utc_string_to_swedish_full(norm["estimated_utc"])],
        ["Actual",         utc_string_to_swedish_full(norm["actual_utc"])],
        ["Status",         colorize_status(norm["status_code"]) + (f" ({norm['status_label']})" if norm["status_label"] != norm["status_code"] else "")],
        ["Terminal",       norm["terminal"] or "N/A"],
        ["Gate",           norm["gate"] or "N/A"],
        ["Baggage Claim",  norm["baggage_claim"] or "N/A"],
        ["Check-in",       norm["check_in"] or "N/A"],
        ["Remarks",        ", ".join(norm["remarks"]) if norm["remarks"] else ""],
    ]

    rows = [r for r in rows if r[1] and r[1] not in ("N/A", "")]
    print(tabulate(rows, tablefmt="rounded_outline"))
    print()


def show_query_results(flights: list, filter_str: str):
    """Displays OData query results."""
    if not flights:
        print_warning("No flights matched your query.")
        return

    print_header(f"QUERY RESULTS — {len(flights)} flight(s) found")
    print_info(f"Filter: {filter_str}")
    print()

    rows = []
    for f in flights:
        norm = flight_utils.normalize_flight(f)
        displayed = norm["actual_time"] if norm["actual_time"] != "--:--" else norm["estimated_time"]

        rows.append([
            norm["flight_id"],
            norm["flight_type_label"],
            norm["location_display"],
            norm["scheduled_time"],
            displayed,
            colorize_status(norm["status_code"]),
        ])

    headers = ["Flight", "Type", "From/To", "Scheduled", "Actual/Est", "Status"]
    print(Fore.WHITE + tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    print()
