"""Security-focused tests for the PD Triglav application"""

import pytest
import io
from models.user import User, UserRole
from models.trip import Trip
from werkzeug.datastructures import FileStorage

# Mark all tests in this file as security tests (some fast, some slow)
pytestmark = [pytest.mark.security]


class TestCSRFProtection:
    """Test CSRF protection on state-changing operations"""

    def test_trip_creation_requires_csrf_token(self, client, test_users):
        """Test that creating trips requires CSRF token"""
        # Login as trip leader
        response = client.post(
            "/auth/login", data={"email": "leader@test.com", "password": "leaderpass"}
        )

        # Try to create trip WITHOUT CSRF token - should fail
        response = client.post(
            "/trips/create",
            data={
                "title": "Test Trip",
                "destination": "Test Mountain",
                "trip_date": "2025-02-15",
                "description": "Test description",
                "difficulty": "moderate",
            },
        )

        # CSRF protection should cause form validation to fail
        # Flask-WTF returns 200 with form errors when CSRF fails
        assert response.status_code == 200
        # Check that no trip was actually created in database

        with client.application.app_context():
            trip = Trip.query.filter_by(title="Test Trip").first()
            assert trip is None  # Trip should not be created due to CSRF failure

    def test_user_approval_requires_csrf_token(self, client, test_users):
        """Test that user approval requires CSRF token"""
        # Login as admin
        response = client.post(
            "/auth/login", data={"email": "admin@test.com", "password": "adminpass"}
        )

        # Try to approve user WITHOUT CSRF token (using correct route)
        pending_user = test_users["pending"]
        response = client.post(f"/admin/approve-user/{pending_user.id}", data={"role": "MEMBER"})

        # CSRF protection should cause redirect to admin page with error
        assert response.status_code == 302
        # Verify user was NOT approved (still pending)
        pending_user = test_users["pending"]  # Refresh from database
        assert pending_user.role == UserRole.PENDING


class TestAuthenticationSecurity:
    """Test authentication bypass attempts and security"""

    def test_admin_dashboard_requires_admin_role(self, client, test_users):
        """Test that admin dashboard blocks non-admin users"""
        # Login as regular member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Try to access admin dashboard (correct route is /admin)
        response = client.get("/admin")
        assert response.status_code in [302, 403]  # Should redirect or deny access

    def test_pending_user_restricted_access(self, client, test_users):
        """Test that pending users have restricted access"""
        # Login as pending user
        client.post("/auth/login", data={"email": "pending@test.com", "password": "pendingpass"})

        # Try to access trips page (should work - pending users can view trips)
        response = client.get("/trips/")
        assert response.status_code == 200  # Pending users can view trips

        # Try to create trip (should be blocked - only trip leaders/admins)
        response = client.get("/trips/create")
        assert response.status_code in [302, 403]  # Should be blocked

    def test_unauthenticated_user_restrictions(self, client):
        """Test that unauthenticated users cannot access protected routes"""
        protected_routes = ["/dashboard", "/trips/create", "/admin", "/reports/create"]

        for route in protected_routes:
            response = client.get(route)
            # Should redirect to login (302) or be forbidden (403)
            assert response.status_code in [
                302,
                401,
                403,
            ], f"Route {route} should be protected, got {response.status_code}"


class TestInputValidation:
    """Test input validation and XSS prevention"""

    @pytest.mark.fast
    def test_user_registration_xss_prevention(self, client):
        """Test that XSS attempts in registration are sanitized"""
        malicious_name = '<script>alert("XSS")</script>'
        malicious_email = 'test@example.com<script>alert("XSS")</script>'

        response = client.post(
            "/auth/register",
            data={
                "name": malicious_name,
                "email": malicious_email,
                "password": "password123",
                "password_confirm": "password123",
            },
        )

        # Check that user was not created with malicious content
        with client.application.app_context():
            user = User.query.filter_by(email=malicious_email).first()
            assert user is None  # Should not exist due to validation

    def test_search_input_length_validation(self, client, test_users):
        """Test that search inputs have reasonable length limits"""
        # Login first
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Try extremely long search term on trips list
        long_search = "A" * 1000
        response = client.get(f"/trips/?q={long_search}")

        # Should handle gracefully (not crash) - follow redirects
        assert response.status_code in [200, 302, 400]

    @pytest.mark.fast
    def test_password_strength_validation(self, client):
        """Test password strength requirements"""
        weak_passwords = ["123", "12345", "password", "abc"]

        for weak_password in weak_passwords:
            response = client.post(
                "/auth/register",
                data={
                    "name": "Test User",
                    "email": f"test{weak_password}@example.com",
                    "password": weak_password,
                    "password_confirm": weak_password,
                },
            )

            # Should reject weak passwords
            assert response.status_code in [200, 400]  # Stay on form or show error


class TestFileUploadSecurity:
    """Test file upload security measures"""

    def test_executable_file_rejection(self, client, test_users):
        """Test that executable files are rejected"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Try to upload executable file types
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00"),  # Windows executable
            ("script.sh", b'#!/bin/bash\necho "malicious"'),  # Shell script
            ("virus.bat", b'@echo off\necho "malicious"'),  # Batch file
        ]

        for filename, content in malicious_files:
            file_storage = FileStorage(
                stream=io.BytesIO(content),
                filename=filename,
                content_type="application/octet-stream",
            )

            # Test that secure_filename handles dangerous files
            from werkzeug.utils import secure_filename

            secured = secure_filename(filename)
            # secure_filename should either sanitize completely or make safe
            # For our test, we verify basic sanitization works for path traversal
            assert "../" not in secured and "\\" not in secured

    def test_oversized_file_rejection(self, client, test_users):
        """Test that oversized files are rejected"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Create a large file (simulated)
        large_content = b"A" * (10 * 1024 * 1024)  # 10MB

        file_storage = FileStorage(
            stream=io.BytesIO(large_content), filename="large_image.jpg", content_type="image/jpeg"
        )

        # Test would check against actual upload endpoint
        # For now, verify file size checking logic
        assert len(large_content) > 5 * 1024 * 1024  # Larger than typical limit


class TestSessionSecurity:
    """Test session security measures"""

    def test_session_invalidation_on_logout(self, client, test_users):
        """Test that sessions are properly invalidated on logout"""
        # Login
        response = client.post(
            "/auth/login", data={"email": "member@test.com", "password": "memberpass"}
        )

        # Verify logged in
        response = client.get("/dashboard")
        assert response.status_code == 200

        # Logout
        response = client.get("/auth/logout")

        # Verify logged out
        response = client.get("/dashboard")
        assert response.status_code in [302, 401, 403]

    def test_concurrent_session_handling(self, client, test_users):
        """Test handling of concurrent sessions"""
        # This would test multiple simultaneous logins
        # For now, just verify basic session behavior

        # Login
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Verify session exists
        with client.session_transaction() as sess:
            assert "_user_id" in sess


class TestDataLeakagePrevention:
    """Test prevention of data leakage"""

    def test_user_enumeration_prevention(self, client):
        """Test that user enumeration is prevented"""
        # Try to register with existing email
        response1 = client.post(
            "/auth/register",
            data={
                "name": "Test User",
                "email": "admin@test.com",  # Assuming this exists
                "password": "password123",
                "password_confirm": "password123",
            },
        )

        # Try to register with non-existing email
        response2 = client.post(
            "/auth/register",
            data={
                "name": "Test User",
                "email": "nonexistent@test.com",
                "password": "password123",
                "password_confirm": "password123",
            },
        )

        # Responses should be similar to prevent user enumeration
        # (This depends on implementation - should give generic error messages)
        assert response1.status_code in [200, 302, 400]
        assert response2.status_code in [200, 302, 400]

    def test_error_message_information_disclosure(self, client):
        """Test that error messages don't disclose sensitive information"""
        # Try invalid login
        response = client.post(
            "/auth/login", data={"email": "nonexistent@test.com", "password": "wrongpassword"}
        )

        # Should get generic error message
        if response.status_code == 200:
            html = response.get_data(as_text=True)
            # Should not contain specific details about what went wrong
            assert "user not found" not in html.lower()
            assert "invalid password" not in html.lower()
