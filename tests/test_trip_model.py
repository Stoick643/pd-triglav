"""Test Trip model functionality and business logic"""

import pytest
from datetime import date, time, timedelta
from models.user import User, UserRole, db
from models.trip import Trip, TripDifficulty, TripStatus, TripParticipant, ParticipantStatus

# Mark all tests in this file as fast model tests
pytestmark = [pytest.mark.fast, pytest.mark.models]


def test_trip_creation_with_difficulty_levels(app, test_users):
    """Test trip creation with different difficulty levels"""
    with app.app_context():
        trip_leader = test_users['trip_leader']
        
        # Test all difficulty levels
        difficulties = [
            (TripDifficulty.EASY, 'Lahka tura'),
            (TripDifficulty.MODERATE, 'Srednje zahtevna'),
            (TripDifficulty.DIFFICULT, 'Zahtevna'),
            (TripDifficulty.EXPERT, 'Zelo zahtevna')
        ]
        
        for difficulty, slovenian_name in difficulties:
            trip = Trip(
                title=f'Test trip - {difficulty.value}',
                destination='Test destination',
                trip_date=date.today() + timedelta(days=30),
                difficulty=difficulty,
                leader_id=trip_leader.id
            )
            db.session.add(trip)
            db.session.commit()
            
            assert trip.difficulty == difficulty
            assert trip.difficulty.slovenian_name == slovenian_name
            assert trip.status == TripStatus.ANNOUNCED


def test_trip_participant_signup_with_capacity(app, test_users):
    """Test participant signup with capacity limits"""
    with app.app_context():
        trip_leader = test_users['trip_leader']
        member = test_users['member']
        admin = test_users['admin']
        
        # Create trip with max 2 participants
        trip = Trip(
            title='Limited capacity trip',
            destination='Test mountain',
            trip_date=date.today() + timedelta(days=15),
            difficulty=TripDifficulty.MODERATE,
            max_participants=2,
            leader_id=trip_leader.id
        )
        db.session.add(trip)
        db.session.commit()
        
        # Test initial state
        assert trip.confirmed_participants_count == 0
        assert trip.waitlist_count == 0
        assert not trip.is_full
        assert trip.can_signup
        
        # First member signs up - should be confirmed
        assert trip.can_user_signup(member)
        participant1 = trip.add_participant(member)
        db.session.commit()
        
        assert participant1.status == ParticipantStatus.CONFIRMED
        assert trip.confirmed_participants_count == 1
        assert not trip.is_full
        
        # Second member signs up - should be confirmed
        assert trip.can_user_signup(admin)
        participant2 = trip.add_participant(admin)
        db.session.commit()
        
        assert participant2.status == ParticipantStatus.CONFIRMED
        assert trip.confirmed_participants_count == 2
        assert trip.is_full
        
        # Try to add third member - should be waitlisted
        pending_user = test_users['pending']  # Use pending user for third signup
        pending_user.approve()  # Approve so they can sign up
        db.session.commit()
        
        assert trip.can_user_signup(pending_user)
        participant3 = trip.add_participant(pending_user)
        db.session.commit()
        
        assert participant3.status == ParticipantStatus.WAITLISTED
        assert trip.confirmed_participants_count == 2
        assert trip.waitlist_count == 1


def test_waitlist_promotion_logic(app, test_users):
    """Test waitlist promotion when confirmed participants leave"""
    with app.app_context():
        trip_leader = test_users['trip_leader']
        member = test_users['member']
        admin = test_users['admin']
        
        # Create trip with max 1 participant for simple testing
        trip = Trip(
            title='Waitlist test trip',
            destination='Test peak',
            trip_date=date.today() + timedelta(days=20),
            difficulty=TripDifficulty.DIFFICULT,
            max_participants=1,
            leader_id=trip_leader.id
        )
        db.session.add(trip)
        db.session.commit()
        
        # Member signs up - confirmed
        participant1 = trip.add_participant(member)
        db.session.commit()
        assert participant1.status == ParticipantStatus.CONFIRMED
        
        # Admin signs up - waitlisted
        participant2 = trip.add_participant(admin)
        db.session.commit()
        assert participant2.status == ParticipantStatus.WAITLISTED
        
        # Member withdraws - admin should be promoted
        success = trip.remove_participant(member)
        db.session.commit()
        
        assert success is True
        assert trip.confirmed_participants_count == 1
        assert trip.waitlist_count == 0
        
        # Refresh participant2 from database
        db.session.refresh(participant2)
        assert participant2.status == ParticipantStatus.CONFIRMED


def test_trip_status_properties(app, test_users):
    """Test trip status and date-based properties"""
    with app.app_context():
        trip_leader = test_users['trip_leader']
        
        # Test future trip
        future_trip = Trip(
            title='Future trip',
            destination='Future peak',
            trip_date=date.today() + timedelta(days=10),
            difficulty=TripDifficulty.EASY,
            leader_id=trip_leader.id
        )
        db.session.add(future_trip)
        
        # Test past trip
        past_trip = Trip(
            title='Past trip',
            destination='Past peak',
            trip_date=date.today() - timedelta(days=10),
            difficulty=TripDifficulty.MODERATE,
            leader_id=trip_leader.id
        )
        db.session.add(past_trip)
        db.session.commit()
        
        # Test future trip properties
        assert not future_trip.is_past
        assert future_trip.can_signup
        
        # Test past trip properties
        assert past_trip.is_past
        assert not past_trip.can_signup  # Past trips can't accept signups
        
        # Test cancelled trip
        cancelled_trip = Trip(
            title='Cancelled trip',
            destination='Cancelled peak',
            trip_date=date.today() + timedelta(days=5),
            difficulty=TripDifficulty.EXPERT,
            status=TripStatus.CANCELLED,
            leader_id=trip_leader.id
        )
        db.session.add(cancelled_trip)
        db.session.commit()
        
        assert not cancelled_trip.can_signup


def test_trip_participant_signup_restrictions(app, test_users):
    """Test participant signup restrictions and validations"""
    with app.app_context():
        trip_leader = test_users['trip_leader']
        member = test_users['member']
        
        trip = Trip(
            title='Restriction test trip',
            destination='Test location',
            trip_date=date.today() + timedelta(days=7),
            difficulty=TripDifficulty.MODERATE,
            leader_id=trip_leader.id
        )
        db.session.add(trip)
        db.session.commit()
        
        # User can sign up initially
        assert trip.can_user_signup(member)
        
        # User signs up
        participant = trip.add_participant(member)
        db.session.commit()
        assert participant is not None
        
        # User cannot sign up again
        assert not trip.can_user_signup(member)
        duplicate_participant = trip.add_participant(member)
        assert duplicate_participant is None
        
        # Check participant status
        status = trip.get_participant_status(member)
        assert status == ParticipantStatus.CONFIRMED


def test_trip_query_methods(app, test_users):
    """Test static query methods for trips"""
    with app.app_context():
        trip_leader = test_users['trip_leader']
        admin = test_users['admin']
        
        # Create various trips
        upcoming_trip = Trip(
            title='Upcoming trip',
            destination='Future peak',
            trip_date=date.today() + timedelta(days=30),
            difficulty=TripDifficulty.EASY,
            leader_id=trip_leader.id
        )
        
        past_trip = Trip(
            title='Past trip',
            destination='Past peak',
            trip_date=date.today() - timedelta(days=30),
            difficulty=TripDifficulty.MODERATE,
            status=TripStatus.COMPLETED,
            leader_id=admin.id
        )
        
        db.session.add_all([upcoming_trip, past_trip])
        db.session.commit()
        
        # Test upcoming trips query
        upcoming_trips = Trip.get_upcoming_trips()
        assert len(upcoming_trips) >= 1
        assert upcoming_trip in upcoming_trips
        assert past_trip not in upcoming_trips
        
        # Test past trips query
        past_trips = Trip.get_past_trips()
        assert len(past_trips) >= 1
        assert past_trip in past_trips
        assert upcoming_trip not in past_trips
        
        # Test trips by leader
        leader_trips = Trip.get_trips_by_leader(trip_leader.id)
        assert upcoming_trip in leader_trips
        assert past_trip not in leader_trips
        
        admin_trips = Trip.get_trips_by_leader(admin.id)
        assert past_trip in admin_trips
        assert upcoming_trip not in admin_trips


def test_trip_serialization(app, test_users):
    """Test trip to_dict method for JSON serialization"""
    with app.app_context():
        trip_leader = test_users['trip_leader']
        member = test_users['member']
        
        trip = Trip(
            title='Serialization test',
            destination='Test mountain',
            trip_date=date.today() + timedelta(days=14),
            difficulty=TripDifficulty.DIFFICULT,
            max_participants=5,
            leader_id=trip_leader.id
        )
        db.session.add(trip)
        db.session.commit()
        
        # Add a participant
        trip.add_participant(member)
        db.session.commit()
        
        # Test serialization
        trip_dict = trip.to_dict()
        
        assert trip_dict['id'] == trip.id
        assert trip_dict['title'] == 'Serialization test'
        assert trip_dict['destination'] == 'Test mountain'
        assert trip_dict['difficulty'] == 'difficult'
        assert trip_dict['difficulty_name'] == 'Zahtevna'
        assert trip_dict['leader'] == trip_leader.name
        assert trip_dict['confirmed_participants'] == 1
        assert trip_dict['waitlist_count'] == 0
        assert trip_dict['status'] == 'announced'
        assert trip_dict['can_signup'] is True
        assert 'trip_date' in trip_dict


def test_unlimited_capacity_trip(app, test_users):
    """Test trip with no participant limit"""
    with app.app_context():
        trip_leader = test_users['trip_leader']
        member = test_users['member']
        admin = test_users['admin']
        
        # Create trip with no max_participants
        trip = Trip(
            title='Unlimited capacity trip',
            destination='Big mountain',
            trip_date=date.today() + timedelta(days=21),
            difficulty=TripDifficulty.EASY,
            max_participants=None,  # Unlimited
            leader_id=trip_leader.id
        )
        db.session.add(trip)
        db.session.commit()
        
        # Should never be full
        assert not trip.is_full
        
        # Add multiple participants - all should be confirmed
        participant1 = trip.add_participant(member)
        participant2 = trip.add_participant(admin)
        db.session.commit()
        
        assert participant1.status == ParticipantStatus.CONFIRMED
        assert participant2.status == ParticipantStatus.CONFIRMED
        assert trip.confirmed_participants_count == 2
        assert trip.waitlist_count == 0
        assert not trip.is_full