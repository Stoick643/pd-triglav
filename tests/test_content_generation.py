"""Test content generation services"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch
from utils.content_generation import (
    HistoricalEventService,
    NewsService,
    ContentManager,
    ContentGenerationError,
    generate_todays_historical_event,
    run_daily_content_generation,
    get_content_stats,
)
from models.content import HistoricalEvent, EventCategory
from models.user import db
from utils.llm_service import LLMError


class TestHistoricalEventService:
    """Test HistoricalEventService functionality"""

    @pytest.fixture
    def event_service(self, app):
        """Create HistoricalEventService instance"""
        with app.app_context():
            return HistoricalEventService()

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM API response (new format without URLs)"""
        return {
            "year": 1953,
            "title": "Test Mountain First Ascent",
            "description": "A significant test achievement in mountaineering history.",
            "location": "Test Mountain Range",
            "people": ["Test Climber", "Test Guide"],
            "category": "first_ascent",
            "confidence": "high",
            "methodology": "Direct date search",
        }

    def test_generate_daily_event_success(self, app, event_service, mock_llm_response):
        """Test successful daily event generation"""
        with app.app_context():
            with patch.object(
                event_service.llm_service, "generate_historical_event"
            ) as mock_generate:
                mock_generate.return_value = mock_llm_response

                with patch("utils.content_generation.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(2024, 7, 27)

                    event = event_service.generate_daily_event()

            assert event is not None
            assert event.event_month == 7
            assert event.event_day == 27
            assert event.year == 1953
            assert event.title == "Test Mountain First Ascent"
            assert event.category == EventCategory.FIRST_ASCENT
            assert event.is_generated is True

            # Verify saved to database
            saved = HistoricalEvent.query.filter_by(event_month=7, event_day=27, year=1953).first()
            assert saved is not None
            assert saved.id == event.id

    def test_generate_daily_event_low_confidence_retries_then_fallback(self, app, event_service):
        """Test that low-confidence events trigger retry, then fallback (Change 4)"""
        with app.app_context():
            low_confidence_response = {
                "year": 1999,
                "title": "Uncertain Event",
                "description": "Not sure about this one.",
                "location": "Unknown",
                "people": [],
                "category": "achievement",
                "confidence": "low",
            }

            with patch.object(
                event_service.llm_service, "generate_historical_event"
            ) as mock_generate:
                # Both primary and retry return low confidence
                mock_generate.return_value = low_confidence_response

                with patch("utils.content_generation.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(2024, 3, 15)

                    result = event_service.generate_daily_event()

            # Should create a fallback event when all providers return low confidence
            assert result is not None
            assert result.is_generated is False  # Fallback is marked as non-generated
            assert result.event_month == 3
            assert result.event_day == 15

            # Retry should have been attempted (called twice: first + skip_first)
            assert mock_generate.call_count == 2

    def test_generate_daily_event_medium_confidence_saved(self, app, event_service, mock_llm_response):
        """Test that medium-confidence events ARE saved"""
        with app.app_context():
            mock_llm_response["confidence"] = "medium"

            with patch.object(
                event_service.llm_service, "generate_historical_event"
            ) as mock_generate:
                mock_generate.return_value = mock_llm_response

                with patch("utils.content_generation.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(2024, 7, 27)

                    event = event_service.generate_daily_event()

            assert event is not None
            assert event.title == "Test Mountain First Ascent"

    def test_generate_daily_event_already_exists(self, app, event_service):
        """Test generation when event already exists for date"""
        with app.app_context():
            existing_event = HistoricalEvent(
                event_month=7, event_day=27, year=1953,
                title="Existing Event",
                description="Already exists",
                category=EventCategory.ACHIEVEMENT,
            )
            db.session.add(existing_event)
            db.session.commit()

            with patch("utils.content_generation.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 7, 27)

                result = event_service.generate_daily_event()

            assert result.id == existing_event.id
            assert result.title == "Existing Event"

    def test_generate_daily_event_invalid_category(self, app, event_service, mock_llm_response):
        """Test handling of invalid category from LLM"""
        with app.app_context():
            mock_llm_response["category"] = "invalid_category"

            with patch.object(
                event_service.llm_service, "generate_historical_event"
            ) as mock_generate:
                mock_generate.return_value = mock_llm_response

                event = event_service.generate_daily_event()

            assert event.category == EventCategory.ACHIEVEMENT

    def test_generate_daily_event_llm_error_fallback(self, app, event_service):
        """Test fallback when LLM service fails"""
        with app.app_context():
            with patch.object(
                event_service.llm_service, "generate_historical_event"
            ) as mock_generate:
                mock_generate.side_effect = LLMError("API failed")

                with patch.object(event_service, "_create_fallback_event") as mock_fallback:
                    mock_fallback_event = Mock()
                    mock_fallback.return_value = mock_fallback_event

                    result = event_service.generate_daily_event()

                    assert result == mock_fallback_event
                    mock_fallback.assert_called_once()

    def test_create_fallback_event(self, app, event_service):
        """Test fallback event creation with month/day"""
        with app.app_context():
            fallback_data = {
                "year": 1953,
                "title": "Fallback Event",
                "description": "Fallback description",
                "location": "Fallback Location",
                "people": ["Fallback Person"],
                "category": "achievement",
                "confidence": "high",
            }

            with patch.object(event_service.llm_service, "get_fallback_content") as mock_fallback:
                mock_fallback.return_value = fallback_data

                event = event_service._create_fallback_event(7, 27)

            assert event.title == "Fallback Event"
            assert event.event_month == 7
            assert event.event_day == 27
            assert event.is_generated is False  # Marked as fallback

    def test_regenerate_event_success(self, app, event_service, mock_llm_response):
        """Test successful event regeneration"""
        with app.app_context():
            existing_event = HistoricalEvent(
                event_month=7, event_day=27, year=1953,
                title="Old Event",
                description="Old description",
                category=EventCategory.ACHIEVEMENT,
            )
            db.session.add(existing_event)
            db.session.commit()
            event_id = existing_event.id

            with patch.object(
                event_service.llm_service, "generate_historical_event"
            ) as mock_generate:
                mock_generate.return_value = mock_llm_response

                updated_event = event_service.regenerate_event(event_id)

            assert updated_event.id == event_id
            assert updated_event.title == "Test Mountain First Ascent"
            assert updated_event.is_generated is True

    def test_regenerate_event_low_confidence_unchanged(self, app, event_service):
        """Test that low-confidence regeneration leaves event unchanged"""
        with app.app_context():
            existing_event = HistoricalEvent(
                event_month=7, event_day=27, year=1953,
                title="Original Title",
                description="Original description",
                category=EventCategory.ACHIEVEMENT,
            )
            db.session.add(existing_event)
            db.session.commit()
            event_id = existing_event.id

            low_confidence = {
                "year": 1999, "title": "New Title", "description": "New",
                "location": "New", "people": [], "category": "achievement",
                "confidence": "low",
            }

            with patch.object(
                event_service.llm_service, "generate_historical_event"
            ) as mock_generate:
                mock_generate.return_value = low_confidence

                result = event_service.regenerate_event(event_id)

            # Should return unchanged event
            assert result.title == "Original Title"

    def test_regenerate_event_not_found(self, app, event_service):
        """Test regeneration of non-existent event"""
        with app.app_context():
            with pytest.raises(ContentGenerationError) as exc_info:
                event_service.regenerate_event(99999)

            assert "not found" in str(exc_info.value)

    def test_get_or_create_todays_event_existing(self, app, event_service):
        """Test getting existing today's event"""
        with app.app_context():
            with patch("utils.content_generation.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 7, 27)

                existing_event = HistoricalEvent(
                    event_month=7, event_day=27, year=1953,
                    title="Existing Today Event",
                    description="Already exists",
                    category=EventCategory.ACHIEVEMENT,
                )
                db.session.add(existing_event)
                db.session.commit()

                result = event_service.get_or_create_todays_event()

            assert result.id == existing_event.id

    def test_get_or_create_todays_event_create_new(self, app, event_service, mock_llm_response):
        """Test creating new today's event when none exists"""
        with app.app_context():
            with patch.object(event_service, "generate_daily_event") as mock_generate:
                mock_event = Mock()
                mock_generate.return_value = mock_event

                result = event_service.get_or_create_todays_event()

            assert result == mock_event

    def test_bulk_generate_events(self, app, event_service):
        """Test bulk event generation for date range"""
        with app.app_context():
            start_date = date(2024, 7, 25)
            end_date = date(2024, 7, 27)

            with patch.object(event_service, "generate_daily_event") as mock_generate:
                mock_events = [Mock(), Mock(), Mock()]
                mock_generate.side_effect = mock_events

                results = event_service.bulk_generate_events(start_date, end_date)

            assert len(results) == 3
            assert mock_generate.call_count == 3


class TestNewsService:
    """Test NewsService functionality (Future Phase 3B)"""

    @pytest.fixture
    def news_service(self, app):
        with app.app_context():
            return NewsService()

    def test_generate_daily_news_not_implemented(self, app, news_service):
        with app.app_context():
            assert news_service.generate_daily_news() == []

    def test_fetch_and_curate_news_not_implemented(self, app, news_service):
        with app.app_context():
            assert news_service.fetch_and_curate_news() == []


class TestContentManager:
    """Test ContentManager functionality"""

    @pytest.fixture
    def content_manager(self, app):
        with app.app_context():
            return ContentManager()

    def test_run_daily_generation_success(self, app, content_manager):
        with app.app_context():
            mock_event = Mock()
            with patch.object(
                content_manager.historical_service, "get_or_create_todays_event"
            ) as mock_get:
                mock_get.return_value = mock_event
                stats = content_manager.run_daily_generation()

            assert stats["historical_events"] == 1
            assert stats["errors"] == 0

    def test_run_daily_generation_with_error(self, app, content_manager):
        with app.app_context():
            with patch.object(
                content_manager.historical_service, "get_or_create_todays_event"
            ) as mock_get:
                mock_get.side_effect = ContentGenerationError("Failed")
                stats = content_manager.run_daily_generation()

            assert stats["historical_events"] == 0
            assert stats["errors"] == 1

    def test_get_dashboard_stats(self, app, content_manager):
        with app.app_context():
            events = [
                HistoricalEvent(
                    event_month=7, event_day=27, year=1953,
                    title="Event 1", description="Desc 1",
                    category=EventCategory.FIRST_ASCENT, is_featured=True,
                ),
                HistoricalEvent(
                    event_month=7, event_day=26, year=1965,
                    title="Event 2", description="Desc 2",
                    category=EventCategory.ACHIEVEMENT, is_featured=False,
                ),
            ]
            for event in events:
                db.session.add(event)
            db.session.commit()

            stats = content_manager.get_dashboard_stats()
            assert stats["total_historical_events"] == 2
            assert stats["featured_events"] == 1


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_generate_todays_historical_event_success(self, app):
        with app.app_context():
            mock_event = Mock()
            with patch("utils.content_generation.HistoricalEventService") as mock_cls:
                mock_service = Mock()
                mock_service.get_or_create_todays_event.return_value = mock_event
                mock_cls.return_value = mock_service
                result = generate_todays_historical_event()
            assert result == mock_event

    def test_generate_todays_historical_event_error(self, app):
        with app.app_context():
            with patch("utils.content_generation.HistoricalEventService") as mock_cls:
                mock_service = Mock()
                mock_service.get_or_create_todays_event.side_effect = ContentGenerationError("Failed")
                mock_cls.return_value = mock_service
                result = generate_todays_historical_event()
            assert result is None


class TestProviderPriority:
    """Test LLM provider priority by use case"""

    def test_historical_provider_order(self, app):
        """Test that historical events use Anthropic > Moonshot > DeepSeek"""
        with app.app_context():
            from utils.llm_providers import ProviderManager
            with patch("utils.llm_providers.AnthropicProvider") as mock_anthropic, \
                 patch("utils.llm_providers.MoonshotProvider") as mock_moonshot, \
                 patch("utils.llm_providers.DeepSeekProvider") as mock_deepseek:

                # Make all providers "configured"
                for mock_provider in [mock_anthropic, mock_moonshot, mock_deepseek]:
                    instance = Mock()
                    instance.is_configured = True
                    mock_provider.return_value = instance

                manager = ProviderManager()

                # Mock a successful call to track which provider is tried first
                test_messages = [{"role": "user", "content": "test"}]

                # Make anthropic succeed
                manager.providers["anthropic"].chat_completion.return_value = {"test": True}

                result = manager.chat_completion_with_fallback(
                    test_messages, use_case="historical"
                )

                # Anthropic should be called (it's first for historical)
                manager.providers["anthropic"].chat_completion.assert_called_once()

    def test_news_provider_order(self, app):
        """Test that news uses Moonshot > DeepSeek > Anthropic"""
        with app.app_context():
            from utils.llm_providers import ProviderManager
            with patch("utils.llm_providers.AnthropicProvider") as mock_anthropic, \
                 patch("utils.llm_providers.MoonshotProvider") as mock_moonshot, \
                 patch("utils.llm_providers.DeepSeekProvider") as mock_deepseek:

                for mock_provider in [mock_anthropic, mock_moonshot, mock_deepseek]:
                    instance = Mock()
                    instance.is_configured = True
                    mock_provider.return_value = instance

                manager = ProviderManager()

                test_messages = [{"role": "user", "content": "test"}]
                manager.providers["moonshot"].chat_completion.return_value = {"test": True}

                result = manager.chat_completion_with_fallback(
                    test_messages, use_case="news"
                )

                # Moonshot should be called first for news
                manager.providers["moonshot"].chat_completion.assert_called_once()
