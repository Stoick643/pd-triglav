"""
Integration tests for LLM providers and services
These tests make real API calls and require valid API keys
"""

import os
import pytest
from datetime import datetime
from unittest.mock import patch

from app import create_app
from models.user import db
from utils.llm_providers import ProviderManager, MoonshotProvider, DeepSeekProvider
from utils.llm_service import LLMService, generate_todays_historical_event
from utils.content_generation import HistoricalEventService, ContentManager


def has_moonshot_api_key():
    """Check if Moonshot API key is configured"""
    return bool(os.getenv('MOONSHOT_API_KEY'))


def has_deepseek_api_key():
    """Check if DeepSeek API key is configured"""
    return bool(os.getenv('DEEPSEEK_API_KEY'))


def has_any_api_keys():
    """Check if any LLM API keys are configured"""
    return has_moonshot_api_key() or has_deepseek_api_key()


@pytest.mark.integration
class TestLLMProviderIntegration:
    """Integration tests for individual LLM providers"""
    
    @pytest.fixture(autouse=True)
    def setup_app_context(self):
        """Set up Flask app context for all tests"""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        yield
        self.app_context.pop()
    
    @pytest.mark.skipif(not has_moonshot_api_key(), reason="MOONSHOT_API_KEY not configured")
    def test_moonshot_basic_connectivity(self):
        """Test basic Moonshot API connectivity"""
        provider = MoonshotProvider()
        
        # Verify provider is configured
        assert provider.is_configured, "Moonshot provider should be configured"
        
        # Test basic connection
        result = provider.test_connection()
        assert result is True, "Moonshot API connection test should succeed"
    
    @pytest.mark.skipif(not has_moonshot_api_key(), reason="MOONSHOT_API_KEY not configured")
    def test_moonshot_chat_completion(self):
        """Test Moonshot chat completion with JSON response"""
        provider = MoonshotProvider()
        
        messages = [
            {"role": "system", "content": "You are a test assistant. Always respond with valid JSON."},
            {"role": "user", "content": 'Generate JSON: {"test": "success", "provider": "moonshot", "timestamp": "2025-01-01"}'}
        ]
        
        result = provider.chat_completion(messages, response_format={"type": "json_object"})
        
        # Verify response structure
        assert isinstance(result, dict), "Response should be a dictionary"
        assert "test" in result, "Response should contain 'test' field"
        assert result["test"] == "success", "Test field should indicate success"
    
    @pytest.mark.skipif(not has_deepseek_api_key(), reason="DEEPSEEK_API_KEY not configured")
    def test_deepseek_basic_connectivity(self):
        """Test basic DeepSeek API connectivity"""
        provider = DeepSeekProvider()
        
        # Verify provider is configured
        assert provider.is_configured, "DeepSeek provider should be configured"
        
        # Test basic connection
        result = provider.test_connection()
        assert result is True, "DeepSeek API connection test should succeed"
    
    @pytest.mark.skipif(not has_deepseek_api_key(), reason="DEEPSEEK_API_KEY not configured")
    def test_deepseek_chat_completion(self):
        """Test DeepSeek chat completion with JSON response"""
        provider = DeepSeekProvider()
        
        messages = [
            {"role": "system", "content": "You are a test assistant. Always respond with valid JSON."},
            {"role": "user", "content": 'Generate JSON: {"test": "success", "provider": "deepseek", "timestamp": "2025-01-01"}'}
        ]
        
        result = provider.chat_completion(messages, response_format={"type": "json_object"})
        
        # Verify response structure (DeepSeek may wrap the response)
        assert isinstance(result, dict), "Response should be a dictionary"
        
        # Handle both direct JSON and wrapped response formats
        if "response" in result:
            # Wrapped format: {"response": {...}, "status": "completed"}
            actual_result = result["response"]
        else:
            # Direct format: {...}
            actual_result = result
            
        assert "test" in actual_result, "Response should contain 'test' field"
        assert actual_result["test"] == "success", "Test field should indicate success"


@pytest.mark.integration
class TestProviderManagerIntegration:
    """Integration tests for provider manager and fallback logic"""
    
    @pytest.fixture(autouse=True)
    def setup_app_context(self):
        """Set up Flask app context for all tests"""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        yield
        self.app_context.pop()
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_provider_manager_initialization(self):
        """Test provider manager initializes available providers"""
        manager = ProviderManager()
        
        available_providers = manager.get_available_providers()
        assert len(available_providers) > 0, "At least one provider should be available"
        
        # Test that available providers are actually configured
        for provider_name in available_providers:
            provider = manager.get_provider(provider_name)
            assert provider is not None, f"Provider {provider_name} should be accessible"
            assert provider.is_configured, f"Provider {provider_name} should be configured"
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_provider_fallback_logic(self):
        """Test provider fallback logic with real APIs"""
        manager = ProviderManager()
        
        messages = [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": 'Respond with JSON: {"fallback_test": "success"}'}
        ]
        
        # Test historical use case (should prefer Moonshot)
        result = manager.chat_completion_with_fallback(
            messages=messages,
            use_case='historical',
            response_format={"type": "json_object"}
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "fallback_test" in result or "fallback" in result, "Should have test result or fallback indicator"
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_all_providers_test(self):
        """Test the test_all_providers method"""
        manager = ProviderManager()
        
        results = manager.test_all_providers()
        
        assert isinstance(results, dict), "Results should be a dictionary"
        assert len(results) > 0, "Should have test results for available providers"
        
        # Verify at least one provider is working
        working_providers = [name for name, status in results.items() if status]
        assert len(working_providers) > 0, "At least one provider should be working"


@pytest.mark.integration
class TestLLMServiceIntegration:
    """Integration tests for the LLM service layer"""
    
    @pytest.fixture(autouse=True)
    def setup_app_context(self):
        """Set up Flask app context for all tests"""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        yield
        self.app_context.pop()
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_llm_service_initialization(self):
        """Test LLM service initializes correctly"""
        service = LLMService()
        
        assert service.provider_manager is not None, "Provider manager should be initialized"
        assert len(service.provider_manager.get_available_providers()) > 0, "Should have available providers"
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_llm_service_connection_test(self):
        """Test LLM service connection testing"""
        service = LLMService()
        
        result = service.test_connection()
        assert result is True, "LLM service connection test should succeed"
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_historical_event_generation(self):
        """Test real historical event generation"""
        service = LLMService()
        
        event_data = service.generate_historical_event()
        
        # Verify required fields
        required_fields = ['year', 'title', 'description', 'location', 'people', 'category', 'date']
        for field in required_fields:
            assert field in event_data, f"Generated event should contain '{field}' field"
        
        # Verify data types
        assert isinstance(event_data['year'], int), "Year should be an integer"
        assert isinstance(event_data['title'], str), "Title should be a string"
        assert isinstance(event_data['description'], str), "Description should be a string"
        assert isinstance(event_data['location'], str), "Location should be a string"
        assert isinstance(event_data['people'], list), "People should be a list"
        assert isinstance(event_data['category'], str), "Category should be a string"
        assert isinstance(event_data['date'], str), "Date should be a string"
        
        # Verify reasonable values
        current_year = datetime.now().year
        assert 1700 <= event_data['year'] <= current_year, f"Year should be reasonable (1700-{current_year})"
        assert len(event_data['title']) > 10, "Title should be descriptive"
        assert len(event_data['description']) > 50, "Description should be detailed"
        
        # Verify category is valid
        valid_categories = ['first_ascent', 'tragedy', 'discovery', 'achievement', 'expedition']
        assert event_data['category'] in valid_categories, f"Category should be one of {valid_categories}"


@pytest.mark.integration
class TestContentGenerationIntegration:
    """Integration tests for content generation services"""
    
    @pytest.fixture(autouse=True)
    def setup_app_context(self):
        """Set up Flask app context for all tests"""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Set up database
        with self.app.app_context():
            db.create_all()
        
        yield
        
        # Cleanup
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        self.app_context.pop()
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_historical_event_service_generation(self):
        """Test historical event service with real API"""
        service = HistoricalEventService()
        
        # Generate event for a specific date
        target_date = datetime(2025, 7, 27)  # Use a fixed date for testing
        event = service.generate_daily_event(target_date)
        
        # Verify database record was created
        assert event.id is not None, "Event should be saved to database"
        assert event.date is not None, "Event should have a date"
        assert event.year is not None, "Event should have a year"
        assert event.title is not None, "Event should have a title"
        assert event.is_generated is True, "Event should be marked as generated"
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_content_manager_services(self):
        """Test content manager service tests"""
        manager = ContentManager()
        
        results = manager.test_services()
        
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'llm_service' in results, "Should test LLM service"
        assert 'database' in results, "Should test database"
        assert 'historical_generation' in results, "Should test historical generation"
        
        # Verify at least LLM service is working
        assert results['llm_service'] is True, "LLM service should be working"
        assert results['database'] is True, "Database should be working"
    
    @pytest.mark.skipif(not has_any_api_keys(), reason="No API keys configured")
    def test_generate_todays_historical_event_function(self):
        """Test the convenience function for generating today's event"""
        event_data = generate_todays_historical_event()
        
        # Should return either real event data or fallback content
        assert isinstance(event_data, dict), "Should return a dictionary"
        assert 'title' in event_data, "Should contain title"
        assert 'year' in event_data, "Should contain year"
        assert 'description' in event_data, "Should contain description"


# Helper functions for running integration tests
def run_basic_connectivity_tests():
    """Run basic connectivity tests manually"""
    print("=== LLM Integration Test Results ===")
    
    # Test API key availability
    print(f"Moonshot API Key: {'✅ Available' if has_moonshot_api_key() else '❌ Missing'}")
    print(f"DeepSeek API Key: {'✅ Available' if has_deepseek_api_key() else '❌ Missing'}")
    
    if not has_any_api_keys():
        print("❌ No API keys configured - integration tests will be skipped")
        return
    
    # Test providers
    app = create_app()
    with app.app_context():
        try:
            manager = ProviderManager()
            results = manager.test_all_providers()
            
            print(f"\n=== Provider Tests ===")
            for provider_name, status in results.items():
                print(f"{provider_name}: {'✅ Working' if status else '❌ Failed'}")
            
            # Test LLM service
            service = LLMService()
            service_ok = service.test_connection()
            print(f"\nLLM Service: {'✅ Working' if service_ok else '❌ Failed'}")
            
            print("\n🎉 Integration tests completed!")
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")


if __name__ == "__main__":
    # Allow running integration tests directly
    run_basic_connectivity_tests()