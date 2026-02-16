"""
Mock LLM services for testing
Provides realistic responses without making real API calls
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


class MockLLMProvider:
    """Mock LLM provider that returns realistic responses"""

    def __init__(self, provider_name="mock"):
        self.provider_name = provider_name
        self.timeout = 30
        self.max_retries = 3
        self._call_count = 0

    def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """Mock chat completion that returns realistic historical event data"""
        self._call_count += 1

        # Simulate different responses based on the prompt content
        prompt_text = str(messages).lower()

        if "historical" in prompt_text and "mountaineering" in prompt_text:
            return self._get_historical_event_response()
        elif "news" in prompt_text:
            return self._get_news_response()
        else:
            return self._get_generic_response()

    def _get_historical_event_response(self) -> Dict:
        """Mock historical event response"""
        today = datetime.now()
        return {
            "id": f"mock-{self._call_count}",
            "object": "chat.completion",
            "created": int(today.timestamp()),
            "model": f"{self.provider_name}-mock",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "year": 1953,
                                "title": "Mock Historical Mountaineering Event",
                                "description": "A significant mock event in mountaineering history.",
                                "location": "Mock Mountain Range, Test Alps",
                                "people": ["Mock Climber", "Test Mountaineer"],
                                "category": "first_ascent",
                                "confidence": "high",
                                "methodology": "Mock historical research methodology",
                            }
                        ),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 150, "completion_tokens": 200, "total_tokens": 350},
        }

    def _get_news_response(self) -> Dict:
        """Mock news response"""
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "title": "Mock Mountaineering News",
                                "summary": "Mock news summary for testing purposes",
                                "items": [
                                    {
                                        "title": "Mock News Item 1",
                                        "summary": "Mock summary 1",
                                        "url": "https://mock-news.example.com/1",
                                    },
                                    {
                                        "title": "Mock News Item 2",
                                        "summary": "Mock summary 2",
                                        "url": "https://mock-news.example.com/2",
                                    },
                                ],
                            }
                        )
                    }
                }
            ]
        }

    def _get_generic_response(self) -> Dict:
        """Mock generic response"""
        return {"choices": [{"message": {"content": "Mock response for testing purposes"}}]}

    def test_connection(self) -> bool:
        """Mock connection test - always returns True"""
        return True


class MockProviderManager:
    """Mock provider manager that manages mock providers"""

    def __init__(self):
        self.providers = {
            "moonshot": MockLLMProvider("moonshot"),
            "deepseek": MockLLMProvider("deepseek"),
            "openai": MockLLMProvider("openai"),
        }
        self.current_provider_name = "moonshot"

    def get_current_provider(self):
        """Get current mock provider"""
        return self.providers[self.current_provider_name]

    def switch_provider(self, provider_name: str) -> bool:
        """Switch to different mock provider"""
        if provider_name in self.providers:
            self.current_provider_name = provider_name
            return True
        return False

    def test_all_providers(self) -> Dict[str, bool]:
        """Test all mock providers - always return success"""
        return {name: True for name in self.providers.keys()}


class MockLLMService:
    """Mock LLM service that provides realistic responses"""

    def __init__(self):
        self.provider_manager = MockProviderManager()
        self._generated_events = []

    def generate_historical_event(self, date: str = None, target_date: Optional[datetime] = None) -> Dict:
        """Generate mock historical event"""
        event_data = {
            "year": 1953 + len(self._generated_events),
            "title": f"Mock Event {len(self._generated_events) + 1}",
            "description": "A mock historical mountaineering event.",
            "location": f"Mock Location {len(self._generated_events) + 1}",
            "people": [f"Mock Person {i+1}" for i in range(2)],
            "category": "first_ascent",
            "confidence": "high",
            "methodology": "Mock methodology",
        }

        self._generated_events.append(event_data)
        return event_data

    def test_connection(self) -> bool:
        """Mock connection test"""
        return True


# Convenient mock factory functions
def create_mock_llm_service():
    """Create a mock LLM service"""
    return MockLLMService()


def create_mock_provider_manager():
    """Create a mock provider manager"""
    return MockProviderManager()


def create_mock_llm_provider(provider_name="mock"):
    """Create a mock LLM provider"""
    return MockLLMProvider(provider_name)


# Patch helpers for common test scenarios
def patch_llm_service():
    """Returns patches for LLM service components"""
    return [
        ("utils.llm_service.LLMService", MockLLMService),
        ("utils.llm_providers.ProviderManager", MockProviderManager),
    ]


def patch_llm_providers():
    """Returns patches for LLM provider components"""
    return [
        ("utils.llm_providers.MoonshotProvider", lambda: MockLLMProvider("moonshot")),
        ("utils.llm_providers.DeepSeekProvider", lambda: MockLLMProvider("deepseek")),
        ("utils.llm_providers.OpenAIProvider", lambda: MockLLMProvider("openai")),
    ]


# Mock responses for different scenarios
MOCK_RESPONSES = {
    "historical_event_success": {
        "year": 1953,
        "title": "Mock Historical Event",
        "description": "A mock event for testing",
        "location": "Mock Location",
        "people": ["Mock Person 1", "Mock Person 2"],
        "category": "first_ascent",
        "confidence": "high",
    },
    "historical_event_minimal": {
        "year": 1960,
        "title": "Minimal Mock Event",
        "description": "Minimal event for testing",
        "location": "Test Location",
        "people": ["Test Person"],
        "category": "achievement",
        "confidence": "medium",
    },
    "historical_event_invalid_category": {
        "year": 1970,
        "title": "Invalid Category Event",
        "description": "Event with invalid category",
        "location": "Test Location",
        "people": ["Test Person"],
        "category": "invalid_category",
        "confidence": "high",
    },
    "news_response": [
        {
            "title": "Mock News 1",
            "summary": "Mock news summary 1",
            "url": "https://mock-news.com/1",
        },
        {
            "title": "Mock News 2",
            "summary": "Mock news summary 2",
            "url": "https://mock-news.com/2",
        },
    ],
}
