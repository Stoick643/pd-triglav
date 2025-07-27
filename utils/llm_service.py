"""
LLM Service for AI Content Generation
Handles Kimi K2 (Moonshot) API integration for historical events
DeepSeek API configuration is reserved for future news implementation (Phase 3B)
"""

import json
import logging
import requests
import os
from datetime import datetime
from typing import Dict, List
from flask import current_app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_date_standard(date_obj: datetime) -> str:
    """
    Format date as '27 July' - day and month for historical events
    
    Args:
        date_obj: datetime object
        
    Returns:
        str: Formatted date like '27 July'
    """
    return date_obj.strftime("%d %B")


class LLMError(Exception):
    """Custom exception for LLM service errors"""
    pass


class LLMService:
    """Service for LLM API integration with Kimi K2 (Moonshot)"""
    
    def __init__(self):
        self.api_key = current_app.config.get('MOONSHOT_API_KEY')
        self.api_url = current_app.config.get('MOONSHOT_API_URL', 'https://api.moonshot.cn/v1/chat/completions')
        self.model = 'kimi-k2-0711-preview' #'moonshot-v1-8k'
        self.timeout = 30  # seconds
        self.max_retries = 3
        
        if not self.api_key:
            logger.warning("MOONSHOT_API_KEY not configured - LLM service will not work")
    
    def _load_prompt_template(self) -> str:
        """Load prompt template from file"""
        try:
            # Get the directory where this file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_file = os.path.join(current_dir, 'history_prompt.md')
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load prompt template: {e}")
            # Fallback to basic prompt
            return """You are a mountaineering historian. Find a significant historical event in mountaineering that occurred on {current_date}.
            
Respond in JSON format:
{{
    "year": number,
    "title": "event title",
    "description": "what happened",
    "location": "mountain/region",
    "people": ["names"],
    "url_1": "source URL",
    "category": "first_ascent|tragedy|discovery|achievement|expedition"
}}"""
    
    def _make_api_request(self, messages: List[Dict], temperature: float = 0.7) -> Dict:
        """Make request to Kimi K2 API with error handling and retries"""
        if not self.api_key:
            raise LLMError("LLM API key not configured")
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': 2000,
            'response_format': {"type": "json_object"}
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making LLM API request (attempt {attempt + 1}/{self.max_retries})")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    logger.info("LLM API request successful")
                    return json.loads(content)
                else:
                    error_msg = f"API returned status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    last_error = LLMError(error_msg)
                    
            except requests.exceptions.Timeout:
                error_msg = f"API request timeout (attempt {attempt + 1})"
                logger.error(error_msg)
                last_error = LLMError(error_msg)
                
            except requests.exceptions.RequestException as e:
                error_msg = f"API request failed: {e}"
                logger.error(error_msg)
                last_error = LLMError(error_msg)
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {e}"
                logger.error(error_msg)
                last_error = LLMError(error_msg)
                
            except (KeyError, IndexError) as e:
                error_msg = f"Unexpected API response format: {e}"
                logger.error(error_msg)
                last_error = LLMError(error_msg)
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retry...")
                import time
                time.sleep(wait_time)
        
        # All retries failed
        raise last_error
    
    def generate_historical_event(self) -> Dict:
        """
        Generate historical mountaineering event for today's date using improved prompt template
            
        Returns:
            Dict with event data matching HistoricalEvent model
            
        Raises:
            LLMError: If API request fails or returns invalid data
        """
        # Get today's date in the required format
        today = datetime.now()
        current_date = format_date_standard(today)
        
        # Load and format the prompt template
        prompt_template = self._load_prompt_template()
        prompt = prompt_template.format(current_date=current_date)
        
        messages = [
            {
                "role": "system",
                "content": "You are a knowledgeable mountaineering historian. Always respond with valid JSON containing historical mountaineering events."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        try:
            logger.info(f"Generating historical event for date: {current_date}")
            result = self._make_api_request(messages, temperature=0.3)  # Lower temp for factual content
            
            # Validate required fields (updated for new format)
            required_fields = ['year', 'title', 'description', 'location', 'people', 'category']
            for field in required_fields:
                if field not in result:
                    raise LLMError(f"Missing required field: {field}")
            
            # Handle new optional fields
            if 'url_1' not in result:
                result['url_1'] = result.get('url', None)  # Fallback to old 'url' field
            if 'url_2' not in result:
                result['url_2'] = None
            if 'methodology' not in result:
                result['methodology'] = None
            if 'url_methodology' not in result:
                result['url_methodology'] = None
            
            # Validate category
            valid_categories = ['first_ascent', 'tragedy', 'discovery', 'achievement', 'expedition']
            if result['category'] not in valid_categories:
                logger.warning(f"Invalid category '{result['category']}', defaulting to 'achievement'")
                result['category'] = 'achievement'
            
            # Ensure people is a list
            if not isinstance(result['people'], list):
                if isinstance(result['people'], str):
                    result['people'] = [name.strip() for name in result['people'].split(',')]
                else:
                    result['people'] = []
            
            # Add date field
            result['date'] = current_date
            
            logger.info(f"Successfully generated historical event: {result['title']}")
            return result
            
        except LLMError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error generating historical event: {e}"
            logger.error(error_msg)
            raise LLMError(error_msg)
    
    def generate_news_summary(self, articles: List[Dict]) -> List[Dict]:
        """
        Generate news summary from provided articles (Future Phase 3B)
        
        Args:
            articles: List of article dicts with title, summary, url
            
        Returns:
            List of 5 news items matching NewsItem model
            
        Raises:
            LLMError: If API request fails or returns invalid data
        """
        if not articles:
            return []
        
        # Prepare articles text for prompt
        articles_text = ""
        for i, article in enumerate(articles, 1):
            articles_text += f"[ARTICLE {i}]\n"
            articles_text += f"Title: {article.get('title', 'Unknown')}\n"
            articles_text += f"Summary: {article.get('summary', 'No summary')}\n"
            articles_text += f"URL: {article.get('url', 'No URL')}\n\n"
        
        prompt = f"""Analyze these recent news articles and select the 5 most relevant for mountaineers and climbers:

{articles_text}

Respond ONLY in JSON format as an array of 5 items:
[
    {{
        "title": "news_title",
        "summary": "brief_summary_1_to_2_sentences", 
        "category": "safety|conditions|achievements|gear|events",
        "url": "source_url_if_available",
        "relevance_score": 0.8,
        "source_name": "source_name"
    }}
]

Prioritize safety incidents, conditions updates, major achievements, gear innovations, and event announcements. 
Assign relevance_score from 0.0 to 1.0 based on importance to mountaineering community."""
        
        messages = [
            {
                "role": "system",
                "content": "You are a mountaineering news curator. Select and summarize the most relevant news for climbers and mountaineers."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            logger.info(f"Generating news summary from {len(articles)} articles")
            result = self._make_api_request(messages, temperature=0.5)
            
            # Ensure result is a list
            if not isinstance(result, list):
                raise LLMError("Expected list of news items")
            
            # Validate each news item
            valid_categories = ['safety', 'conditions', 'achievements', 'gear', 'events']
            validated_items = []
            
            for item in result[:5]:  # Limit to 5 items
                # Validate required fields
                required_fields = ['title', 'summary', 'category']
                if not all(field in item for field in required_fields):
                    logger.warning(f"Skipping invalid news item: {item}")
                    continue
                
                # Validate category
                if item['category'] not in valid_categories:
                    logger.warning(f"Invalid category '{item['category']}', defaulting to 'events'")
                    item['category'] = 'events'
                
                # Ensure relevance_score is float
                if 'relevance_score' not in item:
                    item['relevance_score'] = 0.5
                else:
                    try:
                        item['relevance_score'] = float(item['relevance_score'])
                        # Clamp to 0.0-1.0 range
                        item['relevance_score'] = max(0.0, min(1.0, item['relevance_score']))
                    except (ValueError, TypeError):
                        item['relevance_score'] = 0.5
                
                validated_items.append(item)
            
            logger.info(f"Successfully generated {len(validated_items)} news items")
            return validated_items
            
        except LLMError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error generating news summary: {e}"
            logger.error(error_msg)
            raise LLMError(error_msg)
    
    def get_fallback_content(self, content_type: str = 'historical') -> Dict:
        """
        Get fallback content when LLM service is unavailable
        
        Args:
            content_type: 'historical' or 'news'
            
        Returns:
            Dict with fallback content
        """
        if content_type == 'historical':
            today = format_date_standard(datetime.now())
            return {
                'date': today,
                'year': 1953,
                'title': 'First Ascent of Mount Everest',
                'description': 'On May 29, 1953, Edmund Hillary and Tenzing Norgay became the first confirmed climbers to reach the summit of Mount Everest. This achievement marked a pivotal moment in mountaineering history, proving that the world\'s highest peak could be conquered. Their success opened a new era of high-altitude climbing and inspired generations of mountaineers worldwide.',
                'location': 'Mount Everest, Nepal-Tibet border',
                'people': ['Edmund Hillary', 'Tenzing Norgay'],
                'url': None,
                'category': 'first_ascent'
            }
        else:
            return {
                'title': 'Mountaineering News Unavailable',
                'summary': 'Current mountaineering news is temporarily unavailable. Please check back later.',
                'category': 'events',
                'url': None,
                'relevance_score': 0.5,
                'source_name': 'System'
            }
    
    def test_connection(self) -> bool:
        """
        Test LLM API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a test assistant. Respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": "Respond with JSON: {\"status\": \"ok\", \"message\": \"test successful\"}"
                }
            ]
            result = self._make_api_request(messages, temperature=0.1)
            return result.get('status') == 'ok'
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False


# Convenience functions for easy usage
def generate_todays_historical_event() -> Dict:
    """Generate historical event for today's date"""
    service = LLMService()
    try:
        return service.generate_historical_event()
    except LLMError as e:
        logger.error(f"Failed to generate historical event: {e}")
        return service.get_fallback_content('historical')


def generate_news_from_articles(articles: List[Dict]) -> List[Dict]:
    """Generate news summary from articles (Future Phase 3B)"""
    service = LLMService()
    try:
        return service.generate_news_summary(articles)
    except LLMError as e:
        logger.error(f"Failed to generate news summary: {e}")
        return [service.get_fallback_content('news')]


def test_llm_service() -> bool:
    """Test if LLM service is working"""
    service = LLMService()
    return service.test_connection()