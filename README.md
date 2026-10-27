# ✈ Swedavia FlightInfo Rebuild

A Python terminal application that fetches and displays real-time flight
information from the **Swedavia FlightInfo API v2**.

Built as a school assignment: *Reverse Engineer a Result*.

---

## Features

| Feature | Description |
|---------|-------------|
| ✈ Arrivals | Live arrival flights for any Swedavia airport and date |
| ✈ Departures | Live departure flights for any Swedavia airport and date |
| 🔍 Search Flight | Look up a specific flight by its flight number |
| 🔎 OData Query | Advanced filter queries using the official OData syntax |
| 📡 API Heartbeat | Check whether the Swedavia API is reachable |
| 🎬 Demo Mode | Automatic walkthrough of all features |
| 🕐 Swedish Time | All UTC times converted to Swedish local time (Europe/Stockholm) |
| 📄 Pagination | Large result sets shown page by page |
| ✅ Validation | Input validation and clear, friendly error messages |

---

## Supported Airports

All ten Swedavia airports are supported:

| IATA | Airport |
|------|---------|
| ARN | Stockholm Arlanda Airport |
| GOT | Göteborg Landvetter Airport |
| BMA | Bromma Stockholm Airport |
| MMX | Malmö Airport |
| LLA | Luleå Airport |
| UME | Umeå Airport |
| OSD | Åre Östersund Airport |
| VBY | Visby Airport |
| RNB | Ronneby Airport |
| KRN | Kiruna Airport |

---

## Requirements

- **Python 3.9 or newer** (uses the built-in `zoneinfo` module)
- A **Swedavia developer account** and API key from [developer.swedavia.com](https://developer.swedavia.com)

### Python packages

```text
flask
requests
python-dotenv
tabulate
colorama
tzdata
```

All packages are listed in `requirements.txt`.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/swedavia-flightinfo-rebuild.git
cd swedavia-flightinfo-rebuild
```

### 2. Create and activate a virtual environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

Copy the example environment file:

```bash
copy .env.example .env
```

Open `.env` in a text editor and replace `your_api_key_here` with your real API key:

```
SWEDAVIA_API_KEY=your_api_key_here
```

> ⚠️ **Never commit your `.env` file to GitHub.** It is already listed in `.gitignore`.

---

## How to Run

### Option A: Web Application (Modern Airport Dashboard)

```bash
python web_app.py
```

Then open your browser and go to:
👉 **`http://127.0.0.1:5000`**

The web dashboard provides:
- Live flight board (Arrivals & Departures) with pagination and filters
- Airport switcher in the navigation bar (ARN, GOT, MMX, etc.)
- Flight search by flight number with detailed route cards
- OData advanced query builder with 1-click presets
- Offline Demo Mode clearly labeled with **[SAMPLE DATA — NOT LIVE]**
- Live Swedish local time (Europe/Stockholm) and API connectivity indicator

---

### Option B: Terminal Application

```bash
python main.py
```

The original terminal application will start in your console with an airport selector and full interactive menu.

---

## Automated Testing

The project includes two independent test suites:

### 1. Web Application Test Suite (16 tests)
Tests routing, templates, airport switching, pagination, search, offline demo mode, and verifies that the API key is NEVER exposed in HTML:

```bash
python test_web_app.py
```

### 2. Terminal & Offline Demo Test Suite (44 tests)
Tests sample dataset, time conversion, airport dictionary, status colorization, row formatting, and search logic:

```bash
python test_offline_demo.py
```

---

## Documentation

Comprehensive project documentation is available in [`DOCUMENTATION.md`](DOCUMENTATION.md), covering:
- Reverse engineering analysis
- Schema field mapping & live API empty column resolution
- Architecture overview
- Security & secret management
- 4-minute video recording script

---

### Main Menu

```
  ┌─────────────────────────────────────────┐
  │             MAIN MENU                   │
  ├─────────────────────────────────────────┤
  │  1. ✈  Arrivals                         │
  │  2. ✈  Departures                       │
  │  3. 🔍 Search Flight                     │
  │  4. 🔎 OData Advanced Query              │
  │  5. 📡 API Heartbeat                     │
  │  6. 🎬 Demo Mode                         │
  │  7. 🌍 Change Airport                    │
  │                                         │
  │  0. 🚪 Exit                              │
  └─────────────────────────────────────────┘
```

### 1 & 2 — Arrivals / Departures

Enter a date (or press Enter for today). The application fetches all flights and
displays them in a color-coded table, paginated 12 flights per page.

### 3 — Search Flight

Enter a flight number (e.g. `SK142`), a date, and choose whether to search
arrivals, departures, or both. The application shows a detailed view if found.

### 4 — OData Advanced Query

Write an OData filter expression directly. Supported fields:

| Field | Example |
|-------|---------|
| `airport` | `airport eq 'ARN'` |
| `flightType` | `flightType eq 'A'` (`A`=arrival, `D`=departure) |
| `scheduled` | `scheduled eq '2026-10-26'` |
| `flightId` | `flightId eq 'SK142'` |

Combine with `and`:
```
airport eq 'ARN' and scheduled eq '2026-10-26' and flightType eq 'A'
```

### 5 — API Heartbeat

Checks whether the Swedavia API is reachable by making a real request to the
arrivals endpoint. No dedicated ping endpoint is used since none is documented
in the official API.

### 6 — Demo Mode

Automatically runs through all features using today's date and Stockholm Arlanda
(ARN). Useful for presentations and screen recordings.

---

## Project Structure

```
swedavia-flightinfo-rebuild/
│
├── web_app.py                ← Flask Web Application entry point
├── main.py                   ← Terminal Application entry point
├── flight_utils.py           ← Normalizes Swedavia API responses & Swedish times
├── api_client.py             ← All API calls (arrivals, departures, search, OData)
├── display.py                ← Terminal formatting, tables, colors, pagination
├── time_utils.py             ← UTC to Swedish local time conversion
├── airports.py               ← List of supported Swedavia airports
├── demo.py                   ← Live demo mode logic
├── offline_demo.py           ← Sample flight dataset & offline demo logic
│
├── templates/                ← Jinja2 HTML templates for Web Application
│   ├── base.html             ← Layout, navigation bar, airport switcher, status badges
│   ├── index.html            ← Dashboard overview & quick metrics
│   ├── flights.html          ← Paginated flight board with search and filters
│   ├── flight_detail.html    ← Comprehensive flight detail view
│   ├── search.html           ← Flight number search page
│   ├── odata.html            ← OData advanced query builder & results
│   └── offline_demo.html     ← Offline Demo board clearly marked [SAMPLE DATA]
│
├── static/                   ← Static assets
│   └── css/
│       └── style.css         ← Airport dashboard styling (Bootstrap 5 theme)
│
├── test_offline_demo.py      ← Terminal & data logic test suite (44 tests)
├── test_web_app.py           ← Web application test suite (16 tests)
│
├── .env                      ← Your API key (NEVER committed to GitHub)
├── .env.example              ← Template — copy to .env and fill in your key
├── .gitignore                ← Excludes .env, .venv, and caches from Git
└── requirements.txt          ← Python package dependencies
```

---

## API Reference

- **API:** Swedavia FlightInfo API v2
- **Base URL:** `https://api.swedavia.se/flightinfo/v2`
- **Auth header:** `Ocp-Apim-Subscription-Key`
- **Developer portal:** [developer.swedavia.com](https://developer.swedavia.com)
- **Documentation:** [Swedavia FlightInfo API PDF](https://apideveloper.swedavia.se/content/Using_the_FlightInfo_API.pdf)

---

## School Assignment Context

This project was built as part of a school assignment called
**"Reverse Engineer a Result"**. The goal was to recreate an existing
Python terminal application — originally demonstrated by another student —
using Generative AI assistance and the official Swedavia API documentation.

The application was built step by step, with a focus on beginner-friendly,
readable code and real API integration.

---

## License

This project is licensed under the [MIT License](LICENSE).
