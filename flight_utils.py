# flight_utils.py
# ---------------
# Shared helper functions for parsing, normalizing, and extracting
# flight details from Swedavia FlightInfo API v2 responses.
#
# Supports both:
# 1. Live API responses (nested objects: locationAndStatus, arrivalTime, departureTime, etc.)
# 2. Offline demo sample data (top-level properties)

from time_utils import (
    utc_string_to_swedish,
    utc_string_to_swedish_full,
    DISPLAY_DATETIME_FORMAT,
)
from airports import get_airport_name

# Human-readable labels for flight status codes
STATUS_LABELS = {
    "SCH": "Scheduled",
    "FPL": "Flight Plan",
    "FLS": "Leg Status",
    "SEQ": "Sequenced",
    "ACT": "Active",
    "CAN": "Cancelled",
    "LAN": "Landed",
    "RER": "Rerouted",
    "DIV": "Diverted",
    "DEL": "Delayed",
}

# CSS badge classes / colors
STATUS_BOOTSTRAP_CLASSES = {
    "SCH": "secondary",
    "FPL": "info",
    "FLS": "info",
    "SEQ": "info",
    "ACT": "success",
    "CAN": "danger",
    "LAN": "success",
    "RER": "warning",
    "DIV": "warning",
    "DEL": "warning",
}


def get_flight_id(flight: dict) -> str:
    """Returns the flight identifier (e.g. 'SK142')."""
    return flight.get("flightId", "") or flight.get("flightLegIdentifier", {}).get("flightId", "")


def get_flight_type(flight: dict, default: str = "A") -> str:
    """Returns 'A' for Arrival or 'D' for Departure."""
    ft = flight.get("flightType", "")
    if ft in ("A", "D"):
        return ft
    # In live API, presence of arrivalTime vs departureTime can indicate type
    if "arrivalTime" in flight and "departureTime" not in flight:
        return "A"
    if "departureTime" in flight and "arrivalTime" not in flight:
        return "D"
    return default


def get_status_code(flight: dict) -> str:
    """
    Extracts the status code (e.g. 'SCH', 'DEL', 'LAN', 'CAN').
    Checks live API locationAndStatus.flightLegStatus first, then falls back to top-level.
    """
    loc_status = flight.get("locationAndStatus")
    if isinstance(loc_status, dict) and loc_status.get("flightLegStatus"):
        return loc_status.get("flightLegStatus", "")
    return flight.get("flightLegStatus", "")


def get_status_label(flight: dict) -> str:
    """
    Returns a human-readable description for the flight status.
    Uses official English status description if provided by the API,
    or falls back to STATUS_LABELS dictionary.
    """
    loc_status = flight.get("locationAndStatus")
    if isinstance(loc_status, dict) and loc_status.get("flightLegStatusEnglish"):
        return loc_status.get("flightLegStatusEnglish")
    code = get_status_code(flight)
    return STATUS_LABELS.get(code, code if code else "Scheduled")


def get_status_class(flight: dict) -> str:
    """Returns a CSS / Bootstrap badge class name for styling."""
    code = get_status_code(flight)
    return STATUS_BOOTSTRAP_CLASSES.get(code, "secondary")


def get_airline_info(flight: dict) -> dict:
    """
    Extracts airline name and IATA/ICAO codes.
    Returns: {"name": str, "iata": str, "icao": str, "display": str}
    """
    operator = flight.get("airlineOperator")
    if isinstance(operator, dict):
        iata = operator.get("iata", "") or ""
        icao = operator.get("icao", "") or ""
        name = operator.get("name", "") or ""
        display = name if name else (iata if iata else icao)
        if name and iata and name != iata:
            display = f"{name} ({iata})"
        return {"name": name, "iata": iata, "icao": icao, "display": display}
    return {"name": "", "iata": "", "icao": "", "display": ""}


def get_time_raw(flight: dict, field: str, flight_type: str = "A") -> str:
    """
    Retrieves raw UTC ISO timestamp for 'scheduledUtc', 'estimatedUtc', or 'actualUtc'.
    Checks nested arrivalTime / departureTime objects (live API),
    then falls back to top-level keys (offline demo data).
    """
    primary_key = "arrivalTime" if flight_type == "A" else "departureTime"
    obj = flight.get(primary_key)
    if isinstance(obj, dict) and obj.get(field):
        return obj.get(field)

    secondary_key = "departureTime" if flight_type == "A" else "arrivalTime"
    sec_obj = flight.get(secondary_key)
    if isinstance(sec_obj, dict) and sec_obj.get(field):
        return sec_obj.get(field)

    return flight.get(field, "") or ""


def get_location_info(flight: dict, flight_type: str = "A") -> dict:
    """
    Extracts origin or destination airport information.
    For arrivals: Departure airport (origin).
    For departures: Arrival airport (destination).
    Returns: {"city": str, "iata": str, "display": str}
    """
    flight_leg = flight.get("flightLegIdentifier", {})
    if not isinstance(flight_leg, dict):
        flight_leg = {}

    if flight_type == "A":
        iata = flight_leg.get("departureAirportIata", "")
        city = (
            flight.get("departureAirportEnglish")
            or flight.get("departureAirportSwedish")
            or ""
        )
    else:
        iata = flight_leg.get("arrivalAirportIata", "")
        city = (
            flight.get("arrivalAirportEnglish")
            or flight.get("arrivalAirportSwedish")
            or ""
        )

    # Fallback to locationAndTerminal in offline demo data
    loc = flight.get("locationAndTerminal")
    if not iata and isinstance(loc, dict):
        iata = loc.get("airportCode", "")

    # If city is missing, try looking up via our airport dictionary
    if not city and iata:
        city = get_airport_name(iata)

    if city and iata and city != iata:
        display = f"{city} ({iata})"
    elif city:
        display = city
    elif iata:
        display = iata
    else:
        display = "Unknown"

    via_list = get_via_destinations(flight)
    if via_list:
        display += f" via {', '.join(via_list)}"

    return {"city": city, "iata": iata, "display": display}


def get_via_destinations(flight: dict) -> list:
    """Extracts intermediate stop airport codes."""
    via = flight.get("viaDestinations", [])
    if not isinstance(via, list):
        return []
    result = []
    for item in via:
        if isinstance(item, dict):
            loc = item.get("locationAndTerminal", {})
            if isinstance(loc, dict) and loc.get("airportCode"):
                result.append(loc.get("airportCode"))
            elif item.get("airportCode"):
                result.append(item.get("airportCode"))
    return result


def get_terminal(flight: dict, flight_type: str = "A") -> str:
    """Extracts terminal string."""
    loc_status = flight.get("locationAndStatus")
    if isinstance(loc_status, dict) and loc_status.get("terminal"):
        return str(loc_status.get("terminal"))
    key = "arrivalTerminal" if flight_type == "A" else "departureTerminal"
    term = flight.get(key) or flight.get("terminal")
    return str(term) if term else ""


def get_gate(flight: dict) -> str:
    """Extracts gate string."""
    loc_status = flight.get("locationAndStatus")
    if isinstance(loc_status, dict) and loc_status.get("gate"):
        return str(loc_status.get("gate"))
    gate = flight.get("gate")
    return str(gate) if gate else ""


def get_baggage_claim(flight: dict) -> str:
    """Extracts baggage claim unit."""
    baggage = flight.get("baggage")
    if isinstance(baggage, dict) and baggage.get("baggageClaimUnit"):
        return str(baggage.get("baggageClaimUnit"))
    b = flight.get("baggageClaimUnit")
    return str(b) if b else ""


def get_checkin_desk(flight: dict) -> str:
    """Extracts check-in desk information."""
    ci = flight.get("checkIn")
    if isinstance(ci, dict):
        desk = ci.get("checkInDesk") or ci.get("desk") or ci.get("checkInDesks") or ""
        if desk:
            return str(desk)
    elif ci:
        return str(ci)
    return str(flight.get("checkIn", "") or "")


def normalize_flight(flight: dict, flight_type: str = "A") -> dict:
    """
    Builds a clean, normalized dictionary representation of a flight
    suitable for both console printing and Jinja2 web rendering.
    All times are converted to Swedish local time.
    """
    ft = get_flight_type(flight, default=flight_type)
    sched_utc = get_time_raw(flight, "scheduledUtc", ft)
    est_utc = get_time_raw(flight, "estimatedUtc", ft)
    act_utc = get_time_raw(flight, "actualUtc", ft)

    sched_se = utc_string_to_swedish(sched_utc)
    est_se = utc_string_to_swedish(est_utc)
    act_se = utc_string_to_swedish(act_utc)

    # Actual takes priority if present, then estimated, else scheduled
    effective_se = act_se if act_se != "--:--" else (est_se if est_se != "--:--" else sched_se)

    status_code = get_status_code(flight)
    status_label = get_status_label(flight)
    status_class = get_status_class(flight)

    airline = get_airline_info(flight)
    location = get_location_info(flight, ft)

    remarks = []
    rem_en = flight.get("remarksEnglish")
    if isinstance(rem_en, list):
        for r in rem_en:
            if isinstance(r, dict) and r.get("text"):
                remarks.append(r.get("text"))
            elif isinstance(r, str):
                remarks.append(r)
    rem_dict = flight.get("remarks")
    if isinstance(rem_dict, dict) and rem_dict.get("definition"):
        remarks.append(rem_dict.get("definition"))

    return {
        "flight_id": get_flight_id(flight),
        "flight_type": ft,
        "flight_type_label": "Arrival" if ft == "A" else "Departure",
        "airline_name": airline["name"],
        "airline_iata": airline["iata"],
        "airline_display": airline["display"],
        "location_city": location["city"],
        "location_iata": location["iata"],
        "location_display": location["display"],
        "scheduled_utc": sched_utc,
        "estimated_utc": est_utc,
        "actual_utc": act_utc,
        "scheduled_time": sched_se,
        "estimated_time": est_se,
        "actual_time": act_se,
        "effective_time": effective_se,
        "scheduled_datetime": utc_string_to_swedish_full(sched_utc),
        "status_code": status_code,
        "status_label": status_label,
        "status_class": status_class,
        "terminal": get_terminal(flight, ft),
        "gate": get_gate(flight),
        "baggage_claim": get_baggage_claim(flight),
        "check_in": get_checkin_desk(flight),
        "remarks": remarks,
        "raw": flight,
    }
