# test_offline_demo.py
# --------------------
# Local tests for the offline demo module.
# These tests run entirely without an API key or internet connection.
#
# Run with:  python test_offline_demo.py

import sys
import traceback
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

PASS = Fore.GREEN  + "  PASS" + Style.RESET_ALL
FAIL = Fore.RED    + "  FAIL" + Style.RESET_ALL
INFO = Fore.CYAN   + "  INFO" + Style.RESET_ALL

results = []   # (test_name, passed: bool, detail: str)


def run_test(name: str, fn):
    """Runs a single test function and records the result."""
    try:
        fn()
        results.append((name, True, ""))
        print(f"{PASS}  {name}")
    except AssertionError as e:
        results.append((name, False, str(e)))
        print(f"{FAIL}  {name}\n         {Fore.RED}{e}{Style.RESET_ALL}")
    except Exception as e:
        detail = traceback.format_exc()
        results.append((name, False, detail))
        print(f"{FAIL}  {name}\n         {Fore.RED}{e}{Style.RESET_ALL}")


# -------------------------------------------------------
# Test helpers
# -------------------------------------------------------

def assert_eq(actual, expected, msg=""):
    assert actual == expected, (
        f"{msg}  expected={expected!r}  got={actual!r}"
    )

def assert_contains(container, item, msg=""):
    assert item in container, f"{msg}  {item!r} not in {container!r}"

def assert_true(condition, msg=""):
    assert condition, msg

def assert_no_crash(fn, *args, **kwargs):
    """Calls fn(*args, **kwargs) and asserts it does not raise."""
    fn(*args, **kwargs)


# ================================================================
# Test group 1: Sample data structure
# ================================================================

def test_arrivals_not_empty():
    from offline_demo import SAMPLE_ARRIVALS
    assert_true(len(SAMPLE_ARRIVALS) > 0, "SAMPLE_ARRIVALS must not be empty")

def test_departures_not_empty():
    from offline_demo import SAMPLE_DEPARTURES
    assert_true(len(SAMPLE_DEPARTURES) > 0, "SAMPLE_DEPARTURES must not be empty")

def test_arrivals_have_enough_for_two_pages():
    from offline_demo import SAMPLE_ARRIVALS
    from display import PAGE_SIZE
    assert_true(
        len(SAMPLE_ARRIVALS) > PAGE_SIZE,
        f"Need more than PAGE_SIZE={PAGE_SIZE} arrivals to demo pagination. "
        f"Got {len(SAMPLE_ARRIVALS)}."
    )

def test_departures_have_enough_for_two_pages():
    from offline_demo import SAMPLE_DEPARTURES
    from display import PAGE_SIZE
    assert_true(
        len(SAMPLE_DEPARTURES) > PAGE_SIZE,
        f"Need more than PAGE_SIZE={PAGE_SIZE} departures to demo pagination. "
        f"Got {len(SAMPLE_DEPARTURES)}."
    )

def test_every_arrival_has_required_keys():
    from offline_demo import SAMPLE_ARRIVALS
    required = {"flightId", "flightType", "scheduledUtc",
                "flightLegStatus", "airlineOperator", "locationAndTerminal"}
    for flight in SAMPLE_ARRIVALS:
        for key in required:
            assert_contains(flight, key, f"Arrival {flight.get('flightId','?')} missing key")

def test_every_departure_has_required_keys():
    from offline_demo import SAMPLE_DEPARTURES
    required = {"flightId", "flightType", "scheduledUtc",
                "flightLegStatus", "airlineOperator", "locationAndTerminal"}
    for flight in SAMPLE_DEPARTURES:
        for key in required:
            assert_contains(flight, key, f"Departure {flight.get('flightId','?')} missing key")

def test_all_arrivals_have_type_A():
    from offline_demo import SAMPLE_ARRIVALS
    for f in SAMPLE_ARRIVALS:
        assert_eq(f.get("flightType"), "A", f"Arrival {f.get('flightId')} flightType should be 'A'")

def test_all_departures_have_type_D():
    from offline_demo import SAMPLE_DEPARTURES
    for f in SAMPLE_DEPARTURES:
        assert_eq(f.get("flightType"), "D", f"Departure {f.get('flightId')} flightType should be 'D'")

def test_no_null_flight_ids():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES:
        fid = f.get("flightId", "")
        assert_true(bool(fid), "flightId must not be empty or None")

def test_sample_date_format():
    from offline_demo import SAMPLE_DATE
    from time_utils import is_valid_date
    assert_true(is_valid_date(SAMPLE_DATE), f"SAMPLE_DATE '{SAMPLE_DATE}' is not YYYY-MM-DD")

def test_airline_operator_is_dict():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES:
        op = f.get("airlineOperator")
        assert_true(
            isinstance(op, dict),
            f"airlineOperator in {f.get('flightId')} must be a dict, got {type(op)}"
        )

def test_location_is_dict():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES:
        loc = f.get("locationAndTerminal")
        assert_true(
            isinstance(loc, dict),
            f"locationAndTerminal in {f.get('flightId')} must be a dict, got {type(loc)}"
        )

def test_via_destinations_is_list():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES:
        via = f.get("viaDestinations")
        assert_true(
            isinstance(via, list),
            f"viaDestinations in {f.get('flightId')} must be a list, got {type(via)}"
        )

# ================================================================
# Test group 2: Time conversion (offline — no API needed)
# ================================================================

def test_utc_to_swedish_basic():
    from time_utils import utc_string_to_swedish
    # 2026-10-26 is after DST ends in Sweden (last Sunday of October 2026 = Oct 25)
    # So Europe/Stockholm = UTC+1 on Oct 26
    result = utc_string_to_swedish("2026-10-26T06:00:00Z")
    assert_eq(result, "07:00", "UTC 06:00 should be 07:00 Swedish (UTC+1) on Oct 26")

def test_utc_to_swedish_empty_string():
    from time_utils import utc_string_to_swedish
    result = utc_string_to_swedish("")
    assert_eq(result, "--:--", "Empty string should return '--:--'")

def test_utc_to_swedish_none_like():
    from time_utils import utc_string_to_swedish
    result = utc_string_to_swedish(None)
    assert_eq(result, "--:--", "None should return '--:--'")

def test_utc_full_basic():
    from time_utils import utc_string_to_swedish_full
    result = utc_string_to_swedish_full("2026-10-26T09:00:00Z")
    assert_eq(result, "2026-10-26 10:00", "UTC 09:00 → 10:00 Swedish on Oct 26 (UTC+1)")

def test_utc_full_empty():
    from time_utils import utc_string_to_swedish_full
    assert_eq(utc_string_to_swedish_full(""), "N/A")

def test_is_valid_date_good():
    from time_utils import is_valid_date
    assert_true(is_valid_date("2026-10-26"))
    assert_true(is_valid_date("2024-01-01"))

def test_is_valid_date_bad():
    from time_utils import is_valid_date
    assert_true(not is_valid_date("26-10-2026"))
    assert_true(not is_valid_date("not-a-date"))
    assert_true(not is_valid_date(""))

# ================================================================
# Test group 3: Airport helpers
# ================================================================

def test_valid_airports():
    from airports import is_valid_airport
    for code in ("ARN", "GOT", "BMA", "MMX", "LLA", "UME", "OSD", "VBY", "RNB", "KRN"):
        assert_true(is_valid_airport(code), f"{code} should be valid")

def test_invalid_airport():
    from airports import is_valid_airport
    assert_true(not is_valid_airport("XYZ"), "XYZ should not be a valid airport")

def test_get_airport_name_known():
    from airports import get_airport_name
    assert_eq(get_airport_name("ARN"), "Stockholm Arlanda Airport")

def test_get_airport_name_unknown():
    from airports import get_airport_name
    # Unknown codes should return the code itself
    assert_eq(get_airport_name("XYZ"), "XYZ")

def test_airport_codes_sorted():
    from airports import AIRPORT_CODES
    assert_eq(AIRPORT_CODES, sorted(AIRPORT_CODES), "AIRPORT_CODES must be sorted")

# ================================================================
# Test group 4: Display helpers (no rendering — just logic)
# ================================================================

def test_colorize_status_known():
    from display import colorize_status
    # Should return a non-empty string (contains ANSI codes + label text)
    result = colorize_status("CAN")
    assert_contains(result, "Cancelled", "CAN should map to 'Cancelled'")

def test_colorize_status_unknown():
    from display import colorize_status
    # Unknown codes should pass through the code itself
    result = colorize_status("XYZ")
    assert_contains(result, "XYZ")

def test_format_arrivals_row_no_crash():
    from display import _format_arrivals_row
    from offline_demo import SAMPLE_ARRIVALS
    for flight in SAMPLE_ARRIVALS:
        row = _format_arrivals_row(flight)
        assert_true(isinstance(row, list), "Row must be a list")
        assert_eq(len(row), 8, "Arrivals row must have 8 columns")

def test_format_departures_row_no_crash():
    from display import _format_departures_row
    from offline_demo import SAMPLE_DEPARTURES
    for flight in SAMPLE_DEPARTURES:
        row = _format_departures_row(flight)
        assert_true(isinstance(row, list), "Row must be a list")
        assert_eq(len(row), 8, "Departures row must have 8 columns")

def test_format_row_with_missing_fields():
    """Rows with empty/missing optional fields must not crash."""
    from display import _format_arrivals_row, _format_departures_row
    minimal = {
        "flightId": "XX999",
        "flightType": "A",
        "airlineOperator": {},
        "locationAndTerminal": {},
        "scheduledUtc": "",
        "estimatedUtc": "",
        "actualUtc": "",
        "flightLegStatus": "",
        "viaDestinations": [],
    }
    row = _format_arrivals_row(minimal)
    assert_eq(len(row), 8)
    row = _format_departures_row(minimal)
    assert_eq(len(row), 8)

def test_show_flight_detail_no_crash():
    """show_flight_detail must not raise on any sample flight."""
    from display import show_flight_detail
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    import io, sys
    # Redirect stdout to suppress table output during test
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        for f in SAMPLE_ARRIVALS[:3]:
            show_flight_detail(f, "A")
        for f in SAMPLE_DEPARTURES[:3]:
            show_flight_detail(f, "D")
    finally:
        sys.stdout = old_stdout

def test_show_query_results_empty_no_crash():
    """show_query_results must handle an empty list gracefully."""
    from display import show_query_results
    import io, sys
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        show_query_results([], "test filter")
    finally:
        sys.stdout = old_stdout

# ================================================================
# Test group 5: Offline demo search logic
# ================================================================

def test_offline_search_finds_sk142():
    from offline_demo import SAMPLE_ARRIVALS
    matches = [f for f in SAMPLE_ARRIVALS if f.get("flightId") == "SK142"]
    assert_true(len(matches) == 1, "SK142 must appear exactly once in sample arrivals")

def test_offline_search_case_insensitive():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    all_f = SAMPLE_ARRIVALS + SAMPLE_DEPARTURES
    matches = [f for f in all_f if f.get("flightId", "").upper() == "SK142"]
    assert_true(len(matches) >= 1, "Case-insensitive search for SK142 must find a result")

def test_offline_search_unknown_flight():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    all_f = SAMPLE_ARRIVALS + SAMPLE_DEPARTURES
    matches = [f for f in all_f if f.get("flightId", "").upper() == "NOTEXIST"]
    assert_eq(len(matches), 0, "Unknown flight should return zero matches")

def test_odata_filter_delayed():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    delayed = [
        f for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES
        if f.get("flightLegStatus") == "DEL"
    ]
    assert_true(len(delayed) > 0, "Sample data must contain at least one delayed flight")

def test_odata_filter_cancelled():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    cancelled = [
        f for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES
        if f.get("flightLegStatus") == "CAN"
    ]
    assert_true(len(cancelled) > 0, "Sample data must contain at least one cancelled flight")

def test_odata_filter_sas():
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    sas = [
        f for f in SAMPLE_ARRIVALS + SAMPLE_DEPARTURES
        if isinstance(f.get("airlineOperator"), dict)
        and f["airlineOperator"].get("iata") == "SK"
    ]
    assert_true(len(sas) > 0, "Sample data must contain at least one SAS flight")

def test_odata_filter_lhr_arrivals():
    from offline_demo import SAMPLE_ARRIVALS
    lhr = [
        f for f in SAMPLE_ARRIVALS
        if isinstance(f.get("locationAndTerminal"), dict)
        and f["locationAndTerminal"].get("airportCode") == "LHR"
    ]
    assert_true(len(lhr) > 0, "Sample data must contain at least one LHR arrival")

def test_flight_ids_unique():
    """No duplicate flight IDs within arrivals or departures."""
    from offline_demo import SAMPLE_ARRIVALS, SAMPLE_DEPARTURES
    arr_ids = [f["flightId"] for f in SAMPLE_ARRIVALS]
    dep_ids = [f["flightId"] for f in SAMPLE_DEPARTURES]
    assert_eq(len(arr_ids), len(set(arr_ids)), "Arrival flightIds must be unique")
    assert_eq(len(dep_ids), len(set(dep_ids)), "Departure flightIds must be unique")

# ================================================================
# Test group 6: Main menu integration (import checks)
# ================================================================

def test_handle_offline_demo_importable():
    """The handle_offline_demo function must be importable from main."""
    import importlib
    main_mod = importlib.import_module("main")
    assert_true(
        hasattr(main_mod, "handle_offline_demo"),
        "main.py must define handle_offline_demo()"
    )

def test_offline_demo_module_importable():
    """offline_demo.py must import without errors."""
    import offline_demo  # noqa

def test_run_offline_demo_importable():
    """run_offline_demo() must exist in offline_demo.py."""
    from offline_demo import run_offline_demo
    assert_true(callable(run_offline_demo))

def test_requirements_contains_tzdata():
    """requirements.txt must include tzdata."""
    with open("requirements.txt") as fh:
        content = fh.read()
    assert_contains(content, "tzdata", "requirements.txt must list tzdata")

# ================================================================
# Run all tests
# ================================================================

if __name__ == "__main__":
    import os
    # Change to the project directory so relative imports work
    os.chdir(r"c:\Users\Mina\Desktop\swedavia-flightinfo-rebuild")
    sys.path.insert(0, r"c:\Users\Mina\Desktop\swedavia-flightinfo-rebuild")

    print()
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.CYAN + Style.BRIGHT + "  Swedavia FlightInfo Rebuild -- Offline Demo Test Suite")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60 + Style.RESET_ALL)
    print()

    groups = [
        ("Sample data structure",         [
            test_arrivals_not_empty,
            test_departures_not_empty,
            test_arrivals_have_enough_for_two_pages,
            test_departures_have_enough_for_two_pages,
            test_every_arrival_has_required_keys,
            test_every_departure_has_required_keys,
            test_all_arrivals_have_type_A,
            test_all_departures_have_type_D,
            test_no_null_flight_ids,
            test_sample_date_format,
            test_airline_operator_is_dict,
            test_location_is_dict,
            test_via_destinations_is_list,
        ]),
        ("Time conversion",               [
            test_utc_to_swedish_basic,
            test_utc_to_swedish_empty_string,
            test_utc_to_swedish_none_like,
            test_utc_full_basic,
            test_utc_full_empty,
            test_is_valid_date_good,
            test_is_valid_date_bad,
        ]),
        ("Airport helpers",               [
            test_valid_airports,
            test_invalid_airport,
            test_get_airport_name_known,
            test_get_airport_name_unknown,
            test_airport_codes_sorted,
        ]),
        ("Display helpers",               [
            test_colorize_status_known,
            test_colorize_status_unknown,
            test_format_arrivals_row_no_crash,
            test_format_departures_row_no_crash,
            test_format_row_with_missing_fields,
            test_show_flight_detail_no_crash,
            test_show_query_results_empty_no_crash,
        ]),
        ("Offline search & OData logic",  [
            test_offline_search_finds_sk142,
            test_offline_search_case_insensitive,
            test_offline_search_unknown_flight,
            test_odata_filter_delayed,
            test_odata_filter_cancelled,
            test_odata_filter_sas,
            test_odata_filter_lhr_arrivals,
            test_flight_ids_unique,
        ]),
        ("Integration / imports",         [
            test_handle_offline_demo_importable,
            test_offline_demo_module_importable,
            test_run_offline_demo_importable,
            test_requirements_contains_tzdata,
        ]),
    ]

    for group_name, tests in groups:
        print(Fore.CYAN + f"  -- {group_name} --" + Style.RESET_ALL)
        for test_fn in tests:
            run_test(test_fn.__name__.replace("test_", ""), test_fn)
        print()

    # Summary
    total  = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed

    print(Fore.CYAN + "=" * 60 + Style.RESET_ALL)
    print(
        f"  Results: "
        + Fore.GREEN + f"{passed} passed" + Style.RESET_ALL
        + "  /  "
        + (Fore.RED if failed else Fore.GREEN) + f"{failed} failed" + Style.RESET_ALL
        + f"  /  {total} total"
    )
    print(Fore.CYAN + "=" * 60 + Style.RESET_ALL)
    print()

    if failed:
        print(Fore.RED + "  Failed tests:" + Style.RESET_ALL)
        for name, ok, detail in results:
            if not ok:
                print(Fore.RED + f"    ✖  {name}" + Style.RESET_ALL)
                if detail:
                    for line in detail.strip().splitlines():
                        print(f"       {line}")
        print()
        sys.exit(1)
    else:
        print(Fore.GREEN + "  ✔  All tests passed." + Style.RESET_ALL)
        print()
        sys.exit(0)
