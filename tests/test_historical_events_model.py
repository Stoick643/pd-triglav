"""Test HistoricalEvent model functionality"""

import pytest
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
                event_month=7,
                event_day=27,
                year=1953,
                title="Test First Ascent",
                description="Test description of a significant mountaineering achievement.",
                location="Test Mountain, Test Range",
                people=["Test Climber", "Test Guide"],
                url="https://example.com/source1",
                url_secondary="https://example.com/source2",
                category=EventCategory.FIRST_ASCENT,
                methodology="Direct date search",
                url_methodology="Primary source verification",
                is_featured=True,
                is_generated=True,
            )

            db.session.add(event)
            db.session.commit()

            assert event.id is not None
            assert event.event_month == 7
            assert event.event_day == 27
            assert event.year == 1953
            assert event.title == "Test First Ascent"
            assert event.description == "Test description of a significant mountaineering achievement."
            assert event.location == "Test Mountain, Test Range"
            assert event.people == ["Test Climber", "Test Guide"]
            assert event.url == "https://example.com/source1"
            assert event.url_secondary == "https://example.com/source2"
            assert event.category == EventCategory.FIRST_ASCENT
            assert event.methodology == "Direct date search"
            assert event.url_methodology == "Primary source verification"
            assert event.is_featured is True
            assert event.is_generated is True
            assert event.created_at is not None

    def test_event_creation_minimal_fields(self, app):
        """Test creating event with only required fields"""
        with app.app_context():
            event = HistoricalEvent(
                event_month=7,
                event_day=26,
                year=1865,
                title="Minimal Test Event",
                description="Minimal test description.",
                category=EventCategory.ACHIEVEMENT,
            )

            db.session.add(event)
            db.session.commit()

            assert event.id is not None
            assert event.event_month == 7
            assert event.event_day == 26
            assert event.year == 1865
            assert event.location is None
            assert event.people == []  # Default empty list
            assert event.url is None
            assert event.url_secondary is None
            assert event.is_featured is False  # Default
            assert event.is_generated is True  # Default

    def test_event_people_json_field(self, app):
        """Test people field JSON storage and retrieval"""
        with app.app_context():
            event1 = HistoricalEvent(
                event_month=7, event_day=25, year=1900,
                title="People List Test",
                description="Test description.",
                people=["Climber One", "Climber Two", "Guide"],
                category=EventCategory.EXPEDITION,
            )
            db.session.add(event1)

            event2 = HistoricalEvent(
                event_month=7, event_day=24, year=1901,
                title="Empty People Test",
                description="Test description.",
                people=[],
                category=EventCategory.DISCOVERY,
            )
            db.session.add(event2)

            event3 = HistoricalEvent(
                event_month=7, event_day=23, year=1902,
                title="None People Test",
                description="Test description.",
                category=EventCategory.TRAGEDY,
            )
            db.session.add(event3)

            db.session.commit()

            assert event1.people == ["Climber One", "Climber Two", "Guide"]
            assert event1.people_list == ["Climber One", "Climber Two", "Guide"]
            assert event2.people == []
            assert event2.people_list == []
            assert event3.people_list == []

    def test_event_categories(self, app):
        """Test all event category enums"""
        with app.app_context():
            categories = [
                EventCategory.FIRST_ASCENT,
                EventCategory.TRAGEDY,
                EventCategory.DISCOVERY,
                EventCategory.ACHIEVEMENT,
                EventCategory.EXPEDITION,
            ]

            for i, category in enumerate(categories):
                event = HistoricalEvent(
                    event_month=7, event_day=20 + i, year=1950 + i,
                    title=f"Category Test {category.value}",
                    description=f"Test for {category.value} category.",
                    category=category,
                )
                db.session.add(event)

            db.session.commit()

            events = HistoricalEvent.query.all()
            saved_categories = [event.category for event in events]
            assert set(saved_categories) == set(categories)

    def test_unique_constraint_month_day_year(self, app):
        """Test unique constraint on event_month + event_day + year combination"""
        with app.app_context():
            event1 = HistoricalEvent(
                event_month=7, event_day=27, year=1953,
                title="First Event",
                description="First event description.",
                category=EventCategory.FIRST_ASCENT,
            )
            db.session.add(event1)
            db.session.commit()

            # Duplicate month/day/year should fail
            event2 = HistoricalEvent(
                event_month=7, event_day=27, year=1953,
                title="Duplicate Event",
                description="Duplicate event description.",
                category=EventCategory.ACHIEVEMENT,
            )
            db.session.add(event2)

            with pytest.raises(Exception):
                db.session.commit()

            db.session.rollback()

            # Same month/day, different year should work
            event3 = HistoricalEvent(
                event_month=7, event_day=27, year=1954,
                title="Different Year Event",
                description="Different year description.",
                category=EventCategory.EXPEDITION,
            )
            db.session.add(event3)
            db.session.commit()

            assert event3.id is not None

    def test_date_display_properties(self, app):
        """Test date display properties in English and Slovenian"""
        with app.app_context():
            event = HistoricalEvent(
                event_month=2, event_day=16, year=1953,
                title="Date Format Test",
                description="Test description.",
                category=EventCategory.FIRST_ASCENT,
            )
            db.session.add(event)
            db.session.commit()

            assert event.date_en == "16 February"
            assert event.date_sl == "16. februar"
            assert event.full_date_string == "16. februar 1953"
            assert event.full_date_string_en == "16 February, 1953"

    def test_date_display_all_months(self, app):
        """Test Slovenian display for all 12 months"""
        expected_sl = {
            1: "januar", 2: "februar", 3: "marec", 4: "april",
            5: "maj", 6: "junij", 7: "julij", 8: "avgust",
            9: "september", 10: "oktober", 11: "november", 12: "december",
        }
        with app.app_context():
            for month, sl_name in expected_sl.items():
                event = HistoricalEvent(
                    event_month=month, event_day=1, year=2000 + month,
                    title=f"Month {month} Test",
                    description="Test.",
                    category=EventCategory.ACHIEVEMENT,
                )
                db.session.add(event)
                db.session.commit()

                assert sl_name in event.date_sl, f"Month {month}: expected '{sl_name}' in '{event.date_sl}'"

    def test_repr_method(self, app):
        """Test string representation of HistoricalEvent"""
        with app.app_context():
            event = HistoricalEvent(
                event_month=7, event_day=27, year=1953,
                title="Repr Test Event",
                description="Test description.",
                category=EventCategory.FIRST_ASCENT,
            )
            db.session.add(event)
            db.session.commit()

            expected = "<HistoricalEvent 27 July 1953: Repr Test Event>"
            assert repr(event) == expected


class TestHistoricalEventQueries:
    """Test HistoricalEvent database queries and class methods"""

    @pytest.fixture
    def sample_events(self, app):
        """Create sample events for testing queries"""
        with app.app_context():
            events = [
                HistoricalEvent(
                    event_month=7, event_day=27, year=1953,
                    title="Everest First Ascent",
                    description="Hillary and Tenzing reach Everest summit.",
                    people=["Edmund Hillary", "Tenzing Norgay"],
                    category=EventCategory.FIRST_ASCENT,
                    is_featured=True,
                ),
                HistoricalEvent(
                    event_month=7, event_day=27, year=1865,
                    title="Matterhorn Tragedy",
                    description="First ascent with fatal accident on descent.",
                    people=["Edward Whymper"],
                    category=EventCategory.TRAGEDY,
                    is_featured=True,
                ),
                HistoricalEvent(
                    event_month=7, event_day=26, year=1960,
                    title="Alpine Route Discovery",
                    description="New route discovered in Alps.",
                    category=EventCategory.DISCOVERY,
                    is_featured=False,
                ),
                HistoricalEvent(
                    event_month=7, event_day=25, year=1970,
                    title="Modern Achievement",
                    description="Modern climbing achievement.",
                    category=EventCategory.ACHIEVEMENT,
                    is_featured=False,
                ),
            ]

            for event in events:
                db.session.add(event)
            db.session.commit()

            return events

    def test_get_event_for_date(self, app, sample_events):
        """Test retrieving events for specific month/day"""
        with app.app_context():
            # Date with multiple events
            event = HistoricalEvent.get_event_for_date(7, 27)
            assert event is not None
            assert event.event_month == 7
            assert event.event_day == 27

            # Date with single event
            event = HistoricalEvent.get_event_for_date(7, 26)
            assert event is not None
            assert event.year == 1960

            # Non-existent date
            event = HistoricalEvent.get_event_for_date(1, 1)
            assert event is None

    def test_get_event_for_date_prefers_curated(self, app):
        """Test that curated events are returned before AI-generated ones (Change 2)"""
        with app.app_context():
            # Create AI-generated event first
            ai_event = HistoricalEvent(
                event_month=2, event_day=16, year=1980,
                title="AI Generated Event",
                description="Generated by LLM.",
                category=EventCategory.ACHIEVEMENT,
                is_generated=True,
            )
            db.session.add(ai_event)
            db.session.commit()

            # Create curated event for same date
            curated_event = HistoricalEvent(
                event_month=2, event_day=16, year=1970,
                title="Curated Event",
                description="Scraped from zsa.si.",
                category=EventCategory.FIRST_ASCENT,
                is_generated=False,
            )
            db.session.add(curated_event)
            db.session.commit()

            # Should return curated event (is_generated=False first)
            result = HistoricalEvent.get_event_for_date(2, 16)
            assert result.title == "Curated Event"
            assert result.is_generated is False

    def test_get_all_events_for_date(self, app, sample_events):
        """Test getting all events for a date"""
        with app.app_context():
            events = HistoricalEvent.get_all_events_for_date(7, 27)
            assert len(events) == 2
            years = [e.year for e in events]
            assert 1953 in years
            assert 1865 in years

    def test_get_todays_event(self, app, sample_events):
        """Test getting today's historical event"""
        with app.app_context():
            # Directly test with known date
            existing = HistoricalEvent.get_event_for_date(7, 27)
            assert existing is not None

            # Non-existent date
            non_existent = HistoricalEvent.get_event_for_date(1, 1)
            assert non_existent is None

    def test_get_featured_events(self, app, sample_events):
        """Test retrieving featured events"""
        with app.app_context():
            featured_events = HistoricalEvent.get_featured_events()
            assert len(featured_events) == 2
            for event in featured_events:
                assert event.is_featured is True

            years = [event.year for event in featured_events]
            assert years == sorted(years, reverse=True)

            limited_events = HistoricalEvent.get_featured_events(limit=1)
            assert len(limited_events) == 1

    def test_database_indexes(self, app, sample_events):
        """Test that database indexes work correctly for month/day queries"""
        with app.app_context():
            # Query by month/day
            events_by_date = HistoricalEvent.query.filter_by(event_month=7, event_day=27).all()
            assert len(events_by_date) == 2

            # Query by year
            events_by_year = HistoricalEvent.query.filter_by(year=1953).all()
            assert len(events_by_year) == 1

            # Query by category
            first_ascents = HistoricalEvent.query.filter_by(category=EventCategory.FIRST_ASCENT).all()
            assert len(first_ascents) == 1

    def test_to_dict_includes_structured_date(self, app, sample_events):
        """Test that to_dict includes month/day and formatted dates"""
        with app.app_context():
            event = HistoricalEvent.get_event_for_date(7, 26)
            d = event.to_dict()

            assert d["event_month"] == 7
            assert d["event_day"] == 26
            assert d["date_en"] == "26 July"
            assert d["date_sl"] == "26. julij"
            assert "full_date" in d


class TestDateParsing:
    """Test date string parsing utility"""

    def test_parse_english_dd_month(self):
        """Test parsing English DD Month format"""
        from utils.llm_service import parse_date_string

        month, day = parse_date_string("16 February")
        assert month == 2
        assert day == 16

        month, day = parse_date_string("09 November")
        assert month == 11
        assert day == 9

    def test_parse_english_month_dd(self):
        """Test parsing English Month DD format"""
        from utils.llm_service import parse_date_string

        month, day = parse_date_string("February 16")
        assert month == 2
        assert day == 16

    def test_parse_slovenian(self):
        """Test parsing Slovenian month names"""
        from utils.llm_service import parse_date_string

        test_cases = [
            ("Januar 11", 1, 11),
            ("Februar 18", 2, 18),
            ("Marec 5", 3, 5),
            ("Maj 12", 5, 12),
            ("Junij 25", 6, 25),
            ("Julij 15", 7, 15),
            ("Avgust 11", 8, 11),
            ("Oktober 19", 10, 19),
        ]

        for date_str, expected_month, expected_day in test_cases:
            month, day = parse_date_string(date_str)
            assert month == expected_month, f"Failed for '{date_str}': expected month {expected_month}, got {month}"
            assert day == expected_day, f"Failed for '{date_str}': expected day {expected_day}, got {day}"

    def test_parse_invalid(self):
        """Test parsing invalid date strings"""
        from utils.llm_service import parse_date_string

        month, day = parse_date_string("")
        assert month is None
        assert day is None

        month, day = parse_date_string(None)
        assert month is None
        assert day is None

        month, day = parse_date_string("not a date")
        assert month is None
        assert day is None
