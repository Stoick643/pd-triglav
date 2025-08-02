"""
LLM Provider Architecture
Supports multiple LLM providers with a unified interface
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Custom exception for LLM provider errors"""

    pass


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self):
        self.timeout = 30
        self.max_retries = 3

    @abstractmethod
    def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """
        Create a chat completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Provider-specific options

        Returns:
            Dict with response data

        Raises:
            LLMError: If API request fails
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the provider is available

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def get_fallback_content(self, content_type: str = "historical") -> Dict:
        """
        Get fallback content when provider is unavailable

        Args:
            content_type: 'historical' or 'news'

        Returns:
            Dict with fallback content
        """
        pass

    @abstractmethod
    def get_cost_per_token(self) -> float:
        """
        Get estimated cost per token for this provider

        Returns:
            Cost per token in USD
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured"""
        pass


class MoonshotProvider(BaseLLMProvider):
    """Moonshot AI (Kimi K2) provider using OpenAI client"""

    def __init__(self):
        super().__init__()
        self.api_key = current_app.config.get("MOONSHOT_API_KEY")
        self.base_url = current_app.config.get("MOONSHOT_API_URL", "https://api.moonshot.ai/v1")
        self.model = "kimi-k2-0711-preview"

        if not self.api_key:
            logger.warning("MOONSHOT_API_KEY not configured")

    @property
    def provider_name(self) -> str:
        return "Moonshot (Kimi K2)"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """Create chat completion using OpenAI client with Moonshot"""
        if not self.is_configured:
            raise LLMError("Moonshot provider not configured")

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            # Set defaults with option to override
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.3),
                "max_tokens": kwargs.get("max_tokens", 2000),
            }

            # Add response format if specified
            response_format = kwargs.get("response_format")
            if response_format:
                params["response_format"] = response_format

            logger.info(f"Making Moonshot API request with model {self.model}")
            completion = client.chat.completions.create(**params)

            # Extract content
            content = completion.choices[0].message.content
            logger.info("Moonshot API request successful")

            # Parse JSON if response_format is json_object
            if response_format and response_format.get("type") == "json_object":
                import json

                return json.loads(content)
            else:
                return {"content": content}

        except Exception as e:
            error_msg = f"Moonshot API error: {e}"
            logger.error(error_msg)
            raise LLMError(error_msg)

    def test_connection(self) -> bool:
        """Test Moonshot API connection"""
        try:
            messages = [
                {"role": "system", "content": "You are a test assistant. Respond with valid JSON."},
                {
                    "role": "user",
                    "content": 'Respond with JSON: {"status": "ok", "message": "test successful"}',
                },
            ]
            result = self.chat_completion(messages, response_format={"type": "json_object"})
            return result.get("status") == "ok"
        except Exception as e:
            logger.error(f"Moonshot connection test failed: {e}")
            return False

    def get_fallback_content(self, content_type: str = "historical") -> Dict:
        """Get fallback content for Moonshot"""
        if content_type == "historical":
            from utils.llm_service import format_date_standard

            today = format_date_standard(datetime.now())
            return {
                "date": today,
                "year": 1953,
                "title": "First Ascent of Mount Everest",
                "description": "On May 29, 1953, Edmund Hillary and Tenzing Norgay became the first confirmed climbers to reach the summit of Mount Everest. This achievement marked a pivotal moment in mountaineering history, proving that the world's highest peak could be conquered. Their success opened a new era of high-altitude climbing and inspired generations of mountaineers worldwide.",
                "location": "Mount Everest, Nepal-Tibet border",
                "people": ["Edmund Hillary", "Tenzing Norgay"],
                "url": None,
                "category": "first_ascent",
            }
        else:
            return {
                "title": "Mountaineering News Unavailable",
                "summary": "Current mountaineering news is temporarily unavailable. Please check back later.",
                "category": "events",
                "url": None,
                "relevance_score": 0.5,
                "source_name": "System",
            }

    def get_cost_per_token(self) -> float:
        """Estimated cost per token for Moonshot"""
        # Moonshot pricing (estimated)
        return 0.00001  # $0.01 per 1K tokens


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek provider using requests (for future news implementation)"""

    def __init__(self):
        super().__init__()
        self.api_key = current_app.config.get("DEEPSEEK_API_KEY")
        self.api_url = current_app.config.get(
            "DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"
        )
        self.model = "deepseek-chat"

        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not configured")

    @property
    def provider_name(self) -> str:
        return "DeepSeek"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_url)

    def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """Create chat completion using DeepSeek API"""
        if not self.is_configured:
            raise LLMError("DeepSeek provider not configured")

        try:
            import requests
            import json

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.5),
                "max_tokens": kwargs.get("max_tokens", 2000),
            }

            # Add response format if specified
            response_format = kwargs.get("response_format")
            if response_format:
                payload["response_format"] = response_format

            logger.info(f"Making DeepSeek API request with model {self.model}")
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                logger.info("DeepSeek API request successful")

                # Parse JSON if response_format is json_object
                if response_format and response_format.get("type") == "json_object":
                    return json.loads(content)
                else:
                    return {"content": content}
            else:
                error_msg = f"DeepSeek API returned status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise LLMError(error_msg)

        except Exception as e:
            error_msg = f"DeepSeek API error: {e}"
            logger.error(error_msg)
            raise LLMError(error_msg)

    def test_connection(self) -> bool:
        """Test DeepSeek API connection"""
        try:
            messages = [
                {"role": "system", "content": "You are a test assistant. Respond with valid JSON."},
                {
                    "role": "user",
                    "content": 'Respond with JSON: {"status": "ok", "message": "test successful"}',
                },
            ]
            result = self.chat_completion(messages, response_format={"type": "json_object"})
            return result.get("status") == "ok"
        except Exception as e:
            logger.error(f"DeepSeek connection test failed: {e}")
            return False

    def get_fallback_content(self, content_type: str = "historical") -> Dict:
        """Get fallback content for DeepSeek"""
        return {
            "title": "News Analysis Unavailable",
            "summary": "News analysis is temporarily unavailable. Please check back later.",
            "category": "events",
            "url": None,
            "relevance_score": 0.5,
            "source_name": "System",
        }

    def get_cost_per_token(self) -> float:
        """Estimated cost per token for DeepSeek"""
        # DeepSeek pricing (estimated)
        return 0.000001  # Very low cost


class ProviderManager:
    """Manages multiple LLM providers with fallback logic"""

    def __init__(self):
        self.providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all available providers"""
        try:
            moonshot = MoonshotProvider()
            if moonshot.is_configured:
                self.providers["moonshot"] = moonshot
                logger.info("Moonshot provider initialized")
            else:
                logger.warning("Moonshot provider not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Moonshot provider: {e}")

        try:
            deepseek = DeepSeekProvider()
            if deepseek.is_configured:
                self.providers["deepseek"] = deepseek
                logger.info("DeepSeek provider initialized")
            else:
                logger.warning("DeepSeek provider not configured")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek provider: {e}")

    def get_provider(self, provider_name: str) -> Optional[BaseLLMProvider]:
        """Get specific provider by name"""
        return self.providers.get(provider_name)

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return list(self.providers.keys())

    def chat_completion_with_fallback(
        self, messages: List[Dict], use_case: str = "historical", **kwargs
    ) -> Dict:
        """
        Try chat completion with fallback logic

        Args:
            messages: Chat messages
            use_case: 'historical' or 'news'
            **kwargs: Additional parameters

        Returns:
            Dict with response or fallback content
        """
        # Define provider priority by use case
        if use_case == "historical":
            provider_order = ["moonshot", "deepseek"]
        elif use_case == "news":
            provider_order = ["deepseek", "moonshot"]
        else:
            provider_order = ["moonshot", "deepseek"]

        last_error = None

        # Try providers in order
        for provider_name in provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            try:
                logger.info(f"Trying provider: {provider.provider_name}")
                result = provider.chat_completion(messages, **kwargs)
                logger.info(f"Success with provider: {provider.provider_name}")
                return result

            except LLMError as e:
                logger.warning(f"Provider {provider.provider_name} failed: {e}")
                last_error = e
                continue

        # All providers failed, use fallback
        logger.error(f"All providers failed, using fallback content. Last error: {last_error}")

        # Get fallback from first available provider
        for provider_name in provider_order:
            provider = self.providers.get(provider_name)
            if provider:
                return provider.get_fallback_content(use_case)

        # Absolute fallback if no providers available
        return {"error": "No LLM providers available", "fallback": True}

    def test_all_providers(self) -> Dict[str, bool]:
        """Test all configured providers"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = provider.test_connection()
                logger.info(f"Provider {name}: {'✅ OK' if results[name] else '❌ Failed'}")
            except Exception as e:
                results[name] = False
                logger.error(f"Provider {name}: ❌ Error - {e}")
        return results
