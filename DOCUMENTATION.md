# Swedavia FlightInfo Rebuild — Project Documentation

**School Assignment:** Reverse Engineer a Result  
**Project Name:** Swedavia FlightInfo Rebuild  
**Technologies:** Python 3.13, Flask 3.1, Requests, Colorama, Tabulate, ZoneInfo, Bootstrap 5  
**API:** Official Swedavia FlightInfo API v2 (`https://api.swedavia.se/flightinfo/v2`)  
**Timezone:** Europe/Stockholm (CET / CEST)  

---

## 1. Executive Summary & Assignment Objective

The objective of the **"Reverse Engineer a Result"** school assignment is to take an observed software artifact—specifically a Python terminal application demonstrated by another student (the Buster demo) querying Swedavia airports—and systematically reverse-engineer its capabilities, reconstruct its backend integration using Generative AI assistance, and extend it into a production-grade dual-interface application:
1. **Interactive Python Terminal Application:** Preserving the original CLI experience with colored tables, pagination, and airport switching.
2. **Modern Responsive Flask Web Application:** Featuring a live flight dashboard, flight boards, detail cards, OData queries, and an offline demo mode.

---

## 2. Reverse Engineering Analysis & Core Discoveries

### 2.1 Observed Features from Demonstration
The reference application exhibited six primary functionalities:
1. **Arrivals:** Fetching and listing scheduled/actual arriving flights for a specified airport and date.
2. **Departures:** Fetching and listing scheduled/actual departing flights for a specified airport and date.
3. **Flight Search:** Direct query for a flight identifier (e.g., `SK142`, `AY928`).
4. **OData Advanced Query:** Structured filter syntax supporting queries such as `airport eq 'ARN' and flightType eq 'A'`.
5. **API Heartbeat:** Connectivity verification against documented endpoints.
6. **Demo Mode:** Automated walkthrough demonstrating core capabilities.

Additional observed requirements:
- Support for all 10 Swedavia airports (ARN, GOT, BMA, MMX, LLA, UME, OSD, VBY, RNB, KRN).
- Swedish local time conversion (UTC converted to `Europe/Stockholm`).
- Terminal pagination for high-volume flight boards.
- Input validation and graceful failure handling.

### 2.2 API Investigation & The "Empty Column" Resolution
During initial live testing of the arrivals endpoint, 291–318 flights were successfully received from the API, but several columns (Status, Scheduled Time, Origin, Terminal) appeared blank.

**Root-Cause Discovery:**
The official Swedavia FlightInfo API v2 schema does not use flat keys on the flight object; instead, it uses nested property structures:
- **Scheduled Time:**
  - Live Arrivals: Nested inside `arrivalTime.scheduledUtc`
  - Live Departures: Nested inside `departureTime.scheduledUtc`
  - Offline Sample Data: Stored at top-level `scheduledUtc`
- **Flight Status:**
  - Live API: Stored in `locationAndStatus.flightLegStatus` (code) and `locationAndStatus.flightLegStatusEnglish` / `Swedish`
  - Offline Sample Data: Stored at top-level `flightLegStatus`
- **Location & Airport Names:**
  - Live Arrivals: Origin airport in `departureAirportEnglish` / `departureAirportSwedish` and `flightLegIdentifier.departureAirportIata`
  - Live Departures: Destination airport in `arrivalAirportEnglish` / `arrivalAirportSwedish` and `flightLegIdentifier.arrivalAirportIata`
  - Offline Sample Data: Stored in `locationAndTerminal.airportCode`
- **Terminal & Gate:**
  - Live API: Located inside `locationAndStatus.terminal` and `locationAndStatus.gate`

**Solution:**
We designed a shared normalization engine in `flight_utils.py` with fallback lookup logic. It checks nested live API fields first, then falls back to sample offline structures. This unified the data model so that both the terminal app and the web app display complete, accurate data without missing fields.

---

## 3. System Architecture

```
swedavia-flightinfo-rebuild/
│
├── web_app.py               ← Flask Web Application (routes, sessions, caching)
├── main.py                  ← Terminal Application (menus, terminal loops)
├── flight_utils.py          ← Normalization engine (bridges live & sample schemas)
├── api_client.py            ← Swedavia API HTTP client (auth, heartbeat, endpoints)
├── display.py               ← Terminal UI (ANSI color coding, Tabulate tables)
├── time_utils.py            ← Timezone conversion (UTC -> Europe/Stockholm)
├── airports.py              ← IATA dictionary of 10 Swedavia airports & validation
├── demo.py                  ← Automated live API walkthrough
├── offline_demo.py          ← Offline sample dataset & simulated walkthrough
│
├── templates/               ← Jinja2 HTML5 Templates
│   ├── base.html            ← Responsive layout, navbar, airport selector, status badges
│   ├── index.html           ← Airport dashboard, KPI metric cards, quick search
│   ├── flights.html         ← Paginated flight board with search and status filters
│   ├── flight_detail.html   ← Comprehensive flight detail view & raw JSON inspector
│   ├── search.html          ← Flight search page
│   ├── odata.html           ← OData query builder with 1-click examples
│   ├── offline_demo.html    ← Offline sample data dashboard
│   └── error.html           ← Custom 404 / 500 error pages
│
├── static/css/style.css     ← Aviation dashboard theme, status badges, clean tables
│
├── test_offline_demo.py     ← 44 unit tests for terminal & data logic
├── test_web_app.py          ← 16 unit tests for web application & security
│
├── .env                     ← API key configuration (excluded by .gitignore)
├── .env.example             ← Safe environment template for Git
├── .gitignore               ← Git exclusion rules
└── requirements.txt         ← Pinned Python dependencies
```

---

## 4. Key Implementation Highlights

### 4.1 Swedish Timezone Conversion
The Swedavia API transmits timestamps in UTC ISO 8601 strings (e.g. `2026-10-27T18:45:00Z`). In `time_utils.py`, conversion uses Python's standard `zoneinfo.ZoneInfo("Europe/Stockholm")` coupled with the `tzdata` package:
- Winter time: Central European Time (CET, UTC+1).
- Summer time: Central European Summer Time (CEST, UTC+2).
- Automatically applies daylight saving transitions.

### 4.2 Security & Secret Protection
- The Swedavia developer subscription key is stored strictly in `.env`.
- `api_client.py` injects the key into request headers on the server side:
  `Ocp-Apim-Subscription-Key: <KEY>`
- Neither the frontend HTML, browser JavaScript, public documentation, nor version control repository ever receives or exposes the API key.
- Automated security test (`test_14_api_key_never_exposed` in `test_web_app.py`) verifies that the key never appears in any rendered HTML response.

### 4.3 Rate Limiting & Performance Optimization
To prevent exceeding Swedavia's API request quotas:
- In-memory caching with a 60-second time-to-live (`CACHE_TTL = 60`) caches flight query results by airport and date.
- API heartbeat checks are cached for 300 seconds.
- Users can manually bypass cache via a dedicated "Refresh" button (`/refresh/<ftype>`).

### 4.4 Offline Demo & Sample Dataset
An offline mode (`offline_demo.py` and `/offline-demo`) provides 30 pre-constructed sample flights:
- 16 Arrivals across 2 pages.
- 14 Departures across 2 pages.
- Every offline screen displays prominent warning badges: `[SAMPLE DATA — NOT LIVE]`.
- All features (airport selection, arrivals, departures, flight search, OData filtering, pagination) run completely offline without an API key or internet connection.

---

## 5. Verification & Test Suite

The project includes two independent test suites:

| Test Suite | Purpose | Tests | Result |
|---|---|:---:|:---:|
| `test_offline_demo.py` | Validates sample dataset, time conversions, airport dictionary, status colorization, row formatting, and search logic | 44 | **44 / 44 PASS** |
| `test_web_app.py` | Validates Flask routes, session airport switching, pagination, template rendering, offline demo views, missing-field resilience, 404 handler, and API key leak prevention | 16 | **16 / 16 PASS** |
| **Total** | | **60** | **60 / 60 PASS (100%)** |

---

## 6. Video Presentation Guide (Minimum 4 Minutes)

Suggested script for recording the project demonstration video (e.g., using OBS Studio):

| Timeline | Topic | Action & Talking Points |
|---|---|---|
| **0:00 – 0:45** | **Introduction & Objective** | State your name, the school assignment ("Reverse Engineer a Result"), and introduce the Swedavia FlightInfo Rebuild project. Mention dual implementation: Terminal CLI + Modern Flask Web Dashboard. |
| **0:45 – 1:30** | **Terminal Application Demo** | Run `python main.py`. Show airport selection (`ARN`), view live arrivals and departures. Highlight the colored status codes (`SCH`, `ACT`, `LAN`, `DEL`, `CAN`) and Swedish local time conversion. |
| **1:30 – 2:15** | **Terminal Search & Offline Mode** | Demonstrate flight search (`SK142`) and Option 8 (Offline Demo). Explain that the offline demo uses clearly marked sample data and requires no API key. |
| **2:15 – 3:15** | **Web Application Demo** | Run `python web_app.py` and open `http://127.0.0.1:5000` in Chrome. Show the dashboard, switch airport to `GOT` (Gothenburg), navigate to Arrivals and Departures, show pagination, date filtering, and status filtering. |
| **3:15 – 3:45** | **Flight Detail & OData Queries** | Click on a flight to show the Flight Detail Card (logistics, terminal, gate, baggage claim). Open the OData Query page, execute a 1-click preset, and explain how the OData query endpoint works. |
| **3:45 – 4:15** | **Web Offline Demo & Architecture** | Open `/offline-demo`. Highlight the sample data disclaimer banner. Briefly show the clean modular code structure (`flight_utils.py`, `api_client.py`), mention the 60 passed automated tests, and conclude. |
