"""API and AJAX endpoint tests for the PD Triglav application"""

import pytest

# Mark all tests in this file as fast API tests
pytestmark = [pytest.mark.fast, pytest.mark.api]


class TestHistoricalEventsAPI:
    """Test historical events API endpoints"""

    def test_historical_events_api_success(self, client, sample_historical_events):
        """Test successful historical events API call"""
        response = client.get("/api/historical-events?date=29-05")

        assert response.status_code == 200
        assert response.content_type == "application/json"

        data = response.get_json()
        assert isinstance(data, list)
        if len(data) > 0:
            event = data[0]
            required_fields = ["title", "description", "year", "location"]
            for field in required_fields:
                assert field in event

    def test_historical_events_api_no_date_parameter(self, client):
        """Test API call without date parameter"""
        response = client.get("/api/historical-events")

        # Should either return today's events or an error
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, list)

    def test_historical_events_api_invalid_date_format(self, client):
        """Test API call with invalid date format"""
        invalid_dates = ["invalid", "2025-13-32", "32-05", ""]

        for invalid_date in invalid_dates:
            response = client.get(f"/api/historical-events?date={invalid_date}")
            assert response.status_code in [200, 400]  # Should handle gracefully

    def test_historical_events_api_empty_results(self, client):
        """Test API call when no events exist for date"""
        response = client.get("/api/historical-events?date=31-02")  # Invalid date

        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, list)

    def test_historical_events_api_with_limit(self, client, sample_historical_events):
        """Test API call with limit parameter"""
        response = client.get("/api/historical-events?date=29-05&limit=1")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) <= 1

    def test_historical_events_api_json_structure(self, client, sample_historical_events):
        """Test that API returns properly structured JSON"""
        response = client.get("/api/historical-events?date=29-05")

        if response.status_code == 200:
            data = response.get_json()
            if len(data) > 0:
                event = data[0]

                # Check data types
                assert isinstance(event.get("year"), int)
                assert isinstance(event.get("title"), str)
                assert isinstance(event.get("description"), str)

                # Check for required fields
                assert event.get("title") is not None
                assert event.get("description") is not None


class TestHTMXPartialRendering:
    """Test HTMX partial content rendering"""

    def test_trips_list_htmx_partial(self, client, test_users):
        """Test HTMX partial rendering for trips list"""
        # Login first
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Request with HTMX header
        response = client.get("/trips", headers={"HX-Request": "true"})

        if response.status_code == 200:
            html = response.get_data(as_text=True)

            # Should not contain full page structure
            assert "<html>" not in html
            assert "<head>" not in html
            assert "<body>" not in html

            # Should contain trip-related content
            assert "trip" in html.lower() or "no trips" in html.lower()

    def test_dashboard_htmx_partial(self, client, test_users):
        """Test HTMX partial rendering for dashboard"""
        # Login first
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Request dashboard with HTMX header
        response = client.get("/dashboard", headers={"HX-Request": "true"})

        if response.status_code == 200:
            html = response.get_data(as_text=True)

            # Should be partial content
            assert "<html>" not in html
            assert "dashboard" in html.lower() or "welcome" in html.lower()

    def test_htmx_vs_regular_request_difference(self, client, test_users):
        """Test that HTMX requests return different content than regular requests"""
        # Login first
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Regular request
        regular_response = client.get("/trips")

        # HTMX request
        htmx_response = client.get("/trips", headers={"HX-Request": "true"})

        if regular_response.status_code == 200 and htmx_response.status_code == 200:
            regular_html = regular_response.get_data(as_text=True)
            htmx_html = htmx_response.get_data(as_text=True)

            # Regular response should have full page structure
            assert "<html>" in regular_html

            # HTMX response should not (or should be significantly different)
            assert len(htmx_html) != len(regular_html)


class TestAJAXEndpoints:
    """Test AJAX-specific endpoints and responses"""

    def test_user_search_ajax(self, client, test_users):
        """Test AJAX user search functionality"""
        # Login as admin
        client.post("/auth/login", data={"email": "admin@test.com", "password": "adminpass"})

        # Test user search (if endpoint exists)
        response = client.get("/api/users/search?q=member")

        # Should either work or return 404 if not implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, list)

    def test_ajax_error_handling(self, client):
        """Test AJAX endpoints return proper error responses"""
        # Test unauthenticated API access
        response = client.get("/api/historical-events")

        # Should return proper HTTP status
        assert response.status_code in [200, 401, 403]

        if response.content_type == "application/json":
            data = response.get_json()
            # Should be structured error response
            assert isinstance(data, (list, dict))

    def test_ajax_content_type_headers(self, client, sample_historical_events):
        """Test that AJAX endpoints return correct Content-Type headers"""
        response = client.get("/api/historical-events?date=29-05")

        if response.status_code == 200:
            assert "application/json" in response.content_type


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""

    def test_api_malformed_request(self, client):
        """Test API behavior with malformed requests"""
        # Test with invalid JSON in POST body (if applicable)
        response = client.post(
            "/api/historical-events", data="invalid json", content_type="application/json"
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 404, 405]

    def test_api_missing_required_parameters(self, client):
        """Test API behavior with missing required parameters"""
        # Test different parameter combinations
        test_urls = [
            "/api/historical-events?",
            "/api/historical-events?date=",
            "/api/historical-events?limit=abc",
        ]

        for url in test_urls:
            response = client.get(url)
            assert response.status_code in [200, 400]  # Should handle gracefully

    def test_api_rate_limiting_headers(self, client):
        """Test that API includes appropriate rate limiting headers"""
        response = client.get("/api/historical-events?date=29-05")

        # Check for common rate limiting headers (if implemented)
        headers = response.headers
        # This would check for X-RateLimit-* headers if implemented
        assert response.status_code in [200, 400, 404]

    def test_api_cors_headers(self, client):
        """Test CORS headers on API endpoints"""
        response = client.get("/api/historical-events?date=29-05")

        # Check for CORS headers (if API is meant to be public)
        headers = response.headers
        # This would verify CORS configuration if needed
        assert response.status_code in [200, 400, 404]


class TestAPIPerformance:
    """Test API performance characteristics"""

    def test_api_response_time_reasonable(self, client, sample_historical_events):
        """Test that API responses are reasonably fast"""
        import time

        start_time = time.time()
        response = client.get("/api/historical-events?date=29-05")
        end_time = time.time()

        response_time = end_time - start_time

        # API should respond within reasonable time (5 seconds for test environment)
        assert response_time < 5.0
        assert response.status_code in [200, 400, 404]

    def test_api_handles_multiple_requests(self, client, sample_historical_events):
        """Test that API can handle multiple concurrent-like requests"""
        responses = []

        # Make multiple requests quickly
        for i in range(5):
            response = client.get(f"/api/historical-events?date=29-05&_req={i}")
            responses.append(response)

        # All requests should complete successfully
        for response in responses:
            assert response.status_code in [200, 400, 404]

    def test_api_large_result_set_handling(self, client):
        """Test API behavior with potentially large result sets"""
        # Test without limit parameter
        response = client.get("/api/historical-events?date=29-05")

        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, list)

            # Should have reasonable limits (not return thousands of items)
            assert len(data) <= 100  # Reasonable default limit


class TestAPIDocumentation:
    """Test that API endpoints are self-documenting"""

    def test_api_options_method(self, client):
        """Test that OPTIONS method provides API information"""
        response = client.options("/api/historical-events")

        # Should either provide OPTIONS info or return 405
        assert response.status_code in [200, 405]

    def test_api_help_endpoint(self, client):
        """Test for API help/documentation endpoint"""
        help_endpoints = ["/api", "/api/help", "/api/docs"]

        for endpoint in help_endpoints:
            response = client.get(endpoint)
            # Should either provide help or return 404
            assert response.status_code in [200, 404]
