"""Test LLM service functionality with multi-provider architecture"""

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


@pytest.mark.unit
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


@pytest.mark.unit 
class TestLLMService:
    """Test LLM service functionality with mocked providers"""
    
    @pytest.fixture
    def mock_provider_manager(self):
        """Mock provider manager"""
        mock_manager = Mock()
        mock_manager.get_available_providers.return_value = ['moonshot', 'deepseek']
        mock_manager.chat_completion_with_fallback.return_value = {'test': 'success'}
        mock_manager.test_all_providers.return_value = {'moonshot': True, 'deepseek': True}
        return mock_manager
    
    @pytest.fixture
    def llm_service(self, app, mock_provider_manager):
        """Create LLM service with mocked provider manager"""
        with app.app_context():
            with patch('utils.llm_service.ProviderManager') as mock_pm_class:
                mock_pm_class.return_value = mock_provider_manager
                return LLMService()
    
    def test_llm_service_initialization(self, llm_service, mock_provider_manager):
        """Test LLM service initialization with provider manager"""
        assert llm_service.provider_manager is not None
        assert llm_service.provider_manager == mock_provider_manager
    
    def test_llm_service_no_providers(self, app):
        """Test LLM service without available providers"""
        with app.app_context():
            with patch('utils.llm_service.ProviderManager') as mock_pm_class:
                mock_pm_class.return_value = None
                
                service = LLMService()
                assert service.provider_manager is None
    
    def test_load_prompt_template_success(self, llm_service):
        """Test loading prompt template from file"""
        mock_prompt_content = """Test prompt with [current_date]"""
        
        with patch('builtins.open', mock_open(read_data=mock_prompt_content)):
            result = llm_service._load_prompt_template()
            assert result == mock_prompt_content
    
    def test_load_prompt_template_file_not_found(self, llm_service):
        """Test fallback when prompt template file not found"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = llm_service._load_prompt_template()
            # Should return fallback prompt with square bracket placeholders
            assert '[current_date]' in result or '{current_date}' in result
            assert 'JSON format' in result
    
    def test_make_api_request_success(self, llm_service, mock_provider_manager):
        """Test successful API request via provider manager"""
        expected_result = {"year": 1953, "title": "Test Event"}
        mock_provider_manager.chat_completion_with_fallback.return_value = expected_result
        
        messages = [{'role': 'user', 'content': 'test'}]
        result = llm_service._make_api_request(messages, use_case='historical')
        
        assert result == expected_result
        mock_provider_manager.chat_completion_with_fallback.assert_called_once_with(
            messages=messages,
            use_case='historical',
            response_format={'type': 'json_object'}
        )
    
    def test_make_api_request_provider_error(self, llm_service, mock_provider_manager):
        """Test API request with provider error"""
        mock_provider_manager.chat_completion_with_fallback.side_effect = LLMError("Provider failed")
        
        messages = [{'role': 'user', 'content': 'test'}]
        
        with pytest.raises(LLMError) as exc_info:
            llm_service._make_api_request(messages)
        
        assert 'Provider request failed' in str(exc_info.value)
    
    def test_make_api_request_fallback_content(self, llm_service, mock_provider_manager):
        """Test API request returning fallback content"""
        fallback_result = {'fallback': True, 'title': 'Fallback Event'}
        mock_provider_manager.chat_completion_with_fallback.return_value = fallback_result
        
        messages = [{'role': 'user', 'content': 'test'}]
        result = llm_service._make_api_request(messages)
        
        assert result == fallback_result
        assert 'fallback' in result
    
    def test_make_api_request_no_provider_manager(self, app):
        """Test API request without provider manager"""
        with app.app_context():
            with patch('utils.llm_service.ProviderManager') as mock_pm_class:
                mock_pm_class.return_value = None
                
                service = LLMService()
                messages = [{'role': 'user', 'content': 'test'}]
                
                with pytest.raises(LLMError) as exc_info:
                    service._make_api_request(messages)
                
                assert 'Provider manager not initialized' in str(exc_info.value)
    
    @patch.object(LLMService, '_make_api_request')
    @patch.object(LLMService, '_load_prompt_template')
    def test_generate_historical_event_success(self, mock_load_prompt, mock_api_request, llm_service):
        """Test successful historical event generation"""
        # Mock prompt template with new placeholder format
        mock_load_prompt.return_value = "Find event for [current_date]"
        
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
    
    def test_test_connection_success(self, llm_service, mock_provider_manager):
        """Test successful connection test"""
        mock_provider_manager.test_all_providers.return_value = {'moonshot': True, 'deepseek': True}
        
        result = llm_service.test_connection()
        
        assert result is True
        mock_provider_manager.test_all_providers.assert_called_once()
    
    def test_test_connection_failure(self, llm_service, mock_provider_manager):
        """Test failed connection test"""
        mock_provider_manager.test_all_providers.return_value = {'moonshot': False, 'deepseek': False}
        
        result = llm_service.test_connection()
        
        assert result is False
    
    def test_test_connection_no_provider_manager(self, app):
        """Test connection test without provider manager"""
        with app.app_context():
            with patch('utils.llm_service.ProviderManager') as mock_pm_class:
                mock_pm_class.return_value = None
                
                service = LLMService()
                result = service.test_connection()
                
                assert result is False


@pytest.mark.unit
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