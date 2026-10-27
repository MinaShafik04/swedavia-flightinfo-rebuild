# web_app.py
# ----------
# Flask Web Application for Swedavia FlightInfo Rebuild.
# Provides a modern, responsive web dashboard for monitoring Swedish flights
# using the Swedavia FlightInfo API v2 and an offline sample demo mode.
#
# To run:
#   python web_app.py
#
# Then open in your browser:
#   http://127.0.0.1:5000

import os
import time
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify,
)

# Reuse existing backend modules
from airports import AIRPORTS, AIRPORT_CODES, get_airport_name, is_valid_airport
import api_client
import flight_utils
from time_utils import today_utc, is_valid_date, SWEDISH_TZ
import offline_demo

app = Flask(__name__)
# Generate a secret key for session handling
app.secret_key = os.getenv("FLASK_SECRET_KEY", "swedavia-flightinfo-secret-key-2026")

# -------------------------------------------------------
# In-Memory Cache (Protects Swedavia API quota and speeds up page loads)
# -------------------------------------------------------
# Cache format: key -> (timestamp, data)
_CACHE = {}
CACHE_TTL = 60  # Cache responses for 60 seconds

def get_cached(key):
    if key in _CACHE:
        ts, data = _CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def set_cached(key, data):
    _CACHE[key] = (time.time(), data)

def get_current_airport() -> str:
    """Returns the airport code from the session, defaulting to 'ARN'."""
    code = session.get("airport", "ARN").upper()
    return code if is_valid_airport(code) else "ARN"

def get_swedish_now_str() -> str:
    """Returns the current Swedish local time string (HH:MM)."""
    now_se = datetime.now(timezone.utc).astimezone(SWEDISH_TZ)
    return now_se.strftime("%H:%M")

@app.context_processor
def inject_global_template_vars():
    """Injects common navigation variables into all Jinja2 templates."""
    airport = get_current_airport()
    # Cache heartbeat check for 300 seconds so we don't call it on every page load
    hb_cache = get_cached("api_heartbeat")
    if hb_cache is None:
        hb_status = api_client.check_heartbeat(airport)
        set_cached("api_heartbeat", hb_status)
    else:
        hb_status = hb_cache

    return {
        "current_airport": airport,
        "airport_name": get_airport_name(airport),
        "all_airports": AIRPORTS,
        "api_status": hb_status,
        "swedish_time_now": get_swedish_now_str(),
        "today_date": today_utc(),
    }

# -------------------------------------------------------
# Airport Selection Route
# -------------------------------------------------------
@app.route("/set-airport", methods=["POST"])
def set_airport():
    new_airport = request.form.get("airport", "").strip().upper()
    if is_valid_airport(new_airport):
        session["airport"] = new_airport
        flash(f"Switched active airport to {new_airport} ({get_airport_name(new_airport)})", "success")
    else:
        flash(f"Invalid airport code: '{new_airport}'", "danger")

    # Redirect back to referring page or index
    referrer = request.referrer
    return redirect(referrer if referrer else url_for("index"))

# -------------------------------------------------------
# 1. Dashboard View
# -------------------------------------------------------
@app.route("/")
def index():
    airport = get_current_airport()
    today = today_utc()

    # Fetch arrivals & departures with caching
    arr_key = f"arr_{airport}_{today}"
    raw_arrivals = get_cached(arr_key)
    if raw_arrivals is None:
        raw_arrivals = api_client.get_arrivals(airport, today)
        set_cached(arr_key, raw_arrivals)

    dep_key = f"dep_{airport}_{today}"
    raw_departures = get_cached(dep_key)
    if raw_departures is None:
        raw_departures = api_client.get_departures(airport, today)
        set_cached(dep_key, raw_departures)

    # Normalize flights for preview
    norm_arrivals = [flight_utils.normalize_flight(f, "A") for f in (raw_arrivals or [])]
    norm_departures = [flight_utils.normalize_flight(f, "D") for f in (raw_departures or [])]

    return render_template(
        "index.html",
        active_page="dashboard",
        arrivals_count=len(norm_arrivals),
        departures_count=len(norm_departures),
        upcoming_arrivals=norm_arrivals[:6],
        upcoming_departures=norm_departures[:6],
    )

# -------------------------------------------------------
# 2. Arrivals & Departures Views (with Pagination & Filters)
# -------------------------------------------------------
@app.route("/arrivals")
def arrivals_view():
    return _render_flight_board(flight_type="A", endpoint="arrivals_view", page_title="Live Arrivals")

@app.route("/departures")
def departures_view():
    return _render_flight_board(flight_type="D", endpoint="departures_view", page_title="Live Departures")

@app.route("/refresh/<ftype>")
def flights_view_refresh(ftype):
    airport = get_current_airport()
    date_str = request.args.get("date", today_utc())
    key = f"{'arr' if ftype == 'A' else 'dep'}_{airport}_{date_str}"
    if key in _CACHE:
        del _CACHE[key]
    flash("Flight board refreshed with latest live data.", "info")
    return redirect(url_for("arrivals_view" if ftype == "A" else "departures_view", date=date_str))

def _render_flight_board(flight_type: str, endpoint: str, page_title: str):
    airport = get_current_airport()
    date_str = request.args.get("date", "").strip() or today_utc()
    search_q = request.args.get("q", "").strip().lower()
    status_filter = request.args.get("status", "").strip().upper()

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(5, int(request.args.get("per_page", 15))))
    except ValueError:
        page = 1
        per_page = 15

    cache_key = f"{'arr' if flight_type == 'A' else 'dep'}_{airport}_{date_str}"
    raw_flights = get_cached(cache_key)
    if raw_flights is None:
        if flight_type == "A":
            raw_flights = api_client.get_arrivals(airport, date_str)
        else:
            raw_flights = api_client.get_departures(airport, date_str)
        set_cached(cache_key, raw_flights)

    # Normalize all flights
    all_flights = [flight_utils.normalize_flight(f, flight_type) for f in (raw_flights or [])]

    # Apply client-side filters (query & status)
    filtered = []
    for f in all_flights:
        if status_filter and f["status_code"] != status_filter:
            continue
        if search_q:
            match = (
                search_q in f["flight_id"].lower()
                or search_q in f["location_display"].lower()
                or search_q in f["airline_display"].lower()
            )
            if not match:
                continue
        filtered.append(f)

    # Pagination calculation
    total_flights = len(filtered)
    total_pages = max(1, (total_flights + per_page - 1) // per_page)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_flights = filtered[start_idx:end_idx]

    return render_template(
        "flights.html",
        active_page="arrivals" if flight_type == "A" else "departures",
        page_title=page_title,
        flight_type=flight_type,
        endpoint=endpoint,
        flights=paginated_flights,
        selected_date=date_str,
        search_query=search_q,
        status_filter=status_filter,
        current_page=page,
        total_pages=total_pages,
        total_flights=total_flights,
        per_page=per_page,
    )

# -------------------------------------------------------
# 3. Flight Detail View
# -------------------------------------------------------
@app.route("/flight/<flight_id>")
def flight_detail_view(flight_id):
    airport = get_current_airport()
    today = today_utc()

    # Search in cached flights first
    found_flight = None
    flight_type = "A"

    for ftype, cache_prefix in (("A", "arr"), ("D", "dep")):
        cache_key = f"{cache_prefix}_{airport}_{today}"
        cached = get_cached(cache_key)
        if cached is None:
            cached = api_client.get_arrivals(airport, today) if ftype == chr(65) else api_client.get_departures(airport, today)
            set_cached(cache_key, cached)
        cached = cached or []
        for raw in cached:
            if flight_utils.get_flight_id(raw).upper() == flight_id.upper():
                found_flight = raw
                flight_type = ftype
                break
        if found_flight:
            break

    # If not in cache, use the search endpoint
    if not found_flight:
        arr_results = api_client.search_flight(airport, today, flight_id, "A")
        if arr_results:
            found_flight = arr_results[0]
            flight_type = "A"
        else:
            dep_results = api_client.search_flight(airport, today, flight_id, "D")
            if dep_results:
                found_flight = dep_results[0]
                flight_type = "D"

    # Also search sample offline data if not found in live API
    if not found_flight:
        for f in offline_demo.SAMPLE_ARRIVALS:
            if f["flightId"].upper() == flight_id.upper():
                found_flight = f
                flight_type = "A"
                break
        if not found_flight:
            for f in offline_demo.SAMPLE_DEPARTURES:
                if f["flightId"].upper() == flight_id.upper():
                    found_flight = f
                    flight_type = "D"
                    break

    if not found_flight:
        flash(f"Flight '{flight_id}' could not be located for today.", "warning")
        return redirect(url_for("search_view", flight_id=flight_id))

    normalized = flight_utils.normalize_flight(found_flight, flight_type)
    raw_json_str = json.dumps(found_flight, indent=2, ensure_ascii=False)

    return render_template(
        "flight_detail.html",
        active_page="search",
        flight=normalized,
        raw_json=raw_json_str,
        current_airport_name=get_airport_name(airport),
    )

# -------------------------------------------------------
# 4. Flight Search View
# -------------------------------------------------------
@app.route("/search")
def search_view():
    airport = get_current_airport()
    flight_id = request.args.get("flight_id", "").strip().upper()
    date_str = request.args.get("date", "").strip() or today_utc()
    search_type = request.args.get("type", "both")

    results = []
    searched = bool(flight_id)

    if searched:
        # Search arrivals if requested
        if search_type in ("both", "A"):
            arr_matches = api_client.search_flight(airport, date_str, flight_id, flight_type="A")
            for m in arr_matches:
                results.append(flight_utils.normalize_flight(m, "A"))

        # Search departures if requested
        if search_type in ("both", "D") and (not results or search_type == "D"):
            dep_matches = api_client.search_flight(airport, date_str, flight_id, flight_type="D")
            for m in dep_matches:
                results.append(flight_utils.normalize_flight(m, "D"))

    return render_template(
        "search.html",
        active_page="search",
        flight_id=flight_id,
        selected_date=date_str,
        search_type=search_type,
        results=results,
        searched=searched,
    )

# -------------------------------------------------------
# 5. OData Advanced Queries View
# -------------------------------------------------------
@app.route("/odata", methods=["GET", "POST"])
def odata_view():
    airport = get_current_airport()
    today = today_utc()
    default_filter = f"airport eq '{airport}' and scheduled eq '{today}' and flightType eq 'A'"

    results = []
    executed = False
    current_filter = default_filter

    if request.method == "POST":
        current_filter = request.form.get("filter", "").strip()
        if current_filter:
            raw_results = api_client.run_odata_query(current_filter)
            results = [flight_utils.normalize_flight(f) for f in (raw_results or [])]
            executed = True
            if results:
                flash(f"OData query returned {len(results)} matching flight(s).", "success")
            else:
                flash("OData query executed successfully, but returned 0 matches.", "info")

    return render_template(
        "odata.html",
        active_page="odata",
        current_filter=current_filter,
        results=results,
        executed=executed,
    )

# -------------------------------------------------------
# 6. Offline Demo View (SAMPLE DATA ONLY)
# -------------------------------------------------------
@app.route("/offline-demo")
def offline_demo_view():
    tab = request.args.get("tab", "arrivals")
    page = max(1, int(request.args.get("page", 1)))
    per_page = 8  # Show 8 per page to demonstrate pagination across sample data

    # 1. Sample Arrivals Tab
    if tab == "arrivals":
        norm_arr = [flight_utils.normalize_flight(f, "A") for f in offline_demo.SAMPLE_ARRIVALS]
        total_count = len(norm_arr)
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        paged_flights = norm_arr[(page - 1) * per_page : page * per_page]
        return render_template(
            "offline_demo.html",
            active_page="offline_demo",
            tab=tab,
            flights=paged_flights,
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
            per_page=per_page,
            arrivals_count=len(offline_demo.SAMPLE_ARRIVALS),
            departures_count=len(offline_demo.SAMPLE_DEPARTURES),
        )

    # 2. Sample Departures Tab
    if tab == "departures":
        norm_dep = [flight_utils.normalize_flight(f, "D") for f in offline_demo.SAMPLE_DEPARTURES]
        total_count = len(norm_dep)
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        paged_flights = norm_dep[(page - 1) * per_page : page * per_page]
        return render_template(
            "offline_demo.html",
            active_page="offline_demo",
            tab=tab,
            flights=paged_flights,
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
            per_page=per_page,
            arrivals_count=len(offline_demo.SAMPLE_ARRIVALS),
            departures_count=len(offline_demo.SAMPLE_DEPARTURES),
        )

    # 3. Sample Search Tab
    if tab == "search":
        query = request.args.get("q", "").strip().upper()
        matches = []
        if query:
            all_sample = offline_demo.SAMPLE_ARRIVALS + offline_demo.SAMPLE_DEPARTURES
            for raw in all_sample:
                if query in raw.get("flightId", "").upper():
                    ftype = raw.get("flightType", "A")
                    matches.append(flight_utils.normalize_flight(raw, ftype))

        sample_ids = sorted(list(set(f["flightId"] for f in offline_demo.SAMPLE_ARRIVALS + offline_demo.SAMPLE_DEPARTURES)))

        return render_template(
            "offline_demo.html",
            active_page="offline_demo",
            tab=tab,
            search_query=query,
            search_result=matches,
            sample_flight_ids=sample_ids,
            arrivals_count=len(offline_demo.SAMPLE_ARRIVALS),
            departures_count=len(offline_demo.SAMPLE_DEPARTURES),
        )

    # 4. Sample OData Filtering Tab
    if tab == "odata":
        filter_type = request.args.get("filter", "delayed")
        all_sample = offline_demo.SAMPLE_ARRIVALS + offline_demo.SAMPLE_DEPARTURES
        filtered = []

        if filter_type == "delayed":
            filtered = [f for f in all_sample if f.get("flightLegStatus") == "DEL"]
        elif filter_type == "cancelled":
            filtered = [f for f in all_sample if f.get("flightLegStatus") == "CAN"]
        elif filter_type == "sas":
            filtered = [
                f for f in all_sample
                if isinstance(f.get("airlineOperator"), dict)
                and f["airlineOperator"].get("iata") == "SK"
            ]
        elif filter_type == "lhr":
            filtered = [
                f for f in all_sample
                if isinstance(f.get("locationAndTerminal"), dict)
                and f["locationAndTerminal"].get("airportCode") == "LHR"
            ]

        normalized_res = [flight_utils.normalize_flight(f, f.get("flightType", "A")) for f in filtered]

        return render_template(
            "offline_demo.html",
            active_page="offline_demo",
            tab=tab,
            odata_filter=filter_type,
            odata_results=normalized_res,
            arrivals_count=len(offline_demo.SAMPLE_ARRIVALS),
            departures_count=len(offline_demo.SAMPLE_DEPARTURES),
        )

    return redirect(url_for("offline_demo_view", tab="arrivals"))

# -------------------------------------------------------
# Error Handlers
# -------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "error.html",
        error_code="404",
        error_title="Page Not Found",
        error_message="The requested flight board or page does not exist.",
    ), 404

@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.html",
        error_code="500",
        error_title="Server Error",
        error_message="An unexpected server error occurred. Please try again.",
    ), 500

if __name__ == "__main__":
    # Host on 127.0.0.1 for local testing
    print("\n=======================================================")
    print("  ✈  Swedavia FlightInfo Rebuild — Web Application")
    print("=======================================================")
    print("  Server starting locally at:")
    print("  👉  http://127.0.0.1:5000")
    print("  Press Ctrl+C to stop the server.")
    print("=======================================================\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
