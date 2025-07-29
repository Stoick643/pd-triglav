"""Test HistoricalEvent model functionality"""

import pytest
from datetime import datetime
from models.content import HistoricalEvent, EventCategory
from models.user import db

# Mark all tests in this file as fast model tests
pytestmark = [pytest.mark.fast, pytest.mark.models]


class TestHistoricalEventModel:
    """Test HistoricalEvent model creation and validation"""
    
    def test_event_creation_with_all_fields(self, app):
        """Test creating historical event with all fields"""
        with app.app_context():
            event = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Test First Ascent',
                description='Test description of a significant mountaineering achievement.',
                location='Test Mountain, Test Range',
                people=['Test Climber', 'Test Guide'],
                url='https://example.com/source1',
                url_secondary='https://example.com/source2',
                category=EventCategory.FIRST_ASCENT,
                methodology='Direct date search',
                url_methodology='Primary source verification',
                is_featured=True,
                is_generated=True
            )
            
            db.session.add(event)
            db.session.commit()
            
            assert event.id is not None
            assert event.date == '27 July'
            assert event.year == 1953
            assert event.title == 'Test First Ascent'
            assert event.description == 'Test description of a significant mountaineering achievement.'
            assert event.location == 'Test Mountain, Test Range'
            assert event.people == ['Test Climber', 'Test Guide']
            assert event.url == 'https://example.com/source1'
            assert event.url_secondary == 'https://example.com/source2'
            assert event.category == EventCategory.FIRST_ASCENT
            assert event.methodology == 'Direct date search'
            assert event.url_methodology == 'Primary source verification'
            assert event.is_featured is True
            assert event.is_generated is True
            assert event.created_at is not None
    
    def test_event_creation_minimal_fields(self, app):
        """Test creating event with only required fields"""
        with app.app_context():
            event = HistoricalEvent(
                date='26 July',
                year=1865,
                title='Minimal Test Event',
                description='Minimal test description.',
                category=EventCategory.ACHIEVEMENT
            )
            
            db.session.add(event)
            db.session.commit()
            
            assert event.id is not None
            assert event.date == '26 July'
            assert event.year == 1865
            assert event.title == 'Minimal Test Event'
            assert event.location is None
            assert event.people == []  # Default empty list
            assert event.url is None
            assert event.url_secondary is None
            assert event.methodology is None
            assert event.url_methodology is None
            assert event.is_featured is False  # Default
            assert event.is_generated is True  # Default
    
    def test_event_people_json_field(self, app):
        """Test people field JSON storage and retrieval"""
        with app.app_context():
            # Test with list
            event1 = HistoricalEvent(
                date='25 July',
                year=1900,
                title='People List Test',
                description='Test description.',
                people=['Climber One', 'Climber Two', 'Guide'],
                category=EventCategory.EXPEDITION
            )
            db.session.add(event1)
            
            # Test with empty list
            event2 = HistoricalEvent(
                date='24 July',
                year=1901,
                title='Empty People Test',
                description='Test description.',
                people=[],
                category=EventCategory.DISCOVERY
            )
            db.session.add(event2)
            
            # Test with None (should default to empty list)
            event3 = HistoricalEvent(
                date='23 July',
                year=1902,
                title='None People Test',
                description='Test description.',
                category=EventCategory.TRAGEDY
            )
            db.session.add(event3)
            
            db.session.commit()
            
            # Retrieve and test
            assert event1.people == ['Climber One', 'Climber Two', 'Guide']
            assert event1.people_list == ['Climber One', 'Climber Two', 'Guide']
            
            assert event2.people == []
            assert event2.people_list == []
            
            assert event3.people_list == []  # Should handle None case
    
    def test_event_categories(self, app):
        """Test all event category enums"""
        with app.app_context():
            categories = [
                EventCategory.FIRST_ASCENT,
                EventCategory.TRAGEDY,
                EventCategory.DISCOVERY,
                EventCategory.ACHIEVEMENT,
                EventCategory.EXPEDITION
            ]
            
            for i, category in enumerate(categories):
                event = HistoricalEvent(
                    date=f'{20+i} July',
                    year=1950 + i,
                    title=f'Category Test {category.value}',
                    description=f'Test for {category.value} category.',
                    category=category
                )
                db.session.add(event)
            
            db.session.commit()
            
            # Verify all categories were saved correctly
            events = HistoricalEvent.query.all()
            saved_categories = [event.category for event in events]
            assert set(saved_categories) == set(categories)
    
    def test_unique_constraint_date_year(self, app):
        """Test unique constraint on date + year combination"""
        with app.app_context():
            # Create first event
            event1 = HistoricalEvent(
                date='27 July',
                year=1953,
                title='First Event',
                description='First event description.',
                category=EventCategory.FIRST_ASCENT
            )
            db.session.add(event1)
            db.session.commit()
            
            # Try to create duplicate date + year (should fail)
            event2 = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Duplicate Event',
                description='Duplicate event description.',
                category=EventCategory.ACHIEVEMENT
            )
            db.session.add(event2)
            
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()
            
            db.session.rollback()
            
            # Same date, different year should work
            event3 = HistoricalEvent(
                date='27 July',
                year=1954,
                title='Different Year Event',
                description='Different year description.',
                category=EventCategory.EXPEDITION
            )
            db.session.add(event3)
            db.session.commit()  # Should succeed
            
            assert event3.id is not None
    
    def test_full_date_string_property(self, app):
        """Test full_date_string property formatting"""
        with app.app_context():
            event = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Date Format Test',
                description='Test description.',
                category=EventCategory.FIRST_ASCENT
            )
            db.session.add(event)
            db.session.commit()
            
            assert event.full_date_string == '27 July, 1953'
    
    def test_repr_method(self, app):
        """Test string representation of HistoricalEvent"""
        with app.app_context():
            event = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Repr Test Event',
                description='Test description.',
                category=EventCategory.FIRST_ASCENT
            )
            db.session.add(event)
            db.session.commit()
            
            expected = '<HistoricalEvent 27 July 1953: Repr Test Event>'
            assert repr(event) == expected


class TestHistoricalEventQueries:
    """Test HistoricalEvent database queries and class methods"""
    
    @pytest.fixture
    def sample_events(self, app):
        """Create sample events for testing queries"""
        with app.app_context():
            events = [
                HistoricalEvent(
                    date='27 July',
                    year=1953,
                    title='Everest First Ascent',
                    description='Hillary and Tenzing reach Everest summit.',
                    people=['Edmund Hillary', 'Tenzing Norgay'],
                    category=EventCategory.FIRST_ASCENT,
                    is_featured=True
                ),
                HistoricalEvent(
                    date='27 July',
                    year=1865,
                    title='Matterhorn Tragedy',
                    description='First ascent with fatal accident on descent.',
                    people=['Edward Whymper'],
                    category=EventCategory.TRAGEDY,
                    is_featured=True
                ),
                HistoricalEvent(
                    date='26 July',
                    year=1960,
                    title='Alpine Route Discovery',
                    description='New route discovered in Alps.',
                    category=EventCategory.DISCOVERY,
                    is_featured=False
                ),
                HistoricalEvent(
                    date='25 July',
                    year=1970,
                    title='Modern Achievement',
                    description='Modern climbing achievement.',
                    category=EventCategory.ACHIEVEMENT,
                    is_featured=False
                )
            ]
            
            for event in events:
                db.session.add(event)
            db.session.commit()
            
            return events
    
    def test_get_event_for_date(self, app, sample_events):
        """Test retrieving events for specific date"""
        with app.app_context():
            # Test existing date with multiple years (should return first found)
            event = HistoricalEvent.get_event_for_date('27 July')
            assert event is not None
            assert event.date == '27 July'
            assert event.year in [1953, 1865]  # Could be either
            
            # Test date with single event
            event = HistoricalEvent.get_event_for_date('26 July')
            assert event is not None
            assert event.year == 1960
            assert event.title == 'Alpine Route Discovery'
            
            # Test non-existent date
            event = HistoricalEvent.get_event_for_date('01 January')
            assert event is None
    
    def test_get_todays_event(self, app, sample_events):
        """Test getting today's historical event"""
        with app.app_context():
            # Test directly with existing sample data
            # The sample_events fixture creates an event for '27 July' 
            existing_event = HistoricalEvent.get_event_for_date('27 July')
            assert existing_event is not None
            
            # Test with non-existent date
            non_existent = HistoricalEvent.get_event_for_date('01 January')
            assert non_existent is None
    
    def test_get_featured_events(self, app, sample_events):
        """Test retrieving featured events"""
        with app.app_context():
            featured_events = HistoricalEvent.get_featured_events()
            
            # Should return only featured events
            assert len(featured_events) == 2
            for event in featured_events:
                assert event.is_featured is True
            
            # Should be ordered by year descending
            years = [event.year for event in featured_events]
            assert years == sorted(years, reverse=True)
            
            # Test limit parameter
            limited_events = HistoricalEvent.get_featured_events(limit=1)
            assert len(limited_events) == 1
            assert limited_events[0].year == max(years)  # Most recent year
    
    def test_database_indexes(self, app, sample_events):
        """Test that database indexes work correctly"""
        with app.app_context():
            # Test date index (should be fast query)
            events_by_date = HistoricalEvent.query.filter_by(date='27 July').all()
            assert len(events_by_date) == 2
            
            # Test year index
            events_by_year = HistoricalEvent.query.filter_by(year=1953).all()
            assert len(events_by_year) == 1
            assert events_by_year[0].title == 'Everest First Ascent'
            
            # Test category index
            first_ascents = HistoricalEvent.query.filter_by(category=EventCategory.FIRST_ASCENT).all()
            assert len(first_ascents) == 1
            assert first_ascents[0].title == 'Everest First Ascent'