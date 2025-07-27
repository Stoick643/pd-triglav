"""
Content Generation Service
Handles daily generation and management of AI-powered content
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from flask import current_app

from models.user import db
from models.content import HistoricalEvent, NewsItem, EventCategory, NewsCategory
from utils.llm_service import LLMService, LLMError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentGenerationError(Exception):
    """Custom exception for content generation errors"""
    pass


class HistoricalEventService:
    """Service for managing historical events"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    def generate_daily_event(self, target_date: Optional[datetime] = None) -> HistoricalEvent:
        """
        Generate historical event for a specific date
        
        Args:
            target_date: Date to generate event for. If None, uses today.
            
        Returns:
            HistoricalEvent: Created database record
            
        Raises:
            ContentGenerationError: If generation fails
        """
        if target_date is None:
            target_date = datetime.now()
        
        date_string = target_date.strftime("%B %d")
        
        # Check if event already exists for this date
        existing_event = HistoricalEvent.get_event_for_date(date_string)
        if existing_event:
            logger.info(f"Historical event already exists for {date_string}")
            return existing_event
        
        try:
            logger.info(f"Generating new historical event for {date_string}")
            
            # Generate content using LLM
            event_data = self.llm_service.generate_historical_event()
            
            # Convert category string to enum
            try:
                category = EventCategory(event_data['category'])
            except ValueError:
                logger.warning(f"Invalid category '{event_data['category']}', using ACHIEVEMENT")
                category = EventCategory.ACHIEVEMENT
            
            # Create database record
            event = HistoricalEvent(
                date=event_data['date'],
                year=event_data['year'],
                title=event_data['title'],
                description=event_data['description'],
                location=event_data['location'],
                people=event_data['people'],
                url=event_data.get('url_1', event_data.get('url')),  # Handle both old and new format
                url_secondary=event_data.get('url_2'),
                category=category,
                methodology=event_data.get('methodology'),
                url_methodology=event_data.get('url_methodology'),
                is_generated=True
            )
            
            # Save to database
            db.session.add(event)
            db.session.commit()
            
            logger.info(f"Successfully created historical event: {event.title}")
            return event
            
        except LLMError as e:
            logger.error(f"LLM service failed: {e}")
            # Try to create fallback content
            return self._create_fallback_event(date_string)
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to generate historical event: {e}"
            logger.error(error_msg)
            raise ContentGenerationError(error_msg)
    
    def _create_fallback_event(self, date_string: str) -> HistoricalEvent:
        """Create fallback historical event when LLM fails"""
        try:
            fallback_data = self.llm_service.get_fallback_content('historical')
            fallback_data['date'] = date_string  # Override with requested date
            
            event = HistoricalEvent(
                date=fallback_data['date'],
                year=fallback_data['year'],
                title=fallback_data['title'],
                description=fallback_data['description'],
                location=fallback_data['location'],
                people=fallback_data['people'],
                url=fallback_data.get('url_1', fallback_data.get('url')),
                url_secondary=fallback_data.get('url_2'),
                category=EventCategory(fallback_data['category']),
                methodology=fallback_data.get('methodology'),
                url_methodology=fallback_data.get('url_methodology'),
                is_generated=False  # Mark as fallback content
            )
            
            db.session.add(event)
            db.session.commit()
            
            logger.info(f"Created fallback historical event for {date_string}")
            return event
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to create fallback event: {e}"
            logger.error(error_msg)
            raise ContentGenerationError(error_msg)
    
    def regenerate_event(self, event_id: int) -> HistoricalEvent:
        """
        Regenerate an existing historical event
        
        Args:
            event_id: ID of event to regenerate
            
        Returns:
            HistoricalEvent: Updated database record
            
        Raises:
            ContentGenerationError: If regeneration fails
        """
        event = HistoricalEvent.query.get(event_id)
        if not event:
            raise ContentGenerationError(f"Historical event {event_id} not found")
        
        try:
            logger.info(f"Regenerating historical event {event_id} for {event.date}")
            
            # Generate new content
            new_data = self.llm_service.generate_historical_event()
            logger.debug(f"Generated data keys: {list(new_data.keys()) if isinstance(new_data, dict) else type(new_data)}")
            logger.debug(f"Generated data: {new_data}")
            
            # Update existing record
            try:
                event.year = new_data['year']
                event.title = new_data['title']
                event.description = new_data['description']
                event.location = new_data['location']
                event.people = new_data['people']
            except KeyError as e:
                logger.error(f"Missing key in generated data: {e}. Available keys: {list(new_data.keys()) if isinstance(new_data, dict) else 'Not a dict'}")
                logger.error(f"Generated data content: {repr(new_data)}")
                raise ContentGenerationError(f"Invalid generated data: missing {e}")
            except TypeError as e:
                logger.error(f"Generated data is not a dictionary: {type(new_data)} = {repr(new_data)}")
                raise ContentGenerationError(f"Invalid generated data format: {e}")
            event.url = new_data.get('url_1', new_data.get('url'))
            event.url_secondary = new_data.get('url_2')
            event.methodology = new_data.get('methodology')
            event.url_methodology = new_data.get('url_methodology')
            
            try:
                event.category = EventCategory(new_data['category'])
            except ValueError:
                logger.warning(f"Invalid category '{new_data['category']}', keeping existing")
            
            event.is_generated = True
            event.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Successfully regenerated historical event: {event.title}")
            return event
            
        except LLMError as e:
            logger.error(f"LLM service failed during regeneration: {e}")
            logger.info("Using fallback content for regeneration")
            
            # Try to use fallback content instead of failing completely
            try:
                fallback_data = self.llm_service.get_fallback_content('historical')
                
                # Update with fallback content
                event.year = fallback_data['year']
                event.title = fallback_data['title']
                event.description = fallback_data['description']
                event.location = fallback_data['location']
                event.people = fallback_data['people']
                event.url = fallback_data.get('url')
                event.url_secondary = None
                event.methodology = "Fallback content used due to LLM service unavailability"
                event.url_methodology = None
                event.category = EventCategory(fallback_data['category'])
                event.is_generated = False  # Mark as fallback
                event.updated_at = datetime.utcnow()
                
                db.session.commit()
                logger.info(f"Successfully regenerated with fallback: {event.title}")
                return event
                
            except Exception as fallback_error:
                logger.error(f"Fallback regeneration also failed: {fallback_error}")
                raise ContentGenerationError(f"Regeneration failed: {e}")
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to regenerate historical event: {e}"
            logger.error(error_msg)
            raise ContentGenerationError(error_msg)
    
    def get_or_create_todays_event(self) -> HistoricalEvent:
        """Get today's historical event, creating if it doesn't exist"""
        today = datetime.now()
        date_string = today.strftime("%B %d")
        
        # Try to get existing event
        event = HistoricalEvent.get_event_for_date(date_string)
        if event:
            return event
        
        # Generate new event
        return self.generate_daily_event(today)
    
    def bulk_generate_events(self, start_date: date, end_date: date) -> List[HistoricalEvent]:
        """
        Generate historical events for a date range
        
        Args:
            start_date: Start date for generation
            end_date: End date for generation
            
        Returns:
            List[HistoricalEvent]: Generated events
        """
        events = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                # Convert date to datetime for generation
                target_datetime = datetime.combine(current_date, datetime.min.time())
                event = self.generate_daily_event(target_datetime)
                events.append(event)
                
            except ContentGenerationError as e:
                logger.error(f"Failed to generate event for {current_date}: {e}")
                # Continue with next date
            
            current_date += timedelta(days=1)
        
        return events


class NewsService:
    """Service for managing news items (Future Phase 3B)"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    def generate_daily_news(self, target_date: Optional[date] = None) -> List[NewsItem]:
        """
        Generate daily news items (Future implementation)
        
        Args:
            target_date: Date to generate news for. If None, uses today.
            
        Returns:
            List[NewsItem]: Generated news items
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"News generation not yet implemented for {target_date}")
        return []
    
    def fetch_and_curate_news(self) -> List[NewsItem]:
        """
        Fetch news from external sources and curate with AI (Future implementation)
        
        Returns:
            List[NewsItem]: Curated news items
        """
        logger.info("News fetching and curation not yet implemented")
        return []


class ContentManager:
    """Main service for managing all AI content generation"""
    
    def __init__(self):
        self.historical_service = HistoricalEventService()
        self.news_service = NewsService()
    
    def run_daily_generation(self) -> Dict[str, int]:
        """
        Run daily content generation for all content types
        
        Returns:
            Dict with generation statistics
        """
        stats = {
            'historical_events': 0,
            'news_items': 0,
            'errors': 0
        }
        
        try:
            # Generate today's historical event
            event = self.historical_service.get_or_create_todays_event()
            if event:
                stats['historical_events'] = 1
                logger.info(f"Daily historical event: {event.title}")
            
        except ContentGenerationError as e:
            logger.error(f"Failed to generate daily historical event: {e}")
            stats['errors'] += 1
        
        # Future: Generate daily news items
        # news_items = self.news_service.generate_daily_news()
        # stats['news_items'] = len(news_items)
        
        logger.info(f"Daily generation complete: {stats}")
        return stats
    
    def get_dashboard_stats(self) -> Dict[str, int]:
        """Get statistics for admin dashboard"""
        return {
            'total_historical_events': HistoricalEvent.query.count(),
            'total_news_items': NewsItem.query.count(),
            'generated_this_month': HistoricalEvent.query.filter(
                HistoricalEvent.created_at >= datetime.now().replace(day=1)
            ).count(),
            'featured_events': HistoricalEvent.query.filter_by(is_featured=True).count()
        }
    
    def test_services(self) -> Dict[str, bool]:
        """Test all content generation services"""
        results = {
            'llm_service': self.historical_service.llm_service.test_connection(),
            'database': True,  # Will be False if DB connection fails
            'historical_generation': False,
            'news_generation': False  # Future implementation
        }
        
        try:
            # Test historical event generation
            test_event = self.historical_service.llm_service.generate_historical_event()
            results['historical_generation'] = bool(test_event.get('title'))
        except Exception as e:
            logger.error(f"Historical generation test failed: {e}")
        
        return results


# Convenience functions for easy usage
def generate_todays_historical_event() -> Optional[HistoricalEvent]:
    """Generate today's historical event"""
    try:
        service = HistoricalEventService()
        return service.get_or_create_todays_event()
    except ContentGenerationError as e:
        logger.error(f"Failed to generate today's event: {e}")
        return None


def run_daily_content_generation() -> Dict[str, int]:
    """Run daily content generation"""
    manager = ContentManager()
    return manager.run_daily_generation()


def get_content_stats() -> Dict[str, int]:
    """Get content generation statistics"""
    manager = ContentManager()
    return manager.get_dashboard_stats()