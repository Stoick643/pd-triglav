"""Integration tests for enhanced participant lists with contact info"""

import pytest
from datetime import date, timedelta
from models.user import db
from models.trip import Trip, TripDifficulty

# Mark tests as fast integration tests
pytestmark = [pytest.mark.fast, pytest.mark.integration]


def test_trip_detail_shows_contacts_to_leader(client, test_users):
    """Test that trip leader sees phone/email in trip detail template"""
    with client.application.app_context():
        trip_leader = test_users["trip_leader"]
        member = test_users["member"]

        # Create trip
        trip = Trip(
            title="Integration Contact Test",
            destination="Test Destination",
            trip_date=date.today() + timedelta(days=30),
            difficulty=TripDifficulty.EASY,
            leader_id=trip_leader.id,
        )
        db.session.add(trip)
        db.session.commit()

        # Add member as participant
        trip.add_participant(member, notes="Emergency contact: John Doe")
        db.session.commit()

        # Login as trip leader
        with client.session_transaction() as sess:
            sess["_user_id"] = str(trip_leader.id)
            sess["_fresh"] = True

        # Visit trip detail page
        response = client.get(f"/trips/{trip.id}")
        assert response.status_code == 200

        # Check that contact info is visible
        html_content = response.data.decode("utf-8")
        assert "Kontakti vidni" in html_content
        assert member.phone in html_content
        assert member.email in html_content
        assert "Emergency contact: John Doe" in html_content
        assert "bi-telephone" in html_content
        assert "bi-envelope" in html_content


def test_trip_detail_hides_contacts_from_member(client, test_users):
    """Test that regular member sees only names without contact info"""
    with client.application.app_context():
        trip_leader = test_users["trip_leader"]
        member = test_users["member"]
        other_member = test_users["pending"]  # Using as regular member

        # Create trip
        trip = Trip(
            title="Hidden Contact Test",
            destination="Test Destination",
            trip_date=date.today() + timedelta(days=30),
            difficulty=TripDifficulty.EASY,
            leader_id=trip_leader.id,
        )
        db.session.add(trip)
        db.session.commit()

        # Add member as participant
        trip.add_participant(member, notes="Private notes")
        db.session.commit()

        # Login as different member (not the leader)
        with client.session_transaction() as sess:
            sess["_user_id"] = str(other_member.id)
            sess["_fresh"] = True

        # Visit trip detail page
        response = client.get(f"/trips/{trip.id}")
        assert response.status_code == 200

        # Check that contact info is not visible
        html_content = response.data.decode("utf-8")
        assert "Kontakti vidni" not in html_content
        assert member.phone not in html_content
        assert member.email not in html_content
        assert member.name in html_content  # Name should still be visible
        assert "Private notes" in html_content  # Notes should be visible


def test_participant_list_responsive_layout(client, test_users):
    """Test that contact info displays properly with responsive CSS"""
    with client.application.app_context():
        trip_leader = test_users["trip_leader"]
        member = test_users["member"]
        admin = test_users["admin"]

        # Create trip with multiple participants
        trip = Trip(
            title="Responsive Layout Test",
            destination="Test Destination",
            trip_date=date.today() + timedelta(days=30),
            difficulty=TripDifficulty.MODERATE,
            leader_id=trip_leader.id,
            max_participants=2,
        )
        db.session.add(trip)
        db.session.commit()

        # Add participants (one confirmed, one waitlisted)
        trip.add_participant(member, notes="Confirmed participant")
        trip.add_participant(admin, notes="Waitlisted participant")
        db.session.commit()

        # Login as trip leader
        with client.session_transaction() as sess:
            sess["_user_id"] = str(trip_leader.id)
            sess["_fresh"] = True

        # Visit trip detail page
        response = client.get(f"/trips/{trip.id}")
        assert response.status_code == 200

        html_content = response.data.decode("utf-8")

        # Check that both participants are shown with proper structure
        assert "participant-item" in html_content
        assert "participant-info" in html_content
        assert "contact-info" in html_content
        assert "participant-notes" in html_content

        # Check responsive classes and structure
        assert "d-flex" in html_content
        assert "justify-content-between" in html_content
        assert "align-items-start" in html_content

        # Check that CSS file is included
        assert "trip-detail.css" in html_content

        # Check both participant types are displayed
        assert "Potrjeni" in html_content
        assert "Čakalna lista" in html_content
        assert "bi-check-circle text-success" in html_content
        assert "bi-hourglass text-warning" in html_content


def test_contact_visibility_enforcement_security(client, test_users):
    """Test that contact visibility is properly enforced at template level"""
    with client.application.app_context():
        trip_leader = test_users["trip_leader"]
        member = test_users["member"]

        # Create trip
        trip = Trip(
            title="Security Enforcement Test",
            destination="Test Destination",
            trip_date=date.today() + timedelta(days=30),
            difficulty=TripDifficulty.EASY,
            leader_id=trip_leader.id,
        )
        db.session.add(trip)
        db.session.commit()

        # Add member with sensitive contact info
        trip.add_participant(member, notes="Sensitive: Emergency contact 911")
        db.session.commit()

        # Test as anonymous user (not logged in)
        response = client.get(f"/trips/{trip.id}")
        assert response.status_code == 200

        html_content = response.data.decode("utf-8")

        # Contact info should not be visible to anonymous users
        assert member.phone not in html_content
        assert member.email not in html_content
        assert "Kontakti vidni" not in html_content

        # But participant name should still be visible for transparency
        assert member.name in html_content

        # Notes should be visible (they're not considered private contact info)
        assert "Sensitive: Emergency contact 911" in html_content
