"""Tests for trip modal functionality"""

import pytest
from datetime import date, datetime, timedelta

from models.trip import Trip, TripStatus, TripDifficulty, TripParticipant, ParticipantStatus
from models.user import User, db


@pytest.mark.fast
class TestTripModalEndpoints:
    """Test AJAX endpoints for trip modals"""

    def test_get_trip_modal_data_authenticated(self, client, auth, sample_user, sample_trip):
        """Test getting trip modal data when authenticated"""
        auth.login(sample_user.email, "password123")

        response = client.get(f"/trips/{sample_trip.id}/modal-data")

        assert response.status_code == 200
        data = response.get_json()

        assert data["id"] == sample_trip.id
        assert data["title"] == sample_trip.title
        assert data["destination"] == sample_trip.destination
        assert data["leader_name"] == sample_trip.leader.name
        assert data["can_signup"] == sample_trip.can_signup
        assert data["can_user_signup"] == sample_trip.can_user_signup(sample_user)
        assert "difficulty" in data
        assert "confirmed_count" in data
        assert "waitlist_count" in data

    def test_get_trip_modal_data_unauthenticated(self, client, sample_trip):
        """Test getting trip modal data when not authenticated"""
        response = client.get(f"/trips/{sample_trip.id}/modal-data")
        assert response.status_code == 302  # Redirect to login

    def test_signup_for_trip_ajax_success(self, client, auth, sample_user, sample_trip):
        """Test successful AJAX trip signup"""
        auth.login(sample_user.email, "password123")

        # Get CSRF token
        response = client.get("/trips/")
        csrf_token = auth.get_csrf_token(response)

        response = client.post(
            f"/trips/{sample_trip.id}/signup-ajax",
            headers={"X-CSRFToken": csrf_token},
            json={"notes": "Test notes"},
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        assert "message" in data
        assert data["status"] in ["confirmed", "waitlisted"]
        assert data["confirmed_count"] >= 0
        assert data["waitlist_count"] >= 0

    def test_signup_for_trip_ajax_invalid_csrf(self, client, auth, sample_user, sample_trip):
        """Test AJAX trip signup with invalid CSRF token"""
        auth.login(sample_user.email, "password123")

        response = client.post(
            f"/trips/{sample_trip.id}/signup-ajax",
            headers={"X-CSRFToken": "invalid-token"},
            json={"notes": "Test notes"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_signup_for_trip_ajax_already_registered(self, client, auth, sample_user, sample_trip):
        """Test AJAX trip signup when already registered"""
        auth.login(sample_user.email, "password123")

        # First signup
        participant = TripParticipant(
            trip_id=sample_trip.id, user_id=sample_user.id, status=ParticipantStatus.CONFIRMED
        )
        db.session.add(participant)
        db.session.commit()

        # Get CSRF token and try to signup again
        response = client.get("/trips/")
        csrf_token = auth.get_csrf_token(response)

        response = client.post(
            f"/trips/{sample_trip.id}/signup-ajax",
            headers={"X-CSRFToken": csrf_token},
            json={"notes": "Test notes"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_withdraw_from_trip_ajax_success(self, client, auth, sample_user, sample_trip):
        """Test successful AJAX trip withdrawal"""
        auth.login(sample_user.email, "password123")

        # First signup the user
        participant = TripParticipant(
            trip_id=sample_trip.id, user_id=sample_user.id, status=ParticipantStatus.CONFIRMED
        )
        db.session.add(participant)
        db.session.commit()

        # Get CSRF token
        response = client.get("/trips/")
        csrf_token = auth.get_csrf_token(response)

        response = client.post(
            f"/trips/{sample_trip.id}/withdraw-ajax", headers={"X-CSRFToken": csrf_token}, json={}
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        assert "message" in data
        assert data["confirmed_count"] >= 0
        assert data["waitlist_count"] >= 0

    def test_withdraw_from_trip_ajax_not_registered(self, client, auth, sample_user, sample_trip):
        """Test AJAX trip withdrawal when not registered"""
        auth.login(sample_user.email, "password123")

        # Get CSRF token
        response = client.get("/trips/")
        csrf_token = auth.get_csrf_token(response)

        response = client.post(
            f"/trips/{sample_trip.id}/withdraw-ajax", headers={"X-CSRFToken": csrf_token}, json={}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_withdraw_with_waitlist_promotion(self, client, auth, app_context):
        """Test withdrawal that should promote someone from waitlist"""
        # Create users
        leader = User(name="Trip Leader", email="leader@test.com", role="trip_leader")
        user1 = User(name="User 1", email="user1@test.com", role="member")
        user2 = User(name="User 2", email="user2@test.com", role="member")
        db.session.add_all([leader, user1, user2])
        db.session.flush()

        # Create trip with max 1 participant
        trip = Trip(
            title="Test Trip",
            destination="Test Destination",
            trip_date=date.today() + timedelta(days=7),
            meeting_time=datetime.now().time(),
            leader_id=leader.id,
            difficulty=TripDifficulty.EASY,
            max_participants=1,
            status=TripStatus.ANNOUNCED,
        )
        db.session.add(trip)
        db.session.flush()

        # Add confirmed participant and waitlisted participant
        participant1 = TripParticipant(
            trip_id=trip.id, user_id=user1.id, status=ParticipantStatus.CONFIRMED
        )
        participant2 = TripParticipant(
            trip_id=trip.id, user_id=user2.id, status=ParticipantStatus.WAITLISTED
        )
        db.session.add_all([participant1, participant2])
        db.session.commit()

        # Login as user1 and withdraw
        auth.login("user1@test.com", "password123")
        response = client.get("/trips/")
        csrf_token = auth.get_csrf_token(response)

        response = client.post(
            f"/trips/{trip.id}/withdraw-ajax", headers={"X-CSRFToken": csrf_token}, json={}
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        assert data["promoted"] is True
        assert data["confirmed_count"] == 1  # User2 should be promoted
        assert data["waitlist_count"] == 0


@pytest.mark.fast
class TestTripModalIntegration:
    """Integration tests for trip modal system"""

    def test_modal_templates_render(self, client, auth, sample_user):
        """Test that modal templates are included in pages"""
        auth.login(sample_user.email, "password123")

        response = client.get("/trips/")
        assert response.status_code == 200

        # Check that modal templates are included
        html = response.get_data(as_text=True)
        assert "tripSignupModal" in html
        assert "tripWithdrawModal" in html
        assert "trip-modal.js" in html
        assert "trip-modal.css" in html

    def test_signup_buttons_have_correct_attributes(self, client, auth, sample_user, sample_trip):
        """Test that signup buttons have correct data attributes"""
        auth.login(sample_user.email, "password123")

        response = client.get("/trips/")
        assert response.status_code == 200

        html = response.get_data(as_text=True)
        assert 'data-action="trip-signup"' in html
        assert f'data-trip-id="{sample_trip.id}"' in html

    def test_csrf_token_in_meta_tag(self, client, auth, sample_user):
        """Test that CSRF token is available in meta tag"""
        auth.login(sample_user.email, "password123")

        response = client.get("/trips/")
        assert response.status_code == 200

        html = response.get_data(as_text=True)
        assert 'name="csrf-token"' in html


@pytest.mark.fast
class TestTripModalModels:
    """Test trip model methods used by modal system"""

    def test_add_participant_with_notes(self, app_context, sample_trip, sample_user):
        """Test adding participant with notes"""
        notes = "Has experience with via ferrata"

        participant = sample_trip.add_participant(sample_user, notes=notes)

        assert participant is not None
        assert participant.notes == notes
        assert participant.user_id == sample_user.id
        assert participant.trip_id == sample_trip.id

    def test_promote_from_waitlist(self, app_context):
        """Test promoting user from waitlist"""
        # Create trip with max 1 participant
        leader = User(name="Leader", email="leader@test.com", role="trip_leader")
        user1 = User(name="User 1", email="user1@test.com", role="member")
        user2 = User(name="User 2", email="user2@test.com", role="member")
        db.session.add_all([leader, user1, user2])
        db.session.flush()

        trip = Trip(
            title="Test Trip",
            destination="Test Destination",
            trip_date=date.today() + timedelta(days=7),
            meeting_time=datetime.now().time(),
            leader_id=leader.id,
            difficulty=TripDifficulty.EASY,
            max_participants=1,
            status=TripStatus.ANNOUNCED,
        )
        db.session.add(trip)
        db.session.flush()

        # Fill trip to capacity
        participant1 = TripParticipant(
            trip_id=trip.id, user_id=user1.id, status=ParticipantStatus.CONFIRMED
        )
        # Add waitlisted user
        participant2 = TripParticipant(
            trip_id=trip.id, user_id=user2.id, status=ParticipantStatus.WAITLISTED
        )
        db.session.add_all([participant1, participant2])
        db.session.commit()

        # Remove first participant
        db.session.delete(participant1)
        db.session.commit()

        # Promote from waitlist
        promoted = trip.promote_from_waitlist()

        assert promoted is not None
        assert promoted.user_id == user2.id
        assert promoted.status == ParticipantStatus.CONFIRMED


@pytest.mark.slow
@pytest.mark.integration
class TestTripModalEndToEnd:
    """End-to-end tests for trip modal functionality"""

    def test_complete_signup_flow(self, client, auth, sample_user, sample_trip):
        """Test complete signup flow from button click to success"""
        auth.login(sample_user.email, "password123")

        # 1. Get trips page with modal buttons
        response = client.get("/trips/")
        assert response.status_code == 200

        # 2. Get trip modal data
        response = client.get(f"/trips/{sample_trip.id}/modal-data")
        assert response.status_code == 200
        modal_data = response.get_json()
        assert modal_data["can_user_signup"] is True

        # 3. Submit signup
        csrf_token = auth.get_csrf_token(client.get("/trips/"))
        response = client.post(
            f"/trips/{sample_trip.id}/signup-ajax",
            headers={"X-CSRFToken": csrf_token},
            json={"notes": "End-to-end test signup"},
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result["success"] is True

        # 4. Verify signup in database
        participant = TripParticipant.query.filter_by(
            trip_id=sample_trip.id, user_id=sample_user.id
        ).first()
        assert participant is not None
        assert participant.notes == "End-to-end test signup"

    def test_complete_withdrawal_flow(self, client, auth, sample_user, sample_trip):
        """Test complete withdrawal flow"""
        auth.login(sample_user.email, "password123")

        # 1. First signup the user
        csrf_token = auth.get_csrf_token(client.get("/trips/"))
        response = client.post(
            f"/trips/{sample_trip.id}/signup-ajax",
            headers={"X-CSRFToken": csrf_token},
            json={"notes": "Initial signup"},
        )
        assert response.status_code == 200

        # 2. Get modal data (should show user as registered)
        response = client.get(f"/trips/{sample_trip.id}/modal-data")
        modal_data = response.get_json()
        assert modal_data["user_status"] == "confirmed"

        # 3. Withdraw from trip
        response = client.post(
            f"/trips/{sample_trip.id}/withdraw-ajax", headers={"X-CSRFToken": csrf_token}, json={}
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result["success"] is True

        # 4. Verify withdrawal in database
        participant = TripParticipant.query.filter_by(
            trip_id=sample_trip.id, user_id=sample_user.id
        ).first()
        assert participant is None
