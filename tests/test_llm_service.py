"""Test LLM service functionality"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock, mock_open
from utils.llm_service import (
    LLMService, 
    LLMError, 
    format_date_standard,
    generate_todays_historical_event,
    test_llm_service
)


class TestDateFormatting:
    """Test date formatting utility functions"""
    
    def test_format_date_standard_various_dates(self):
        """Test date formatting with various dates"""
        test_cases = [
            (datetime(2024, 7, 27), '27 July'),
            (datetime(2024, 1, 1), '01 January'),
            (datetime(2024, 12, 31), '31 December'),
            (datetime(2024, 2, 29), '29 February'),  # Leap year
            (datetime(2023, 2, 28), '28 February'),  # Non-leap year
            (datetime(2024, 5, 5), '05 May'),
        ]
        
        for date_input, expected in test_cases:
            result = format_date_standard(date_input)
            assert result == expected, f"Expected {expected}, got {result} for {date_input}"
    
    def test_format_date_standard_consistency(self):
        """Test that formatting is consistent across calls"""
        test_date = datetime(2024, 7, 27)
        
        result1 = format_date_standard(test_date)
        result2 = format_date_standard(test_date)
        
        assert result1 == result2
        assert result1 == '27 July'


class TestLLMService:
    """Test LLM service functionality"""
    
    @pytest.fixture
    def mock_app_config(self):
        """Mock Flask app config"""
        return {
            'MOONSHOT_API_KEY': 'test-api-key',
            'MOONSHOT_API_URL': 'https://api.test.com/v1/chat/completions'
        }
    
    @pytest.fixture
    def llm_service(self, app, mock_app_config):
        """Create LLM service with mocked config"""
        with app.app_context():
            with patch('utils.llm_service.current_app') as mock_app:
                mock_app.config.get.side_effect = lambda key, default=None: mock_app_config.get(key, default)
                return LLMService()
    
    def test_llm_service_initialization(self, llm_service):
        """Test LLM service initialization"""
        assert llm_service.api_key == 'test-api-key'
        assert llm_service.api_url == 'https://api.test.com/v1/chat/completions'
        assert llm_service.model == 'kimi-k2-0711-preview'
        assert llm_service.timeout == 30
        assert llm_service.max_retries == 3
    
    def test_llm_service_no_api_key(self, app):
        """Test LLM service without API key"""
        with app.app_context():
            with patch('utils.llm_service.current_app') as mock_app:
                mock_app.config.get.return_value = None
                
                service = LLMService()
                assert service.api_key is None
    
    def test_load_prompt_template_success(self, llm_service):
        """Test loading prompt template from file"""
        mock_prompt_content = """Test prompt with {current_date}"""
        
        with patch('builtins.open', mock_open(read_data=mock_prompt_content)):
            result = llm_service._load_prompt_template()
            assert result == mock_prompt_content
    
    def test_load_prompt_template_file_not_found(self, llm_service):
        """Test fallback when prompt template file not found"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = llm_service._load_prompt_template()
            # Should return fallback prompt
            assert '{current_date}' in result
            assert 'JSON format' in result
    
    @patch('utils.llm_service.requests.post')
    def test_make_api_request_success(self, mock_post, llm_service):
        """Test successful API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"year": 1953, "title": "Test Event"}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        messages = [{'role': 'user', 'content': 'test'}]
        result = llm_service._make_api_request(messages)
        
        assert result == {"year": 1953, "title": "Test Event"}
        mock_post.assert_called_once()
        
        # Verify request parameters
        call_args = mock_post.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer test-api-key'
        assert call_args[1]['json']['model'] == 'kimi-k2-0711-preview'
        assert call_args[1]['json']['messages'] == messages
    
    @patch('utils.llm_service.requests.post')
    def test_make_api_request_http_error(self, mock_post, llm_service):
        """Test API request with HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = 'Rate limit exceeded'
        mock_post.return_value = mock_response
        
        messages = [{'role': 'user', 'content': 'test'}]
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._make_api_request(messages)
        
        assert 'API returned status 429' in str(exc_info.value)
    
    @patch('utils.llm_service.requests.post')
    def test_make_api_request_timeout(self, mock_post, llm_service):
        """Test API request timeout"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        messages = [{'role': 'user', 'content': 'test'}]
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._make_api_request(messages)
        
        assert 'timeout' in str(exc_info.value)
    
    @patch('utils.llm_service.requests.post')
    def test_make_api_request_invalid_json(self, mock_post, llm_service):
        """Test API request with invalid JSON response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'invalid json content'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        messages = [{'role': 'user', 'content': 'test'}]
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._make_api_request(messages)
        
        assert 'Failed to parse JSON' in str(exc_info.value)
    
    @patch('utils.llm_service.requests.post')
    def test_make_api_request_no_api_key(self, mock_post):
        """Test API request without API key"""
        with patch('utils.llm_service.current_app') as mock_app:
            mock_app.config.get.return_value = None
            
            service = LLMService()
            messages = [{'role': 'user', 'content': 'test'}]
            
            with pytest.raises(LLMError) as exc_info:
                service._make_api_request(messages)
            
            assert 'API key not configured' in str(exc_info.value)
            mock_post.assert_not_called()
    
    @patch('utils.llm_service.requests.post')
    @patch('utils.llm_service.time.sleep')  # Mock sleep for faster tests
    def test_make_api_request_retry_logic(self, mock_sleep, mock_post, llm_service):
        """Test retry logic on failures"""
        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = 'Internal server error'
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"success": true}'
                }
            }]
        }
        
        mock_post.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]
        
        messages = [{'role': 'user', 'content': 'test'}]
        result = llm_service._make_api_request(messages)
        
        assert result == {"success": True}
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2  # Should sleep between retries
    
    @patch.object(LLMService, '_make_api_request')
    @patch.object(LLMService, '_load_prompt_template')
    def test_generate_historical_event_success(self, mock_load_prompt, mock_api_request, llm_service):
        """Test successful historical event generation"""
        # Mock prompt template
        mock_load_prompt.return_value = "Find event for {current_date}"
        
        # Mock API response
        mock_api_response = {
            'year': 1953,
            'title': 'Test Mountain First Ascent',
            'description': 'A test mountaineering achievement.',
            'location': 'Test Range',
            'people': ['Test Climber'],
            'url_1': 'https://example.com/source1',
            'url_2': 'https://example.com/source2',
            'category': 'first_ascent',
            'methodology': 'Direct date search',
            'url_methodology': 'Primary source verification'
        }
        mock_api_request.return_value = mock_api_response
        
        with patch('utils.llm_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime
            
            result = llm_service.generate_historical_event()
        
        # Verify result
        assert result['year'] == 1953
        assert result['title'] == 'Test Mountain First Ascent'
        assert result['date'] == '27 July'
        assert result['url_1'] == 'https://example.com/source1'
        assert result['url_2'] == 'https://example.com/source2'
        
        # Verify prompt was formatted with current date
        mock_load_prompt.assert_called_once()
        mock_api_request.assert_called_once()
    
    @patch.object(LLMService, '_make_api_request')
    def test_generate_historical_event_missing_fields(self, mock_api_request, llm_service):
        """Test event generation with missing required fields"""
        # Mock API response missing required fields
        mock_api_response = {
            'year': 1953,
            'title': 'Test Event'
            # Missing: description, location, people, category
        }
        mock_api_request.return_value = mock_api_response
        
        with pytest.raises(LLMError) as exc_info:
            llm_service.generate_historical_event()
        
        assert 'Missing required field' in str(exc_info.value)
    
    @patch.object(LLMService, '_make_api_request')
    def test_generate_historical_event_invalid_category(self, mock_api_request, llm_service):
        """Test event generation with invalid category"""
        # Mock API response with invalid category
        mock_api_response = {
            'year': 1953,
            'title': 'Test Event',
            'description': 'Test description',
            'location': 'Test Location',
            'people': ['Test Person'],
            'category': 'invalid_category'
        }
        mock_api_request.return_value = mock_api_response
        
        result = llm_service.generate_historical_event()
        
        # Should default to 'achievement' for invalid category
        assert result['category'] == 'achievement'
    
    @patch.object(LLMService, '_make_api_request')
    def test_generate_historical_event_people_string_conversion(self, mock_api_request, llm_service):
        """Test conversion of people field from string to list"""
        # Mock API response with people as string
        mock_api_response = {
            'year': 1953,
            'title': 'Test Event',
            'description': 'Test description',
            'location': 'Test Location',
            'people': 'Climber One, Climber Two, Guide',
            'category': 'first_ascent'
        }
        mock_api_request.return_value = mock_api_response
        
        result = llm_service.generate_historical_event()
        
        # Should convert string to list
        assert result['people'] == ['Climber One', 'Climber Two', 'Guide']
    
    def test_get_fallback_content_historical(self, llm_service):
        """Test fallback content for historical events"""
        with patch('utils.llm_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime
            
            result = llm_service.get_fallback_content('historical')
        
        assert result['date'] == '27 July'
        assert result['year'] == 1953
        assert 'Everest' in result['title']
        assert result['category'] == 'first_ascent'
        assert 'Edmund Hillary' in result['people']
    
    def test_get_fallback_content_news(self, llm_service):
        """Test fallback content for news"""
        result = llm_service.get_fallback_content('news')
        
        assert 'Unavailable' in result['title']
        assert result['category'] == 'events'
        assert result['relevance_score'] == 0.5
    
    @patch.object(LLMService, '_make_api_request')
    def test_test_connection_success(self, mock_api_request, llm_service):
        """Test successful connection test"""
        mock_api_request.return_value = {'status': 'ok'}
        
        result = llm_service.test_connection()
        
        assert result is True
        mock_api_request.assert_called_once()
    
    @patch.object(LLMService, '_make_api_request')
    def test_test_connection_failure(self, mock_api_request, llm_service):
        """Test failed connection test"""
        mock_api_request.side_effect = LLMError("Connection failed")
        
        result = llm_service.test_connection()
        
        assert result is False


class TestConvenienceFunctions:
    """Test module-level convenience functions"""
    
    @patch('utils.llm_service.LLMService')
    def test_generate_todays_historical_event_success(self, mock_llm_service_class):
        """Test successful today's event generation"""
        mock_service = Mock()
        mock_service.generate_historical_event.return_value = {'title': 'Test Event'}
        mock_llm_service_class.return_value = mock_service
        
        result = generate_todays_historical_event()
        
        assert result == {'title': 'Test Event'}
        mock_service.generate_historical_event.assert_called_once()
    
    @patch('utils.llm_service.LLMService')
    def test_generate_todays_historical_event_fallback(self, mock_llm_service_class):
        """Test fallback on generation failure"""
        mock_service = Mock()
        mock_service.generate_historical_event.side_effect = LLMError("API failed")
        mock_service.get_fallback_content.return_value = {'title': 'Fallback Event'}
        mock_llm_service_class.return_value = mock_service
        
        result = generate_todays_historical_event()
        
        assert result == {'title': 'Fallback Event'}
        mock_service.get_fallback_content.assert_called_once_with('historical')
    
    @patch('utils.llm_service.LLMService')
    def test_test_llm_service_function(self, mock_llm_service_class):
        """Test LLM service testing function"""
        mock_service = Mock()
        mock_service.test_connection.return_value = True
        mock_llm_service_class.return_value = mock_service
        
        result = test_llm_service()
        
        assert result is True
        mock_service.test_connection.assert_called_once()