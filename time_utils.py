# time_utils.py
# -------------
# Handles all date/time conversions for the application.
# The Swedavia API returns timestamps in UTC (Coordinated Universal Time).
# We convert these to Swedish local time (Europe/Stockholm timezone),
# which is CET (UTC+1) in winter and CEST (UTC+2) in summer.

from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo  # Built into Python 3.9+

# The timezone we want to display times in
SWEDISH_TZ = ZoneInfo("Europe/Stockholm")

# The format the API expects for dates
API_DATE_FORMAT = "%Y-%m-%d"

# The format we use when displaying times to the user
DISPLAY_TIME_FORMAT = "%H:%M"
DISPLAY_DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def utc_string_to_swedish(utc_string: str) -> str:
    """
    Converts a UTC ISO 8601 timestamp string from the API into
    a human-readable Swedish local time string (HH:MM).

    Example input:  "2026-10-26T14:30:00Z"
    Example output: "15:30"   (because Sweden is UTC+1 in October)

    Returns "--:--" if the input is empty or cannot be parsed.
    """
    if not utc_string:
        return "--:--"

    try:
        # Handle both "Z" suffix and "+00:00" offset formats
        utc_string = utc_string.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(utc_string)

        # If the datetime has no timezone info, assume it is UTC
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)

        # Convert to Swedish timezone
        dt_swedish = dt_utc.astimezone(SWEDISH_TZ)
        return dt_swedish.strftime(DISPLAY_TIME_FORMAT)

    except (ValueError, AttributeError):
        return "--:--"


def utc_string_to_swedish_full(utc_string: str) -> str:
    """
    Same as utc_string_to_swedish() but returns the full date and time.
    Example output: "2026-10-26 15:30"
    """
    if not utc_string:
        return "N/A"

    try:
        utc_string = utc_string.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(utc_string)

        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)

        dt_swedish = dt_utc.astimezone(SWEDISH_TZ)
        return dt_swedish.strftime(DISPLAY_DATETIME_FORMAT)

    except (ValueError, AttributeError):
        return "N/A"


def today_utc() -> str:
    """
    Returns today's date in UTC as a string formatted for the API (YYYY-MM-DD).
    """
    return datetime.now(timezone.utc).strftime(API_DATE_FORMAT)


def is_valid_date(date_string: str) -> bool:
    """
    Returns True if the given string is a valid date in YYYY-MM-DD format.
    """
    try:
        datetime.strptime(date_string, API_DATE_FORMAT)
        return True
    except ValueError:
        return False
