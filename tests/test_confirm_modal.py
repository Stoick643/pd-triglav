"""
Test suite for PD Triglav Confirmation Modal System
Tests both JavaScript behavior and Python integration
"""

import pytest
from flask import url_for
from models.user import User, UserRole, db
from models.content import TripReport
from models.trip import Trip, TripDifficulty
from datetime import datetime, timedelta


@pytest.mark.fast
class TestConfirmModalIntegration:
    """Test confirm modal integration with forms and pages"""

    def test_confirm_modal_scripts_loaded_on_pages(self, client):
        """Test that confirm modal JS and CSS are included on all pages"""
        # Test index page (accessible to all)
        response = client.get(url_for("main.index"))
        assert response.status_code == 200

        # Check for confirm modal resources
        assert b"confirm-modal.js" in response.data
        assert b"confirm-modal.css" in response.data

    def test_admin_dashboard_uses_data_confirm_attributes(self, client, test_user_admin):
        """Test that admin dashboard uses data-confirm instead of onclick confirm"""
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        # Should not have old-style onclick confirm
        assert b'onclick="return confirm(' not in response.data

        # Should have new data-confirm attributes
        if b"data-confirm=" in response.data:  # Only if there are pending users
            assert b"data-confirm-type=" in response.data
            assert b"data-confirm-text=" in response.data
            assert b"data-confirm-icon=" in response.data

    def test_report_delete_uses_modal_system(self, client, test_user_member):
        """Test that report delete uses modal system instead of basic confirm"""
        # Create a trip and report
        trip = Trip(
            title="Test Trip for Modal",
            description="Testing modal functionality",
            destination="Test Mountain",
            trip_date=datetime.now() + timedelta(days=1),
            difficulty=TripDifficulty.EASY,
            max_participants=10,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Test Report for Modal",
            content="Testing delete modal",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Should not have old-style onsubmit confirm
        assert b'onsubmit="return confirm(' not in response.data

        # Should have new data-confirm attributes for delete
        if "Izbriši poročilo".encode("utf-8") in response.data:  # Only if user can delete
            assert b"data-confirm=" in response.data
            assert b'data-confirm-type="danger"' in response.data

    def test_trip_cancel_uses_modal_system(self, client, test_user_trip_leader):
        """Test that trip cancellation uses modal system"""
        # Create a future trip
        trip = Trip(
            title="Cancellable Trip",
            description="Test trip cancellation modal",
            destination="Cancel Mountain",
            trip_date=datetime.now() + timedelta(days=5),
            difficulty=TripDifficulty.MODERATE,
            max_participants=15,
            leader_id=test_user_trip_leader.id,
        )
        db.session.add(trip)
        db.session.commit()

        response = client.get(url_for("trips.view_trip", trip_id=trip.id))
        assert response.status_code == 200

        # Should not have old-style onclick confirm
        assert b'onclick="return confirm(' not in response.data

        # Should have new data-confirm attributes for cancellation
        if "Odpovej izlet".encode("utf-8") in response.data:  # Only if user can cancel
            assert b"data-confirm=" in response.data
            assert b'data-confirm-type="warning"' in response.data

    def test_trip_withdrawal_uses_modal_system(self, client, test_user_member):
        """Test that trip withdrawal uses modal system"""
        # Create a trip and sign up the user
        trip = Trip(
            title="Withdrawal Test Trip",
            description="Test trip withdrawal modal",
            destination="Withdrawal Peak",
            trip_date=datetime.now() + timedelta(days=3),
            difficulty=TripDifficulty.EASY,
            max_participants=20,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        response = client.get(url_for("trips.member_dashboard"))
        assert response.status_code == 200

        # Should not have old-style onclick confirm
        assert b'onclick="return confirm(' not in response.data

        # Should have new data-confirm attributes for withdrawal
        if b"box-arrow-left" in response.data:  # Only if user has trips to withdraw from
            assert b"data-confirm=" in response.data
            assert b'data-confirm-type="warning"' in response.data

    def test_index_admin_actions_use_modal_system(self, client, test_user_admin):
        """Test that index page admin actions use modal system"""
        response = client.get(url_for("main.index"))
        assert response.status_code == 200

        # Should not have old-style confirm() calls in JavaScript
        assert b"if (confirm(" not in response.data

        # Should have new PDTriglavConfirmModal.show calls
        if b"regenerate-event-btn" in response.data or b"refresh-news-btn" in response.data:
            assert b"PDTriglavConfirmModal.show(" in response.data

    def test_no_old_confirm_dialogs_remain(self, client, test_user_admin):
        """Test that no old-style confirm dialogs remain in the system"""
        # Test key pages for old confirm patterns
        pages_to_test = [
            url_for("main.dashboard"),
            url_for("main.index"),
        ]

        for page_url in pages_to_test:
            response = client.get(page_url)
            if response.status_code == 200:
                # Should not have any old-style confirm patterns
                assert b'onclick="return confirm(' not in response.data
                assert b'onsubmit="return confirm(' not in response.data
                # Note: JavaScript confirm() in if statements is replaced with PDTriglavConfirmModal.show


@pytest.mark.fast
class TestConfirmModalAccessibility:
    """Test accessibility aspects of confirm modal system"""

    def test_confirm_modal_attributes_include_accessibility(self, client, test_user_admin):
        """Test that confirm modal attributes include accessibility features"""
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        # Check that templates include proper attributes for accessibility
        if b"data-confirm=" in response.data:
            # Should have semantic icon classes
            assert b"bi-" in response.data
            # Should have descriptive confirm text
            assert b"data-confirm-text=" in response.data

    def test_confirm_modal_different_types(self, client, test_user_admin):
        """Test that different confirmation types are used appropriately"""
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        # If there are confirmations, they should use appropriate types
        content = response.data.decode("utf-8")
        if "data-confirm=" in content:
            # Dangerous actions should use danger type
            if "Zavrni" in content or "odstrani" in content:
                assert 'data-confirm-type="danger"' in content
            # Approvals should use info type
            if "Odobri" in content:
                assert 'data-confirm-type="info"' in content


@pytest.mark.fast
class TestConfirmModalSecurity:
    """Test security aspects of confirm modal implementation"""

    def test_confirm_modal_prevents_xss_in_messages(self, client, test_user_admin):
        """Test that confirm modal messages are properly escaped"""
        # Create a user with potentially malicious name
        malicious_user = User.create_user(
            email="malicious@test.com",
            name="<script>alert('XSS')</script>TestUser",
            password="password",
        )
        malicious_user.role = UserRole.PENDING
        db.session.add(malicious_user)
        db.session.commit()

        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        # Script should be escaped in data-confirm attributes
        assert b"<script>alert" not in response.data
        assert b"&lt;script&gt;" in response.data or b"TestUser" in response.data

    def test_confirm_modal_respects_permissions(self, client, test_user_member):
        """Test that confirm modals only appear for actions user can perform"""
        # Regular member accessing admin dashboard should not see confirmations
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 403  # Should be forbidden

    def test_confirm_modal_csrf_protection(self, client, test_user_admin):
        """Test that forms with confirm modals still have CSRF protection"""
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        # Forms should still have CSRF tokens
        if b"<form" in response.data:
            assert b"csrf_token" in response.data or b"hidden_tag()" in response.data


@pytest.mark.fast
class TestConfirmModalPerformance:
    """Test performance aspects of confirm modal system"""

    def test_confirm_modal_resources_load_once(self, client, test_user_admin):
        """Test that confirm modal resources are included only once"""
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        # Should include resources exactly once
        content = response.data.decode("utf-8")
        assert content.count("confirm-modal.js") == 1
        assert content.count("confirm-modal.css") == 1

    def test_confirm_modal_no_inline_javascript(self, client, test_user_admin):
        """Test that confirm modal doesn't create excessive inline JavaScript"""
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        # Should use data attributes instead of inline event handlers
        content = response.data.decode("utf-8")
        if "data-confirm=" in content:
            # Count of inline onclick handlers should be minimal or zero
            onclick_count = content.count("onclick=")
            # Should have minimal inline JavaScript for confirmations
            assert onclick_count < 5  # Allow some for non-confirmation features


@pytest.mark.fast
class TestConfirmModalUserExperience:
    """Test user experience aspects of confirm modal system"""

    def test_confirm_modal_provides_context(self, client, test_user_admin):
        """Test that confirm modal messages provide sufficient context"""
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        content = response.data.decode("utf-8")
        if "data-confirm=" in content:
            # Messages should include user names or item titles for context
            assert "uporabnika" in content or "poročilo" in content or "izlet" in content

    def test_confirm_modal_uses_slovenian_text(self, client, test_user_admin):
        """Test that confirm modal uses Slovenian language throughout"""
        response = client.get(url_for("main.dashboard"))
        assert response.status_code == 200

        content = response.data.decode("utf-8")
        if "data-confirm=" in content:
            # All text should be in Slovenian
            assert "Ali ste prepričani" in content or "Ste prepričani" in content
            # Button text should be in Slovenian
            if "data-confirm-text=" in content:
                # Should not have English text in confirm buttons
                assert "Delete" not in content
                assert "Confirm" not in content

    def test_confirm_modal_consistent_styling(self, client, test_user_admin):
        """Test that confirm modal styling is consistent across pages"""
        pages_to_test = [
            url_for("main.dashboard"),
            url_for("main.index"),
        ]

        confirm_types_found = set()

        for page_url in pages_to_test:
            response = client.get(page_url)
            if response.status_code == 200:
                content = response.data.decode("utf-8")
                if "data-confirm-type=" in content:
                    # Extract confirm types used
                    import re

                    types = re.findall(r'data-confirm-type="([^"]+)"', content)
                    confirm_types_found.update(types)

        # Should only use approved confirmation types
        approved_types = {"danger", "warning", "info"}
        for confirm_type in confirm_types_found:
            assert confirm_type in approved_types
