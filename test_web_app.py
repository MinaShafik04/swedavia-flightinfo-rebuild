# test_web_app.py
# ---------------
# Automated test suite for the Flask Web Application.
# Tests routing, templates, airport switching, pagination, search,
# offline demo mode, and verifies that the API key is NEVER exposed in HTML.
#
# All tests run in isolated testing mode without making external live API calls,
# ensuring tests run fast, offline, and never exceed API rate limits.
#
# Run with:  python test_web_app.py

import os
import sys
import unittest
from unittest.mock import patch
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

import web_app
from web_app import app
import offline_demo
import flight_utils


class TestSwedaviaWebApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key-123"

    def setUp(self):
        self.client = app.test_client()
        # Seed cache with sample data so tests never hit the external Swedavia rate limits
        web_app.set_cached("api_heartbeat", True)
        web_app.set_cached("arr_ARN_2026-10-27", offline_demo.SAMPLE_ARRIVALS)
        web_app.set_cached("dep_ARN_2026-10-27", offline_demo.SAMPLE_DEPARTURES)
        web_app.set_cached("arr_GOT_2026-10-27", offline_demo.SAMPLE_ARRIVALS[:5])
        web_app.set_cached("dep_GOT_2026-10-27", offline_demo.SAMPLE_DEPARTURES[:5])

    def test_01_index_dashboard(self):
        """Dashboard route returns 200 OK and contains airport dashboard elements."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Swedavia FlightInfo", html)
        self.assertIn("ACTIVE AIRPORT", html)
        self.assertIn("Stockholm Arlanda Airport", html)

    def test_02_arrivals_page(self):
        """Arrivals page returns 200 OK and renders arrival table."""
        response = self.client.get("/arrivals?date=2026-10-27")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Live Arrivals", html)
        self.assertIn("Origin (From)", html)

    def test_03_departures_page(self):
        """Departures page returns 200 OK and renders departure table."""
        response = self.client.get("/departures?date=2026-10-27")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Live Departures", html)
        self.assertIn("Destination (To)", html)

    def test_04_set_airport_session(self):
        """Switching airport updates the session and reflects on next page load."""
        response = self.client.post("/set-airport", data={"airport": "GOT"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Göteborg Landvetter Airport", html)

    def test_05_search_page(self):
        """Flight search page loads with 200 OK."""
        response = self.client.get("/search")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Flight Search", html)
        self.assertIn("Flight Number", html)

    @patch("api_client.search_flight")
    def test_06_search_execution(self, mock_search):
        """Searching for a flight calls the search function and renders results."""
        mock_search.return_value = [offline_demo.SAMPLE_ARRIVALS[0]]
        response = self.client.get("/search?flight_id=SK142&date=2026-10-27&type=both")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("SK142", html)

    def test_07_odata_page_get(self):
        """OData query page loads with 200 OK and documentation."""
        response = self.client.get("/odata")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("OData Advanced Flight Queries", html)
        self.assertIn("OData Filter Expression", html)

    @patch("api_client.run_odata_query")
    def test_08_odata_page_post(self, mock_odata):
        """Submitting an OData query executes and renders results."""
        mock_odata.return_value = [offline_demo.SAMPLE_ARRIVALS[0]]
        response = self.client.post("/odata", data={"filter": "airport eq 'ARN'"})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("SK142", html)
        self.assertIn("1 flight(s) matched", html)

    def test_09_offline_demo_arrivals(self):
        """Offline demo arrivals tab loads sample data without API key."""
        response = self.client.get("/offline-demo?tab=arrivals")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("OFFLINE DEMO MODE — SAMPLE DATA ONLY", html)
        self.assertIn("SK142", html)
        self.assertIn("Sample Arrivals", html)

    def test_10_offline_demo_departures(self):
        """Offline demo departures tab loads sample departure flights."""
        response = self.client.get("/offline-demo?tab=departures")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Sample Departures", html)
        self.assertIn("SK143", html)

    def test_11_offline_demo_search(self):
        """Offline demo search finds sample flight without internet connection."""
        response = self.client.get("/offline-demo?tab=search&q=SK142")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("SK142", html)
        self.assertIn("CPH", html)

    def test_12_offline_demo_odata_filtering(self):
        """Offline demo simulates OData filtering on sample flights."""
        response = self.client.get("/offline-demo?tab=odata&filter=delayed")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Simulated OData Filtering", html)
        self.assertIn("LH784", html)

    def test_13_flight_detail_view(self):
        """Flight detail view card loads with full scheduling and logistics info."""
        response = self.client.get("/flight/SK142")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("SK142", html)
        self.assertIn("Flight Schedule", html)
        self.assertIn("Airport Logistics", html)

    def test_14_api_key_never_exposed(self):
        """Security: Real API key must NEVER appear in any rendered HTML output."""
        api_key = os.getenv("SWEDAVIA_API_KEY", "")
        if not api_key or len(api_key) < 5:
            self.skipTest("No API key configured to check against.")

        endpoints_to_test = [
            "/",
            "/arrivals",
            "/departures",
            "/search",
            "/odata",
            "/offline-demo",
            "/flight/SK142",
        ]
        for url in endpoints_to_test:
            res = self.client.get(url)
            html = res.get_data(as_text=True)
            self.assertNotIn(
                api_key,
                html,
                f"SECURITY VIOLATION: SWEDAVIA_API_KEY was leaked in response HTML at {url}!"
            )

    def test_15_flight_normalizer_handles_missing_fields(self):
        """flight_utils.normalize_flight handles empty/corrupted dict without crashing."""
        empty_flight = {}
        norm = flight_utils.normalize_flight(empty_flight)
        self.assertIsInstance(norm, dict)
        self.assertEqual(norm["flight_id"], "")
        self.assertEqual(norm["scheduled_time"], "--:--")
        self.assertEqual(norm["status_code"], "")

    def test_16_404_error_page(self):
        """404 error handler returns proper 404 status and error page."""
        response = self.client.get("/non-existent-endpoint-xyz")
        self.assertEqual(response.status_code, 404)
        html = response.get_data(as_text=True)
        self.assertIn("404", html)
        self.assertIn("Page Not Found", html)


if __name__ == "__main__":
    unittest.main()
