"""Test content generation services"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch
from utils.content_generation import (
    HistoricalEventService,
    NewsService,
    ContentManager,
    ContentGenerationError,
    generate_todays_historical_event,
    run_daily_content_generation,
    get_content_stats
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
        """Mock LLM API response"""
        return {
            'date': '27 July',
            'year': 1953,
            'title': 'Test Mountain First Ascent',
            'description': 'A significant test achievement in mountaineering history.',
            'location': 'Test Mountain Range',
            'people': ['Test Climber', 'Test Guide'],
            'url_1': 'https://example.com/source1',
            'url_2': 'https://example.com/source2',
            'category': 'first_ascent',
            'methodology': 'Direct date search',
            'url_methodology': 'Verified primary sources'
        }
    
    def test_generate_daily_event_success(self, app, event_service, mock_llm_response):
        """Test successful daily event generation"""
        with app.app_context():
            with patch.object(event_service.llm_service, 'generate_historical_event') as mock_generate:
                mock_generate.return_value = mock_llm_response
                
                with patch('utils.content_generation.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2024, 7, 27)
                    
                    event = event_service.generate_daily_event()
            
            # Verify event was created and saved
            assert event is not None
            assert event.date == '27 July'
            assert event.year == 1953
            assert event.title == 'Test Mountain First Ascent'
            assert event.url == 'https://example.com/source1'
            assert event.url_secondary == 'https://example.com/source2'
            assert event.methodology == 'Direct date search'
            assert event.category == EventCategory.FIRST_ASCENT
            assert event.is_generated is True
            
            # Verify it was saved to database
            saved_event = HistoricalEvent.query.filter_by(date='27 July', year=1953).first()
            assert saved_event is not None
            assert saved_event.id == event.id
    
    def test_generate_daily_event_with_target_date(self, app, event_service, mock_llm_response):
        """Test generating event for specific target date"""
        with app.app_context():
            target_date = datetime(2024, 8, 15)
            mock_llm_response['date'] = '15 August'
            
            with patch.object(event_service.llm_service, 'generate_historical_event') as mock_generate:
                mock_generate.return_value = mock_llm_response
                
                event = event_service.generate_daily_event(target_date)
            
            assert event.date == '15 August'
    
    def test_generate_daily_event_already_exists(self, app, event_service):
        """Test generation when event already exists for date"""
        with app.app_context():
            # Create existing event
            existing_event = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Existing Event',
                description='Already exists',
                category=EventCategory.ACHIEVEMENT
            )
            db.session.add(existing_event)
            db.session.commit()
            
            with patch('utils.content_generation.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 7, 27)
                
                # Should return existing event, not generate new one
                result = event_service.generate_daily_event()
            
            assert result.id == existing_event.id
            assert result.title == 'Existing Event'
    
    def test_generate_daily_event_invalid_category(self, app, event_service, mock_llm_response):
        """Test handling of invalid category from LLM"""
        with app.app_context():
            mock_llm_response['category'] = 'invalid_category'
            
            with patch.object(event_service.llm_service, 'generate_historical_event') as mock_generate:
                mock_generate.return_value = mock_llm_response
                
                event = event_service.generate_daily_event()
            
            # Should default to ACHIEVEMENT for invalid category
            assert event.category == EventCategory.ACHIEVEMENT
    
    def test_generate_daily_event_llm_error_fallback(self, app, event_service):
        """Test fallback when LLM service fails"""
        with app.app_context():
            with patch.object(event_service.llm_service, 'generate_historical_event') as mock_generate:
                mock_generate.side_effect = LLMError("API failed")
                
                with patch.object(event_service, '_create_fallback_event') as mock_fallback:
                    mock_fallback_event = Mock()
                    mock_fallback.return_value = mock_fallback_event
                    
                    result = event_service.generate_daily_event()
                    
                    assert result == mock_fallback_event
                    mock_fallback.assert_called_once()
    
    def test_create_fallback_event(self, app, event_service):
        """Test fallback event creation"""
        with app.app_context():
            fallback_data = {
                'date': '27 July',
                'year': 1953,
                'title': 'Fallback Event',
                'description': 'Fallback description',
                'location': 'Fallback Location',
                'people': ['Fallback Person'],
                'url': None,
                'category': 'achievement'
            }
            
            with patch.object(event_service.llm_service, 'get_fallback_content') as mock_fallback:
                mock_fallback.return_value = fallback_data
                
                event = event_service._create_fallback_event('27 July')
            
            assert event.title == 'Fallback Event'
            assert event.is_generated is False  # Marked as fallback
            assert event.date == '27 July'
    
    def test_regenerate_event_success(self, app, event_service, mock_llm_response):
        """Test successful event regeneration"""
        with app.app_context():
            # Create existing event
            existing_event = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Old Event',
                description='Old description',
                category=EventCategory.ACHIEVEMENT
            )
            db.session.add(existing_event)
            db.session.commit()
            event_id = existing_event.id
            
            # Mock new LLM response
            with patch.object(event_service.llm_service, 'generate_historical_event') as mock_generate:
                mock_generate.return_value = mock_llm_response
                
                updated_event = event_service.regenerate_event(event_id)
            
            # Verify event was updated
            assert updated_event.id == event_id
            assert updated_event.title == 'Test Mountain First Ascent'
            assert updated_event.description == 'A significant test achievement in mountaineering history.'
            assert updated_event.is_generated is True
            assert updated_event.updated_at is not None
    
    def test_regenerate_event_not_found(self, app, event_service):
        """Test regeneration of non-existent event"""
        with app.app_context():
            with pytest.raises(ContentGenerationError) as exc_info:
                event_service.regenerate_event(99999)
            
            assert 'not found' in str(exc_info.value)
    
    def test_get_or_create_todays_event_existing(self, app, event_service):
        """Test getting existing today's event"""
        with app.app_context():
            # Create existing event for today
            with patch('utils.content_generation.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 7, 27)
                
                existing_event = HistoricalEvent(
                    date='27 July',
                    year=1953,
                    title='Existing Today Event',
                    description='Already exists',
                    category=EventCategory.ACHIEVEMENT
                )
                db.session.add(existing_event)
                db.session.commit()
                
                result = event_service.get_or_create_todays_event()
            
            assert result.id == existing_event.id
            assert result.title == 'Existing Today Event'
    
    def test_get_or_create_todays_event_create_new(self, app, event_service, mock_llm_response):
        """Test creating new today's event when none exists"""
        with app.app_context():
            with patch.object(event_service, 'generate_daily_event') as mock_generate:
                mock_event = Mock()
                mock_generate.return_value = mock_event
                
                result = event_service.get_or_create_todays_event()
            
            assert result == mock_event
            mock_generate.assert_called_once()
    
    def test_bulk_generate_events(self, app, event_service):
        """Test bulk event generation for date range"""
        with app.app_context():
            start_date = date(2024, 7, 25)
            end_date = date(2024, 7, 27)  # 3 days
            
            with patch.object(event_service, 'generate_daily_event') as mock_generate:
                mock_events = [Mock(), Mock(), Mock()]
                mock_generate.side_effect = mock_events
                
                results = event_service.bulk_generate_events(start_date, end_date)
            
            assert len(results) == 3
            assert mock_generate.call_count == 3
            assert results == mock_events
    
    def test_bulk_generate_events_with_errors(self, app, event_service):
        """Test bulk generation with some failures"""
        with app.app_context():
            start_date = date(2024, 7, 25)
            end_date = date(2024, 7, 27)  # 3 days
            
            with patch.object(event_service, 'generate_daily_event') as mock_generate:
                # First call succeeds, second fails, third succeeds
                mock_generate.side_effect = [
                    Mock(),
                    ContentGenerationError("Failed"),
                    Mock()
                ]
                
                results = event_service.bulk_generate_events(start_date, end_date)
            
            # Should return 2 successful events, skip the failed one
            assert len(results) == 2
            assert mock_generate.call_count == 3


class TestNewsService:
    """Test NewsService functionality (Future Phase 3B)"""
    
    @pytest.fixture
    def news_service(self, app):
        """Create NewsService instance"""
        with app.app_context():
            return NewsService()
    
    def test_generate_daily_news_not_implemented(self, app, news_service):
        """Test that news generation is not yet implemented"""
        with app.app_context():
            result = news_service.generate_daily_news()
            assert result == []
    
    def test_fetch_and_curate_news_not_implemented(self, app, news_service):
        """Test that news fetching is not yet implemented"""
        with app.app_context():
            result = news_service.fetch_and_curate_news()
            assert result == []


class TestContentManager:
    """Test ContentManager functionality"""
    
    @pytest.fixture
    def content_manager(self, app):
        """Create ContentManager instance"""
        with app.app_context():
            return ContentManager()
    
    def test_run_daily_generation_success(self, app, content_manager):
        """Test successful daily content generation"""
        with app.app_context():
            mock_event = Mock()
            
            with patch.object(content_manager.historical_service, 'get_or_create_todays_event') as mock_get:
                mock_get.return_value = mock_event
                
                stats = content_manager.run_daily_generation()
            
            assert stats['historical_events'] == 1
            assert stats['news_items'] == 0
            assert stats['errors'] == 0
    
    def test_run_daily_generation_with_error(self, app, content_manager):
        """Test daily generation with error"""
        with app.app_context():
            with patch.object(content_manager.historical_service, 'get_or_create_todays_event') as mock_get:
                mock_get.side_effect = ContentGenerationError("Generation failed")
                
                stats = content_manager.run_daily_generation()
            
            assert stats['historical_events'] == 0
            assert stats['news_items'] == 0
            assert stats['errors'] == 1
    
    def test_get_dashboard_stats(self, app, content_manager):
        """Test dashboard statistics calculation"""
        with app.app_context():
            # Create sample events
            events = [
                HistoricalEvent(
                    date='27 July',
                    year=1953,
                    title='Event 1',
                    description='Description 1',
                    category=EventCategory.FIRST_ASCENT,
                    is_featured=True
                ),
                HistoricalEvent(
                    date='26 July',
                    year=1965,
                    title='Event 2',
                    description='Description 2',
                    category=EventCategory.ACHIEVEMENT,
                    is_featured=False
                )
            ]
            
            for event in events:
                db.session.add(event)
            db.session.commit()
            
            stats = content_manager.get_dashboard_stats()
            
            assert stats['total_historical_events'] == 2
            assert stats['total_news_items'] == 0
            assert stats['featured_events'] == 1
            assert stats['generated_this_month'] >= 0  # Depends on creation dates
    
    def test_test_services(self, app, content_manager):
        """Test service testing functionality"""
        with app.app_context():
            with patch.object(content_manager.historical_service.llm_service, 'test_connection') as mock_test_llm:
                mock_test_llm.return_value = True
                
                with patch.object(content_manager.historical_service.llm_service, 'generate_historical_event') as mock_generate:
                    mock_generate.return_value = {'title': 'Test Event'}
                    
                    results = content_manager.test_services()
            
            assert results['llm_service'] is True
            assert results['database'] is True
            assert results['historical_generation'] is True
            assert results['news_generation'] is False  # Not implemented yet
    
    def test_test_services_with_failures(self, app, content_manager):
        """Test service testing with failures"""
        with app.app_context():
            with patch.object(content_manager.historical_service.llm_service, 'test_connection') as mock_test_llm:
                mock_test_llm.return_value = False
                
                with patch.object(content_manager.historical_service.llm_service, 'generate_historical_event') as mock_generate:
                    mock_generate.side_effect = Exception("Generation failed")
                    
                    results = content_manager.test_services()
            
            assert results['llm_service'] is False
            assert results['database'] is True
            assert results['historical_generation'] is False


class TestConvenienceFunctions:
    """Test module-level convenience functions"""
    
    def test_generate_todays_historical_event_success(self, app):
        """Test successful today's event generation function"""
        with app.app_context():
            mock_event = Mock()
            
            with patch('utils.content_generation.HistoricalEventService') as mock_service_class:
                mock_service = Mock()
                mock_service.get_or_create_todays_event.return_value = mock_event
                mock_service_class.return_value = mock_service
                
                result = generate_todays_historical_event()
            
            assert result == mock_event
    
    def test_generate_todays_historical_event_error(self, app):
        """Test today's event generation with error"""
        with app.app_context():
            with patch('utils.content_generation.HistoricalEventService') as mock_service_class:
                mock_service = Mock()
                mock_service.get_or_create_todays_event.side_effect = ContentGenerationError("Failed")
                mock_service_class.return_value = mock_service
                
                result = generate_todays_historical_event()
            
            assert result is None
    
    def test_run_daily_content_generation_function(self, app):
        """Test daily content generation function"""
        with app.app_context():
            expected_stats = {'historical_events': 1, 'news_items': 0, 'errors': 0}
            
            with patch('utils.content_generation.ContentManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.run_daily_generation.return_value = expected_stats
                mock_manager_class.return_value = mock_manager
                
                result = run_daily_content_generation()
            
            assert result == expected_stats
    
    def test_get_content_stats_function(self, app):
        """Test content statistics function"""
        with app.app_context():
            expected_stats = {'total_historical_events': 5, 'total_news_items': 0, 'featured_events': 2}
            
            with patch('utils.content_generation.ContentManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.get_dashboard_stats.return_value = expected_stats
                mock_manager_class.return_value = mock_manager
                
                result = get_content_stats()
            
            assert result == expected_stats


class TestContentGenerationIntegration:
    """Integration tests for content generation workflow"""
    
    def test_full_content_generation_workflow(self, app):
        """Test complete content generation workflow from start to finish"""
        with app.app_context():
            # Mock LLM response
            mock_llm_response = {
                'date': '27 July',
                'year': 1953,
                'title': 'Integration Test Event',
                'description': 'Full workflow test event.',
                'location': 'Test Mountain',
                'people': ['Test Climber'],
                'url_1': 'https://example.com/source',
                'category': 'first_ascent'
            }
            
            # Create service and mock LLM
            service = HistoricalEventService()
            
            with patch.object(service.llm_service, 'generate_historical_event') as mock_generate:
                mock_generate.return_value = mock_llm_response
                
                with patch('utils.content_generation.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2024, 7, 27)
                    
                    # Generate event
                    event = service.generate_daily_event()
            
            # Verify complete workflow
            assert event is not None
            assert event.title == 'Integration Test Event'
            
            # Verify database persistence
            saved_event = HistoricalEvent.query.filter_by(date='27 July', year=1953).first()
            assert saved_event is not None
            assert saved_event.title == 'Integration Test Event'
            
            # Test retrieval methods
            todays_event = HistoricalEvent.get_todays_event()
            assert todays_event.id == event.id
            
            # Test regeneration
            mock_llm_response['title'] = 'Regenerated Event'
            with patch.object(service.llm_service, 'generate_historical_event') as mock_regenerate:
                mock_regenerate.return_value = mock_llm_response
                
                regenerated = service.regenerate_event(event.id)
            
            assert regenerated.title == 'Regenerated Event'
            assert regenerated.id == event.id  # Same event, updated content