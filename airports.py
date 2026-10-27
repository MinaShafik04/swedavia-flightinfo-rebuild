# airports.py
# -----------
# Contains the list of all Swedavia airports with their IATA codes
# and full names. This is used in the airport selection menu.

# Dictionary mapping IATA code -> full airport name
AIRPORTS = {
    "ARN": "Stockholm Arlanda Airport",
    "GOT": "Göteborg Landvetter Airport",
    "BMA": "Bromma Stockholm Airport",
    "MMX": "Malmö Airport",
    "LLA": "Luleå Airport",
    "UME": "Umeå Airport",
    "OSD": "Åre Östersund Airport",
    "VBY": "Visby Airport",
    "RNB": "Ronneby Airport",
    "KRN": "Kiruna Airport",
}

# Sorted list of IATA codes for display purposes
AIRPORT_CODES = sorted(AIRPORTS.keys())


def get_airport_name(iata_code: str) -> str:
    """
    Returns the full name of an airport given its IATA code.
    Returns the code itself if the airport is not in our list.
    """
    return AIRPORTS.get(iata_code.upper(), iata_code.upper())


def is_valid_airport(iata_code: str) -> bool:
    """
    Returns True if the given IATA code is a supported Swedavia airport.
    """
    return iata_code.upper() in AIRPORTS
