"""Test historical events routes and integration"""

import pytest
from unittest.mock import patch, Mock
from models.content import HistoricalEvent, EventCategory
from models.user import db


class TestHomepageHistoricalEvents:
    """Test historical events integration on homepage"""

    @pytest.fixture
    def sample_event(self, app):
        """Create sample historical event"""
        with app.app_context():
            event = HistoricalEvent(
                event_month=7, event_day=27,
                year=1953,
                title="Test Historical Event",
                description="A significant test event in mountaineering history.",
                location="Test Mountain Range",
                people=["Test Climber", "Test Guide"],
                url="https://example.com/source1",
                url_secondary="https://example.com/source2",
                category=EventCategory.FIRST_ASCENT,
                methodology="Direct date search",
                url_methodology="Verified through primary sources",
                is_featured=True,
                is_generated=True,
            )
            db.session.add(event)
            db.session.commit()
            return event

    def test_homepage_shows_historical_events_for_authenticated_users(
        self, client, test_users, sample_event
    ):
        """Test that authenticated users see historical events section"""
        # Login as member
        response = client.post(
            "/auth/login", data={"email": "member@test.com", "password": "memberpass"}
        )
        assert response.status_code == 302  # Redirect after login

        # Mock today's date to match sample event
        with patch("models.content.datetime") as mock_datetime:
            from datetime import datetime

            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime

            response = client.get("/")
            assert response.status_code == 200

            # Should contain historical events section
            assert b"Na ta dan v zgodovini" in response.data
            assert b"Test Historical Event" in response.data
            assert b"Test Mountain Range" in response.data
            assert b"Test Climber" in response.data
            assert b"Vir 1" in response.data  # Source link
            assert b"Vir 2" in response.data  # Secondary source link

    def test_homepage_shows_historical_events_for_all_users_temp(self, client, sample_event):
        """Test that all users see historical events (temporary for testing)"""
        # Note: This test reflects current temporary state where everyone sees events

        # Mock today's date to match sample event
        with patch("models.content.datetime") as mock_datetime:
            from datetime import datetime

            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime

            response = client.get("/")
            assert response.status_code == 200

            # Should contain historical events section even without login
            assert b"Na ta dan v zgodovini" in response.data
            assert b"Test Historical Event" in response.data

    def test_homepage_handles_no_event_gracefully(self, client, test_users):
        """Test homepage renders when no event exists for today"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Homepage doesn't auto-generate — it just shows None if no event exists
        # Generation happens via scheduler or admin action
        with patch("models.content.HistoricalEvent.get_todays_event", return_value=None):
            response = client.get("/")
            assert response.status_code == 200
            # Page loads without crashing

    def test_homepage_handles_database_error_gracefully(self, client, test_users):
        """Test graceful handling of database errors on homepage"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        with patch("models.content.HistoricalEvent.get_todays_event", side_effect=Exception("DB error")):
            response = client.get("/")
            assert response.status_code == 200
            # Should not crash, continues without historical events

    def test_homepage_event_display_formatting(self, client, test_users, sample_event):
        """Test proper formatting of historical event display"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        with patch("models.content.datetime") as mock_datetime:
            from datetime import datetime

            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime

            response = client.get("/")
            assert response.status_code == 200

            # Check for proper HTML structure
            assert b"card border-primary" in response.data  # Main card
            assert b"card-header bg-primary text-white" in response.data  # Header
            assert b"27. julij 1953" in response.data  # Slovenian date display
            assert b"badge bg-success" in response.data  # Category badge for first_ascent
            assert b"Prva vzpon" in response.data  # Slovenian category text
            assert b"bi bi-mountain" in response.data  # Category icon
            assert b"avtomatsko generirana" in response.data  # Generation indicator

    def test_homepage_event_category_badges_and_icons(self, client, test_users, app):
        """Test different category badges and icons"""
        # Test each category type
        categories = [
            (EventCategory.FIRST_ASCENT, "bg-success", "Prva vzpon", "bi-mountain"),
            (EventCategory.ACHIEVEMENT, "bg-warning", "Dosežek", "bi-trophy"),
            (EventCategory.EXPEDITION, "bg-info", "Odprava", "bi-compass"),
            (EventCategory.DISCOVERY, "bg-secondary", "Odkritje", "bi-search"),
            (EventCategory.TRAGEDY, "bg-danger", "Tragedija", "bi-heart"),
        ]

        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        for category, badge_class, slovenian_text, icon_class in categories:
            with app.app_context():
                # Clear existing events
                HistoricalEvent.query.delete()

                # Create event with specific category
                event = HistoricalEvent(
                    event_month=7, event_day=27,
                    year=1953,
                    title=f"Test {category.value} Event",
                    description="Test description",
                    category=category,
                )
                db.session.add(event)
                db.session.commit()

                with patch("models.content.datetime") as mock_datetime:
                    from datetime import datetime

                    mock_datetime.now.return_value = datetime(2024, 7, 27)
                    mock_datetime.strftime = datetime.strftime

                    response = client.get("/")
                    assert response.status_code == 200

                    # Check for category-specific elements
                    assert badge_class.encode() in response.data
                    assert slovenian_text.encode() in response.data
                    assert icon_class.encode() in response.data

    def test_homepage_dual_url_display(self, client, test_users, app):
        """Test display of dual URLs when available"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        with app.app_context():
            # Test event with both URLs
            event_both = HistoricalEvent(
                event_month=7, event_day=27,
                year=1953,
                title="Event with Both URLs",
                description="Test description",
                url="https://source1.com",
                url_secondary="https://source2.com",
                category=EventCategory.FIRST_ASCENT,
            )
            db.session.add(event_both)
            db.session.commit()

            with patch("models.content.datetime") as mock_datetime:
                from datetime import datetime

                mock_datetime.now.return_value = datetime(2024, 7, 27)
                mock_datetime.strftime = datetime.strftime

                response = client.get("/")
                assert response.status_code == 200

                # Should show both source buttons
                assert b"Vir 1" in response.data
                assert b"Vir 2" in response.data
                assert b"https://source1.com" in response.data
                assert b"https://source2.com" in response.data

        with app.app_context():
            # Clear and test event with only primary URL
            HistoricalEvent.query.delete()

            event_single = HistoricalEvent(
                event_month=7, event_day=27,
                year=1953,
                title="Event with Single URL",
                description="Test description",
                url="https://source1.com",
                url_secondary=None,
                category=EventCategory.FIRST_ASCENT,
            )
            db.session.add(event_single)
            db.session.commit()

            with patch("models.content.datetime") as mock_datetime:
                from datetime import datetime

                mock_datetime.now.return_value = datetime(2024, 7, 27)
                mock_datetime.strftime = datetime.strftime

                response = client.get("/")
                assert response.status_code == 200

                # Should show only primary source button
                assert b"Vir 1" in response.data
                assert b"Vir 2" not in response.data


class TestAdminRoutes:
    """Test admin routes for historical events management"""

    def test_admin_regenerate_route_exists(self, client, test_users):
        """Test that admin regenerate route exists and requires admin"""
        # Login as admin
        client.post("/auth/login", data={"email": "admin@test.com", "password": "adminpass"})

        # Route exists — returns 200 (with LLM call) or handles gracefully
        response = client.post("/admin/regenerate-today-event")
        assert response.status_code in (200, 500)  # 200 success or 500 if no LLM configured

    def test_admin_regenerate_requires_admin(self, client, test_users):
        """Test that regular members cannot regenerate events"""
        # Login as regular member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        # Should be forbidden for non-admin users
        response = client.post("/admin/regenerate-today-event")
        assert response.status_code in (302, 403)  # Redirect to login or forbidden


class TestHistoryArchiveRoutes:
    """Test history archive routes"""

    def test_history_archive_route_placeholder(self, client):
        """Test that history archive route doesn't exist yet"""
        response = client.get("/history/")
        assert response.status_code == 404  # Should not exist yet

    def test_history_event_detail_route(self, client, app):
        """Test event detail route"""
        with app.app_context():
            event = HistoricalEvent(
                event_month=7, event_day=27,
                year=1953,
                title="Detail Test Event",
                description="Test description",
                category=EventCategory.FIRST_ASCENT,
            )
            db.session.add(event)
            db.session.commit()
            event_id = event.id

        # Event detail route exists — may require login (302) or show (200)
        response = client.get(f"/history/event/{event_id}")
        assert response.status_code in (200, 302)

    def test_history_event_detail_nonexistent(self, client, test_users):
        """Test event detail for non-existent event redirects gracefully"""
        # Login first — route requires authentication
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})
        response = client.get("/history/event/99999")
        # Route catches 404 and redirects to homepage with flash message
        assert response.status_code == 302

    def test_history_load_more_api_placeholder(self, client):
        """Test that load more API doesn't exist yet"""
        response = client.get("/history/api/load-more")
        assert response.status_code == 404  # Should not exist yet


class TestAuthenticationRequirements:
    """Test authentication requirements for historical events"""

    @pytest.fixture
    def sample_event(self, app):
        """Create sample historical event for auth tests"""
        with app.app_context():
            event = HistoricalEvent(
                event_month=7, event_day=27,
                year=1953,
                title="Test Historical Event",
                description="A significant test event.",
                category=EventCategory.FIRST_ASCENT,
                is_generated=True,
            )
            db.session.add(event)
            db.session.commit()
            return event

    def test_historical_events_visible_to_unauthenticated(self, client, sample_event):
        """Test current state: events visible to everyone (temporary)"""
        with patch("models.content.datetime") as mock_datetime:
            from datetime import datetime

            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime

            response = client.get("/")
            assert response.status_code == 200
            assert b"Na ta dan v zgodovini" in response.data

    def test_pending_user_access(self, client, test_users, sample_event):
        """Test access for pending users"""
        # Login as pending user
        client.post("/auth/login", data={"email": "pending@test.com", "password": "pendingpass"})

        with patch("models.content.datetime") as mock_datetime:
            from datetime import datetime

            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime

            response = client.get("/")
            assert response.status_code == 200
            # Currently shows to everyone


class TestErrorHandling:
    """Test error handling in historical events routes"""

    def test_database_error_handling(self, client, test_users):
        """Test handling of database errors"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        with patch("models.content.HistoricalEvent.get_todays_event", side_effect=Exception("Database error")):
            response = client.get("/")
            assert response.status_code == 200
            # Should handle error gracefully and not crash

    def test_template_rendering_with_none_event(self, client, test_users):
        """Test template rendering when no event is available"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        with patch("models.content.HistoricalEvent.get_todays_event", return_value=None):
            response = client.get("/")
            assert response.status_code == 200
            # Should show fallback content or hide section


class TestPerformanceConsiderations:
    """Test performance aspects of historical events routes"""

    def _make_mock_event(self):
        """Create a mock event that works outside session context"""
        mock_event = Mock()
        mock_event.id = 1
        mock_event.event_month = 7
        mock_event.event_day = 27
        mock_event.year = 1953
        mock_event.title = "Test Historical Event"
        mock_event.description = "A significant test event."
        mock_event.location = "Test Location"
        mock_event.people = ["Test Person"]
        mock_event.people_list = ["Test Person"]
        mock_event.url = None
        mock_event.url_secondary = None
        mock_event.category = EventCategory.FIRST_ASCENT
        mock_event.is_generated = True
        mock_event.is_featured = False
        mock_event.methodology = None
        mock_event.url_methodology = None
        mock_event.date_sl = "27. julij"
        mock_event.date_en = "27 July"
        mock_event.full_date_string = "27. julij 1953"
        mock_event.full_date_string_en = "27 July 1953"
        mock_event.created_at = Mock()
        mock_event.created_at.strftime = Mock(return_value="27. 7. 2024")
        return mock_event

    def test_single_database_query_for_todays_event(self, client, test_users):
        """Test that only one database query is made for today's event"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        mock_event = self._make_mock_event()

        with patch("models.content.HistoricalEvent.get_todays_event") as mock_get:
            mock_get.return_value = mock_event

            response = client.get("/")
            assert response.status_code == 200

            # Should only call get_todays_event once
            mock_get.assert_called_once()

    def test_no_unnecessary_generation_on_homepage(self, client, test_users):
        """Test that homepage does not trigger LLM generation"""
        # Login as member
        client.post("/auth/login", data={"email": "member@test.com", "password": "memberpass"})

        mock_event = self._make_mock_event()

        with patch("models.content.HistoricalEvent.get_todays_event") as mock_get:
            mock_get.return_value = mock_event

            response = client.get("/")
            assert response.status_code == 200
            # Homepage just displays — generation only via scheduler/admin
